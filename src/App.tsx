import React, { useState, useEffect, useRef } from 'react';
import { MinimalNav, DestinationTab } from './components/MinimalNav';
import { CleanHomeScreen } from './components/CleanHomeScreen';
import { CleanTutorWorkspace } from './components/CleanTutorWorkspace';
import { CleanProgressView } from './components/CleanProgressView';
import { IntelligenceState } from './components/JarvisNeuralCore';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState<DestinationTab>('home');
  const [activeLearnerId] = useState<string>('learner_gate_01');
  const [hudStatus, setHudStatus] = useState<IntelligenceState>('IDLE');

  // Input states
  const [homeQuery, setHomeQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Data states from MongoDB
  const [concepts, setConcepts] = useState<Array<{ id: string; name: string; prerequisites: string[]; default_p_init: number }>>([]);
  const [selectedConceptId, setSelectedConceptId] = useState<string>('');
  const [masteries, setMasteries] = useState<any[]>([]);

  // Adaptive Session & Practice State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [isSubmittingPractice, setIsSubmittingPractice] = useState<boolean>(false);
  const [latestDiagnosis, setLatestDiagnosis] = useState<any>(null);

  // Progressive Streaming Tutor Dialogue Conversation
  const [conversationHistory, setConversationHistory] = useState<Array<{ role: 'user' | 'assistant'; text: string; provider?: string }>>([]);

  // 1. Initial Load: Synchronize with MongoDB
  useEffect(() => {
    async function initData() {
      try {
        const [conceptsData, masteriesData] = await Promise.all([
          api.getConcepts(),
          api.getLearnerMastery(activeLearnerId),
        ]);

        setConcepts(conceptsData);
        if (conceptsData.length > 0) {
          setSelectedConceptId(conceptsData[0].id);
        }
        setMasteries(masteriesData);

        // Resume or start session
        const sess = await api.startSession(activeLearnerId);
        setSessionId(sess.session_id);
        if (sess.current_question) {
          setCurrentQuestion(sess.current_question);
        }
      } catch (err) {
        console.warn('Initial load fallback/warning:', err);
      }
    }
    initData();
  }, [activeLearnerId]);

  const activeConcept = concepts.find((c) => c.id === selectedConceptId);

  // Progressive Streaming Tutor Inquire handler
  const handleTutorInquire = (messageText: string, targetMode: 'learn' | 'ask' | 'practice') => {
    if (!messageText.trim()) return;

    // Switch to workspace view immediately
    setActiveTab(targetMode);

    // 1. Append user message & initialize assistant placeholder
    setConversationHistory((prev) => [
      ...prev,
      { role: 'user', text: messageText },
      { role: 'assistant', text: '' },
    ]);

    setIsLoading(true);
    setHudStatus('THINKING');

    const abortCtrl = new AbortController();
    abortControllerRef.current = abortCtrl;

    const modeKey = targetMode === 'learn' ? 'TEACH' : 'DOUBT';

    api.streamTutor(
      {
        learner_id: activeLearnerId,
        message: messageText,
        mode: modeKey,
        concept_id: selectedConceptId,
      },
      {
        onStart: (data) => {
          setHudStatus('THINKING');
        },
        onChunk: (chunk) => {
          setHudStatus('RESPONDING');
          setConversationHistory((prev) => {
            if (prev.length === 0) return prev;
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            const currentItem = updated[lastIdx];
            if (currentItem && currentItem.role === 'assistant') {
              updated[lastIdx] = {
                ...currentItem,
                text: (currentItem.text || '') + chunk,
              };
            }
            return updated;
          });
        },
        onComplete: (data) => {
          setIsLoading(false);
          setHudStatus('IDLE');
          setConversationHistory((prev) => {
            if (prev.length === 0) return prev;
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            const currentItem = updated[lastIdx];
            if (currentItem && currentItem.role === 'assistant') {
              updated[lastIdx] = {
                ...currentItem,
                provider: data.provider,
              };
            }
            return updated;
          });
        },
        onError: (err) => {
          setIsLoading(false);
          setHudStatus('ERROR');
          setConversationHistory((prev) => {
            const copy = [...prev];
            const last = copy[copy.length - 1];
            if (last && last.role === 'assistant') {
              if (!last.text) {
                last.text = `Tutor connection notice: ${err.message}. Retrying or operating in fallback mode.`;
              }
            }
            return copy;
          });
          setTimeout(() => setHudStatus('IDLE'), 4000);
        },
      },
      abortCtrl.signal
    );
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      setHudStatus('IDLE');
    }
  };

  // Practice Submission handler
  const handlePracticeSubmit = async (answer: string, reasoning: string) => {
    if (!sessionId || !currentQuestion) return;
    setIsSubmittingPractice(true);
    setHudStatus('THINKING');

    try {
      const res = await api.submitAttempt({
        learner_id: activeLearnerId,
        session_id: sessionId,
        question_id: currentQuestion.question_id,
        student_answer: answer,
        reasoning_transcript: reasoning,
      });

      setLatestDiagnosis(res.diagnosis);
      setHudStatus('RESPONDING');

      const updatedMasteries = await api.getLearnerMastery(activeLearnerId);
      setMasteries(updatedMasteries);

      if (res.next_question) {
        setCurrentQuestion(res.next_question);
      } else {
        setCurrentQuestion(null);
      }
    } catch (err: any) {
      console.error('Practice submission error:', err);
      setHudStatus('ERROR');
    } finally {
      setIsSubmittingPractice(false);
      setTimeout(() => setHudStatus('IDLE'), 3500);
    }
  };

  const recentModules = concepts.map((c) => {
    const m = masteries.find((rec) => rec.concept_id === c.id);
    return {
      id: c.id,
      title: c.name,
      mastery: m ? Math.round(m.p_mastery * 100) : Math.round(c.default_p_init * 100),
    };
  });

  return (
    <div className="min-h-screen bg-[#06080A] text-[#CBE7F5] selection:bg-[#00D9FF]/20 selection:text-[#00D9FF] flex flex-col font-sans">
      {/* 1. Minimal Top Navigation */}
      <MinimalNav
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        learnerName="Arjun Sharma"
      />

      {/* 2. Main Viewport */}
      <div className="flex-1 flex flex-col">
        {activeTab === 'home' && (
          <CleanHomeScreen
            status={hudStatus === 'ERROR' ? 'IDLE' : hudStatus}
            query={homeQuery}
            onQueryChange={setHomeQuery}
            onSubmit={(e) => {
              e?.preventDefault();
              handleTutorInquire(homeQuery, 'ask');
              setHomeQuery('');
            }}
            isLoading={isLoading}
            onSelectAction={(mode) => setActiveTab(mode)}
            activeConceptName={activeConcept?.name}
            recentModules={recentModules}
            onContinueConcept={(cid) => {
              setSelectedConceptId(cid);
              setActiveTab('learn');
            }}
          />
        )}

        {(activeTab === 'learn' || activeTab === 'ask' || activeTab === 'practice') && (
          <CleanTutorWorkspace
            intelligenceState={hudStatus}
            mode={activeTab}
            activeConceptName={activeConcept?.name}
            conceptsList={concepts}
            selectedConceptId={selectedConceptId}
            onSelectConcept={setSelectedConceptId}
            currentQuestion={currentQuestion}
            onPracticeSubmit={handlePracticeSubmit}
            isSubmittingPractice={isSubmittingPractice}
            latestDiagnosis={latestDiagnosis}
            conversationHistory={conversationHistory}
            onSendMessage={(msg) => handleTutorInquire(msg, activeTab)}
            isLoading={isLoading}
            onStopGeneration={handleStopGeneration}
          />
        )}

        {activeTab === 'progress' && (
          <CleanProgressView masteries={masteries} />
        )}
      </div>
    </div>
  );
}
