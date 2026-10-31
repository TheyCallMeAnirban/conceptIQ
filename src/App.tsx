import React, { useState, useEffect } from 'react';
import { MinimalNav, DestinationTab } from './components/MinimalNav';
import { CleanHomeScreen } from './components/CleanHomeScreen';
import { CleanTutorWorkspace } from './components/CleanTutorWorkspace';
import { CleanProgressView } from './components/CleanProgressView';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState<DestinationTab>('home');
  const [activeLearnerId] = useState<string>('learner_gate_01');
  const [hudStatus, setHudStatus] = useState<'IDLE' | 'LISTENING' | 'THINKING' | 'RESPONDING' | 'ASSESSING'>('IDLE');

  // Input states
  const [homeQuery, setHomeQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Data states from MongoDB
  const [concepts, setConcepts] = useState<Array<{ id: string; name: string; prerequisites: string[]; default_p_init: number }>>([]);
  const [selectedConceptId, setSelectedConceptId] = useState<string>('');
  const [masteries, setMasteries] = useState<any[]>([]);

  // Adaptive Session & Practice State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [isSubmittingPractice, setIsSubmittingPractice] = useState<boolean>(false);
  const [latestDiagnosis, setLatestDiagnosis] = useState<any>(null);

  // Tutor Dialogue Conversation
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

  // Tutor Inquire handler (Universal AI Tutor)
  const handleTutorInquire = async (messageText: string, targetMode: 'learn' | 'ask' | 'practice') => {
    if (!messageText.trim()) return;

    // Switch to workspace view
    setActiveTab(targetMode);
    setConversationHistory((prev) => [...prev, { role: 'user', text: messageText }]);
    setIsLoading(true);
    setHudStatus('THINKING');

    try {
      const modeKey = targetMode === 'learn' ? 'TEACH' : 'DOUBT';
      const res = await api.queryTutor({
        learner_id: activeLearnerId,
        message: messageText,
        mode: modeKey,
        concept_id: selectedConceptId,
      });

      setConversationHistory((prev) => [
        ...prev,
        { role: 'assistant', text: res.reply, provider: res.provider },
      ]);
      setHudStatus('RESPONDING');
    } catch (err: any) {
      setConversationHistory((prev) => [
        ...prev,
        { role: 'assistant', text: `Tutor communication error: ${err.message}` },
      ]);
    } finally {
      setIsLoading(false);
      setTimeout(() => setHudStatus('IDLE'), 3500);
    }
  };

  // Practice Submission handler
  const handlePracticeSubmit = async (answer: string, reasoning: string) => {
    if (!sessionId || !currentQuestion) return;
    setIsSubmittingPractice(true);
    setHudStatus('ASSESSING');

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

      // Refresh masteries
      const updatedMasteries = await api.getLearnerMastery(activeLearnerId);
      setMasteries(updatedMasteries);

      if (res.next_question) {
        setCurrentQuestion(res.next_question);
      } else {
        setCurrentQuestion(null);
      }
    } catch (err: any) {
      console.error('Practice submission error:', err);
    } finally {
      setIsSubmittingPractice(false);
      setTimeout(() => setHudStatus('IDLE'), 3500);
    }
  };

  // Build compact modules for Continue Learning list
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
            status={hudStatus}
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
            hudStatus={hudStatus}
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
          />
        )}

        {activeTab === 'progress' && (
          <CleanProgressView masteries={masteries} />
        )}
      </div>
    </div>
  );
}
