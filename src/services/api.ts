/**
 * Centralized API Client for ConceptIQ.
 * Connects the React/Vite frontend to the FastAPI/MongoDB backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20000);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        errorDetail = errorJson.detail || errorDetail;
      } catch {
        // Fallback to text status
      }
      throw new Error(errorDetail);
    }

    return await res.json();
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. Please check if the backend server is reachable.');
    }
    throw err;
  }
}

export const api = {
  // --- Concepts & Syllabus ---
  getConcepts: () => request<Array<{
    id: string;
    name: string;
    description: string;
    prerequisites: string[];
    default_p_init: number;
  }>>('/concepts'),

  // --- Learner Profile & Mastery ---
  getLearners: () => request<Array<{
    id: string;
    name: string;
    created_at?: string;
  }>>('/learners'),

  getLearnerMastery: (learnerId: string, subjectId?: string) => {
    const query = subjectId ? `?subject_id=${encodeURIComponent(subjectId)}` : '';
    return request<Array<{
      concept_id: string;
      concept_name: string;
      topic_id?: string;
      subject_id?: string;
      p_mastery: number;
      leitner_box: number;
      consecutive_correct: number;
      last_reviewed_at: string | null;
      next_review_due: string | null;
      is_due_for_review: boolean;
      urgency_hours: number;
      assessment_state: 'UNASSESSED' | 'IN_PROGRESS' | 'ASSESSED';
      formal_attempt_count: number;
      last_assessed_at: string | null;
    }>>(`/learners/${learnerId}/mastery${query}`);
  },

  // --- Adaptive Sessions & Practice ---
  startSession: (learnerId: string, forceNew: boolean = false) =>
    request<{
      session_id: string;
      learner_id: string;
      status: string;
      current_question?: {
        question_id: string;
        title: string;
        problem_text: string;
        code_snippet?: string;
        question_type: string;
        options?: Array<{ id: string; text: string }>;
        difficulty: number;
        target_concept_id: string;
        target_concept_name: string;
        rationale: {
          selection_reason: string;
          recommended_difficulty: number;
          rationale_details: string;
          prerequisite_status: string;
        };
      };
    }>('/sessions/start', {
      method: 'POST',
      body: JSON.stringify({ learner_id: learnerId, force_new: forceNew }),
    }),

  submitAttempt: (payload: {
    learner_id: string;
    session_id: string;
    question_id: string;
    student_answer: string;
    reasoning_transcript: string;
  }) =>
    request<{
      session_id: string;
      attempt_id: string;
      sequence_number: number;
      is_correct: boolean;
      diagnosis: {
        is_correct: boolean;
        reasoning_quality: string;
        detected_misconceptions: string[];
        affected_concepts: string[];
        reasoning_evidence: string;
        explanation: string;
        recommended_intervention: string;
        suggested_difficulty: number;
        diagnosis_provider: string;
      };
      bkt_update: {
        prior: number;
        posterior: number;
        delta: number;
        p_transit: number;
        p_guess: number;
        p_slip: number;
      };
      leitner_update: {
        previous_box: number;
        new_box: number;
        consecutive_correct: number;
        next_review_due: string;
      };
      next_question?: any;
      session_status: string;
    }>('/sessions/submit', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // --- Progressive Streaming Tutor Chat via SSE ---
  streamTutor: (
    payload: {
      learner_id: string;
      message: string;
      mode?: 'DOUBT' | 'EXPLAIN' | 'TEACH' | 'ANALYZE';
      subject_id?: string;
      concept_id?: string;
    },
    callbacks: {
      onStart?: (data: { request_id: string; mode: string }) => void;
      onChunk: (chunk: string) => void;
      onComplete?: (data: { provider: string }) => void;
      onError?: (err: any) => void;
    },
    signal?: AbortSignal
  ) => {
    const url = `${API_BASE_URL}/tutor/stream`;

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Streaming failed: HTTP ${response.status}`);
        }
        if (!response.body) {
          throw new Error('ReadableStream not supported by browser/environment');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('data:')) {
              const jsonStr = trimmed.slice(5).trim();
              try {
                const event = JSON.parse(jsonStr);
                if (event.type === 'start' && callbacks.onStart) {
                  callbacks.onStart(event);
                } else if (event.type === 'content' && event.chunk) {
                  callbacks.onChunk(event.chunk);
                } else if (event.type === 'complete' && callbacks.onComplete) {
                  callbacks.onComplete(event);
                }
              } catch (e) {
                // Incomplete JSON line in chunk
              }
            }
          }
        }
      })
      .catch((err) => {
        if (signal?.aborted) return;
        if (callbacks.onError) callbacks.onError(err);
      });
  },

  // --- Universal Tutor Chat / Doubts (Non-streaming fallback) ---
  queryTutor: (payload: {
    learner_id: string;
    message: string;
    mode?: 'DOUBT' | 'EXPLAIN' | 'TEACH' | 'ANALYZE';
    subject_id?: string;
    concept_id?: string;
  }) =>
    request<{
      mode: string;
      reply: string;
      concept_id?: string;
      pedagogical_breakdown?: Record<string, string>;
      provider: string;
    }>('/tutor/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  // --- Analytics ---
  getMisconceptionsAnalytics: () =>
    request<Array<{
      misconception_id: string;
      misconception_name: string;
      concept_id: string;
      concept_name: string;
      occurrence_count: number;
      remediation_hint: string;
    }>>('/analytics/misconceptions'),
};

