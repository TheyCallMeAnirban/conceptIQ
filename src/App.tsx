import React, { useState, useEffect } from 'react';
import { TopNav } from './components/TopNav';
import { OrbitalFocalHub } from './components/OrbitalFocalHub';
import { CognitiveRadar } from './components/CognitiveRadar';
import { SystemStreamWing } from './components/SystemStreamWing';
import { SocraticDialogueWing } from './components/SocraticDialogueWing';
import { SimulationLab } from './components/SimulationLab';
import { KnowledgeTopologyView } from './components/KnowledgeTopologyView';
import { TerminalBar } from './components/TerminalBar';
import { CalibrationModal } from './components/CalibrationModal';
import { ModuleTrack, CognitiveVector, SessionMetrics, TelemetryLog } from './types/hud';
import { parseTerminalCommand } from './lib/tutor-engine';
import { api } from './services/api';
import { INITIAL_COGNITIVE_VECTORS, INITIAL_LOGS } from './data/mock-curriculum';
import { Brain, Sparkles, Loader2, Send } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'telemetry' | 'simulation' | 'topology' | 'socratic'>('telemetry');
  const [activeLearnerId] = useState<string>('learner_gate_01');
  const [modules, setModules] = useState<ModuleTrack[]>([]);
  const [activeModuleId, setActiveModuleId] = useState<string>('');
  const [vectors, setVectors] = useState<CognitiveVector[]>(INITIAL_COGNITIVE_VECTORS);
  const [logs, setLogs] = useState<TelemetryLog[]>(INITIAL_LOGS);
  const [isCalibrationOpen, setIsCalibrationOpen] = useState<boolean>(false);
  const [terminalFeedback, setTerminalFeedback] = useState<string>('System initialized. Connected to MongoDB backend.');
  const [hudState, setHudState] = useState<'IDLE' | 'THINKING' | 'RESPONDING' | 'ASSESSING'>('IDLE');
  
  // Adaptive Session State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [isAttempting, setIsAttempting] = useState<boolean>(false);
  const [latestDiagnosis, setLatestDiagnosis] = useState<any>(null);

  // Tutor Dialogue
  const [tutorQuery, setTutorQuery] = useState<string>('');
  const [tutorResponse, setTutorResponse] = useState<string>('');
  const [isTutorLoading, setIsTutorLoading] = useState<boolean>(false);

  // Session clock state
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(120);
  const [metrics, setMetrics] = useState<SessionMetrics>({
    masteryVelocity: 2.18,
    comprehensionBandwidth: 78.5,
    retentionCurve: 89.2,
    neuralFocusDrift: 0.02,
    totalCycles: 1,
    elapsedSeconds: 120,
  });

  // 1. Initial Load: Fetch live concepts & mastery from MongoDB
  useEffect(() => {
    async function loadBackendData() {
      try {
        setLogs((prev) => [
          {
            id: `log_${Date.now()}`,
            timestamp: new Date().toLocaleTimeString(),
            line: prev.length + 1,
            channel: 'SYS.INIT',
            type: 'nominal',
            message: 'Synchronizing with MongoDB syllabus & learner graph...',
          },
          ...prev,
        ]);

        const [conceptsData, masteries] = await Promise.all([
          api.getConcepts(),
          api.getLearnerMastery(activeLearnerId),
        ]);

        // Map concepts and masteries into HUD ModuleTracks
        const masteryMap = new Map(masteries.map((m) => [m.concept_id, m]));
        const mappedModules: ModuleTrack[] = conceptsData.map((c, i) => {
          const m = masteryMap.get(c.id);
          const pMastery = m ? Math.round(m.p_mastery * 100) : Math.round(c.default_p_init * 100);
          return {
            id: c.id,
            code: `CON: ${c.id.slice(0, 14)}`,
            title: c.name,
            domain: c.description.slice(0, 32),
            status: m?.is_due_for_review ? 'review_required' : 'nominal',
            mastery: pMastery,
            retention: Math.min(100, Math.round(pMastery * 1.05)),
            activeConcept: c.name,
            problemPrompt: {
              title: c.name,
              description: c.description,
              systemEquation: 'P(L_t) = P(L_{t-1}) + (1 - P(L_{t-1})) · P(T)',
              parameterName: 'Mastery Probability (BKT)',
              parameterUnit: '%',
              currentValue: pMastery,
              targetMin: 0,
              targetMax: 100,
              nominalTarget: 85,
              tolerance: 10,
              contextExplanation: `Syllabus concept registered in MongoDB. Prerequisites: ${c.prerequisites.join(', ') || 'None'}.`,
              socraticHints: [
                'Observe the prerequisite relationships in the topological graph.',
                'Submitting active recall attempts updates your BKT mastery and Leitner schedule.',
              ],
            },
          };
        });

        if (mappedModules.length > 0) {
          setModules(mappedModules);
          setActiveModuleId(mappedModules[0].id);
        }

        // Update Cognitive Vectors based on active subjects
        if (masteries.length > 0) {
          const csMastery = masteries.filter((m) => m.subject_id === 'CS');
          const avgCs = csMastery.length ? Math.round(csMastery.reduce((acc, curr) => acc + curr.p_mastery, 0) / csMastery.length * 100) : 60;
          setVectors((prev) =>
            prev.map((v) => (v.id === 'vec_cyber' ? { ...v, value: avgCs } : v))
          );
        }

        // Auto-start or resume adaptive session
        const sessionRes = await api.startSession(activeLearnerId);
        setSessionId(sessionRes.session_id);
        if (sessionRes.current_question) {
          setCurrentQuestion(sessionRes.current_question);
        }

        setTerminalFeedback('Backend synchronized: MongoDB collections active. AI Tutor online.');
      } catch (err: any) {
        setTerminalFeedback(`Connection Warning: ${err.message}. Retrying or operating in fallback mode.`);
      }
    }
    loadBackendData();
  }, [activeLearnerId]);

  // Tick clock
  useEffect(() => {
    const timer = setInterval(() => setElapsedSeconds((prev) => prev + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatSessionTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `T+${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  const currentModule = modules.find((m) => m.id === activeModuleId) || modules[0];

  // Socratic / Practice Answer Submission
  const handlePracticeSubmit = async (answer: string, reasoning: string) => {
    if (!sessionId || !currentQuestion) return;
    setIsAttempting(true);
    setHudState('ASSESSING');

    try {
      const result = await api.submitAttempt({
        learner_id: activeLearnerId,
        session_id: sessionId,
        question_id: currentQuestion.question_id,
        student_answer: answer,
        reasoning_transcript: reasoning,
      });

      setLatestDiagnosis(result.diagnosis);
      setHudState('RESPONDING');

      // Add audit log
      setLogs((prev) => [
        {
          id: `log_${Date.now()}`,
          timestamp: new Date().toLocaleTimeString(),
          line: prev.length + 1,
          channel: 'BKT.DIAG',
          type: result.is_correct ? 'nominal' : 'warning',
          message: `Attempt on ${currentQuestion.question_id}: ${result.is_correct ? 'CORRECT' : 'INCORRECT'}. BKT posterior: ${(result.bkt_update.posterior * 100).toFixed(1)}% (Δ ${(result.bkt_update.delta * 100).toFixed(1)}%)`,
        },
        ...prev,
      ]);

      // Refresh mastery state
      const masteries = await api.getLearnerMastery(activeLearnerId);
      const updatedMastery = masteries.find((m) => m.concept_id === currentQuestion.target_concept_id);
      if (updatedMastery) {
        setModules((prev) =>
          prev.map((mod) =>
            mod.id === updatedMastery.concept_id
              ? { ...mod, mastery: Math.round(updatedMastery.p_mastery * 100) }
              : mod
          )
        );
      }

      if (result.next_question) {
        setCurrentQuestion(result.next_question);
      } else {
        setCurrentQuestion(null);
        setTerminalFeedback('Session completed. All curriculum objectives evaluated.');
      }
    } catch (err: any) {
      setTerminalFeedback(`Submission failed: ${err.message}`);
    } finally {
      setIsAttempting(false);
      setTimeout(() => setHudState('IDLE'), 3000);
    }
  };

  // Universal Tutor Chat / Ask Doubt
  const handleAskTutor = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!tutorQuery.trim()) return;

    setIsTutorLoading(true);
    setHudState('THINKING');
    try {
      const res = await api.queryTutor({
        learner_id: activeLearnerId,
        message: tutorQuery,
        mode: 'DOUBT',
        concept_id: currentModule?.id,
      });
      setTutorResponse(res.reply);
      setHudState('RESPONDING');
      setTerminalFeedback(`Tutor evaluated via ${res.provider}.`);
    } catch (err: any) {
      setTutorResponse(`Tutor communication error: ${err.message}`);
    } finally {
      setIsTutorLoading(false);
      setTimeout(() => setHudState('IDLE'), 4000);
    }
  };

  return (
    <div className="min-h-screen bg-[#06080A] text-[#CBE7F5] selection:bg-[#00D9FF]/20 selection:text-[#00D9FF] flex flex-col font-sans">
      {/* Top Navigation */}
      <TopNav
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        onOpenCalibration={() => setIsCalibrationOpen(true)}
        sessionTime={formatSessionTime(elapsedSeconds)}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-[1720px] w-full mx-auto p-3 sm:p-5 flex flex-col gap-4">
        {activeTab === 'telemetry' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left Wing: Real MongoDB Syllabus & Telemetry */}
            <div className="lg:col-span-3 flex flex-col gap-4">
              <SystemStreamWing
                modules={modules}
                activeModuleId={activeModuleId}
                onSelectModule={(id) => setActiveModuleId(id)}
                logs={logs}
              />
            </div>

            {/* Center Wing: Radial HUD & Universal AI Tutor Workspace */}
            <div className="lg:col-span-6 flex flex-col gap-4">
              <OrbitalFocalHub
                metrics={metrics}
                activeVectorLabel={currentModule?.activeConcept || 'ADAPTIVE NEURAL COGNITION'}
                onCalibrateDial={() => setIsCalibrationOpen(true)}
              />

              {/* Universal AI Tutor Intelligence Workspace */}
              <div className="w-full bg-[#111519]/90 border border-[#1E2830] backdrop-blur-md p-4 reticle-box chamfer-card font-mono">
                <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#1E2830] text-xs">
                  <div className="flex items-center gap-2 text-[#00D9FF]">
                    <Brain className="w-4 h-4 animate-pulse" />
                    <span className="font-semibold uppercase tracking-wider">
                      UNIVERSAL AI TUTOR WORKSPACE
                    </span>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 border border-[#1E2830] text-[#00D9FF]">
                    HUD STATE: {hudState}
                  </span>
                </div>

                {/* Question / Practice Display */}
                {currentQuestion ? (
                  <div className="p-3 bg-[#0A0D10] border border-[#263844] mb-3 space-y-2 text-xs">
                    <div className="flex items-center justify-between text-[#8EA7B5]">
                      <span className="text-[#00D9FF] font-bold">[{currentQuestion.question_id}] {currentQuestion.title}</span>
                      <span>Difficulty: {currentQuestion.difficulty}</span>
                    </div>
                    <p className="text-[#E6F7FF] whitespace-pre-wrap">{currentQuestion.problem_text}</p>
                    {currentQuestion.code_snippet && (
                      <pre className="p-2 bg-[#050709] border border-[#1E2830] text-[#00D9FF] text-[11px] overflow-x-auto">
                        {currentQuestion.code_snippet}
                      </pre>
                    )}
                    {currentQuestion.options && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                        {currentQuestion.options.map((opt: any) => (
                          <button
                            key={opt.id}
                            disabled={isAttempting}
                            onClick={() => handlePracticeSubmit(opt.id, `Selected option ${opt.id} based on memory and pointer layout.`)}
                            className="text-left px-2.5 py-1.5 bg-[#111519] border border-[#1E2830] hover:border-[#00D9FF] hover:text-[#00D9FF] text-[11px] transition-colors"
                          >
                            <span className="text-[#00D9FF] font-bold mr-1.5">{opt.id}:</span>
                            {opt.text}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="p-3 bg-[#0A0D10] border border-[#263844] mb-3 text-xs text-[#8EA7B5]">
                    No active question queued. Use the doubt input below to inquire about any concept.
                  </div>
                )}

                {/* AI Tutor Chat / Doubt Input */}
                <form onSubmit={handleAskTutor} className="flex gap-2">
                  <input
                    type="text"
                    value={tutorQuery}
                    onChange={(e) => setTutorQuery(e.target.value)}
                    placeholder="Ask any doubt (e.g. 'Explain pointers', 'Why integration by parts?')..."
                    className="flex-1 bg-[#090B0D] border border-[#1E2830] px-3 py-1.5 text-xs text-[#E6F7FF] placeholder-[#4D6270] focus:border-[#00D9FF] focus:outline-none"
                  />
                  <button
                    type="submit"
                    disabled={isTutorLoading}
                    className="px-3 py-1.5 bg-[#00D9FF]/20 border border-[#00D9FF] text-[#00D9FF] hover:bg-[#00D9FF]/30 text-xs font-semibold uppercase flex items-center gap-1.5 transition-colors"
                  >
                    {isTutorLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    <span>Inquire</span>
                  </button>
                </form>

                {/* Tutor Response Output */}
                {tutorResponse && (
                  <div className="mt-3 p-3 bg-[#090B0D] border border-[#1E2830] text-xs text-[#CBE7F5] max-h-60 overflow-y-auto space-y-2">
                    <div className="text-[10px] text-[#00D9FF] flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> TUTOR PEDAGOGICAL BREAKDOWN
                    </div>
                    <div className="whitespace-pre-wrap leading-relaxed">{tutorResponse}</div>
                  </div>
                )}

                {/* Latest Practice Diagnosis */}
                {latestDiagnosis && (
                  <div className="mt-2 p-2 bg-[#090B0D] border border-[#263844] text-[11px] text-[#8EA7B5]">
                    <span className="text-[#00D9FF] font-semibold">Latest Diagnosis: </span>
                    {latestDiagnosis.explanation} ({latestDiagnosis.recommended_intervention})
                  </div>
                )}
              </div>
            </div>

            {/* Right Wing: Cognitive Radar & Socratic Practice */}
            <div className="lg:col-span-3 flex flex-col gap-4">
              <CognitiveRadar
                vectors={vectors}
                selectedVectorId={vectors[0]?.id}
                onSelectVector={(id) => {}}
              />
              {currentModule && (
                <SocraticDialogueWing
                  module={currentModule}
                  onUpdateScore={(delta, isNominal, msg) => {
                    setLogs((prev) => [
                      {
                        id: `log_${Date.now()}`,
                        timestamp: new Date().toLocaleTimeString(),
                        line: prev.length + 1,
                        channel: 'SOCRATIC',
                        type: isNominal ? 'nominal' : 'warning',
                        message: msg,
                      },
                      ...prev,
                    ]);
                  }}
                />
              )}
            </div>
          </div>
        )}

        {activeTab === 'simulation' && (
          <SimulationLab
            onLogTelemetry={(msg) => {
              setLogs((prev) => [
                {
                  id: `log_${Date.now()}`,
                  timestamp: new Date().toLocaleTimeString(),
                  line: prev.length + 1,
                  channel: 'SIM.LAB',
                  type: 'info',
                  message: msg,
                },
                ...prev,
              ]);
            }}
          />
        )}

        {activeTab === 'topology' && (
          <KnowledgeTopologyView
            vectors={vectors}
            modules={modules}
            onSelectModule={(id) => setActiveModuleId(id)}
          />
        )}

        {activeTab === 'socratic' && currentModule && (
          <div className="max-w-3xl mx-auto w-full">
            <SocraticDialogueWing
              module={currentModule}
              onUpdateScore={(delta, isNominal, msg) => {
                setLogs((prev) => [
                  {
                    id: `log_${Date.now()}`,
                    timestamp: new Date().toLocaleTimeString(),
                    line: prev.length + 1,
                    channel: 'SOCRATIC',
                    type: isNominal ? 'nominal' : 'warning',
                    message: msg,
                  },
                  ...prev,
                ]);
              }}
            />
          </div>
        )}
      </main>

      {/* Terminal Bar Console */}
      <footer className="w-full mt-auto">
        <TerminalBar
          onExecuteCommand={(cmd, res) => {
            setTerminalFeedback(res.outputMessage);
            if (res.action === 'calibrate') setIsCalibrationOpen(true);
          }}
          recentOutput={terminalFeedback}
        />
      </footer>

      {/* 360° Sweep Calibration Modal */}
      <CalibrationModal
        isOpen={isCalibrationOpen}
        onClose={() => setIsCalibrationOpen(false)}
        onCalibrationComplete={() => {
          setTerminalFeedback('Orbital concentric reticles normalized to 360° nominal state.');
        }}
      />
    </div>
  );
}
