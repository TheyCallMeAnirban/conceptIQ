import React, { useState } from 'react';
import { JarvisRadialHud } from './JarvisRadialHud';
import { Send, Sparkles, BookOpen, Layers, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

interface CleanTutorWorkspaceProps {
  hudStatus: 'IDLE' | 'THINKING' | 'RESPONDING' | 'ASSESSING';
  mode: 'learn' | 'ask' | 'practice';
  activeConceptName?: string;
  conceptsList: Array<{ id: string; name: string; prerequisites: string[] }>;
  selectedConceptId: string;
  onSelectConcept: (id: string) => void;
  // Practice attempt
  currentQuestion?: any;
  onPracticeSubmit?: (answer: string, reasoning: string) => void;
  isSubmittingPractice?: boolean;
  latestDiagnosis?: any;
  // Tutor interaction
  conversationHistory: Array<{ role: 'user' | 'assistant'; text: string; provider?: string }>;
  onSendMessage: (msg: string) => void;
  isLoading: boolean;
}

export const CleanTutorWorkspace: React.FC<CleanTutorWorkspaceProps> = ({
  hudStatus,
  mode,
  activeConceptName,
  conceptsList,
  selectedConceptId,
  onSelectConcept,
  currentQuestion,
  onPracticeSubmit,
  isSubmittingPractice,
  latestDiagnosis,
  conversationHistory,
  onSendMessage,
  isLoading,
}) => {
  const [inputVal, setInputVal] = useState<string>('');
  const [practiceReasoning, setPracticeReasoning] = useState<string>('');
  const [selectedOption, setSelectedOption] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim() || isLoading) return;
    onSendMessage(inputVal);
    setInputVal('');
  };

  const handlePracticeAttempt = () => {
    if (!selectedOption || !onPracticeSubmit) return;
    onPracticeSubmit(selectedOption, practiceReasoning || `Chose option ${selectedOption}`);
  };

  return (
    <div className="w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-5 py-4 px-3 sm:px-6 h-[calc(100vh-4.5rem)]">
      {/* LEFT PANEL: Compact Expandable Syllabus / Sources */}
      <aside className="lg:col-span-3 bg-[#090C0E]/90 border border-[#1A2228] p-3.5 flex flex-col overflow-hidden backdrop-blur-md">
        <div className="flex items-center gap-2 pb-2.5 border-b border-[#1A2228] mb-3 text-xs font-mono text-[#8EA7B5]">
          <Layers className="w-4 h-4 text-[#00D9FF]" />
          <span className="uppercase tracking-wider font-semibold">SYLLABUS TREE</span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1 font-mono text-xs pr-1">
          {conceptsList.map((c) => {
            const isSelected = c.id === selectedConceptId;
            return (
              <button
                key={c.id}
                onClick={() => onSelectConcept(c.id)}
                className={`w-full text-left p-2 transition-all flex flex-col gap-0.5 border ${
                  isSelected
                    ? 'bg-[#10171D] border-[#00D9FF] text-[#00D9FF] shadow-[inset_0_0_8px_rgba(0,217,255,0.1)]'
                    : 'bg-transparent border-transparent text-[#7F95A3] hover:text-[#E6F7FF] hover:bg-[#0D1216]'
                }`}
              >
                <span className="line-clamp-1">{c.name}</span>
                {c.prerequisites.length > 0 && (
                  <span className="text-[10px] text-[#4A5E6D]">
                    Prereqs: {c.prerequisites.length}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </aside>

      {/* CENTER: Main Tutor Conversation & Explanation Area (Majority of Screen) */}
      <main className="lg:col-span-6 bg-[#0B0E11]/90 border border-[#1A2228] p-4 flex flex-col overflow-hidden backdrop-blur-md">
        {/* Tutor Header with Small Radial Intelligence Indicator */}
        <div className="flex items-center justify-between pb-3 border-b border-[#1A2228] mb-3">
          <div className="flex items-center gap-3">
            <JarvisRadialHud status={hudStatus} size="compact" />
            <div className="flex flex-col">
              <span className="font-mono text-xs font-bold uppercase tracking-wider text-[#F0F6FC]">
                {mode === 'practice' ? 'Adaptive Assessment' : 'JARVIS Academic Intelligence'}
              </span>
              <span className="text-[11px] font-sans text-[#8EA7B5]">
                {activeConceptName || 'Universal Knowledge Model'}
              </span>
            </div>
          </div>
          <span className="font-mono text-[10px] text-[#00D9FF] px-2 py-0.5 border border-[#1A2228] bg-[#0E1418]">
            {mode.toUpperCase()} MODE
          </span>
        </div>

        {/* Central Educational Content / Practice Area */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 text-sm font-sans">
          {/* Practice Mode Layout */}
          {mode === 'practice' && currentQuestion && (
            <div className="p-4 bg-[#0F1418] border border-[#1E2830] space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-[#8EA7B5]">
                <span className="text-[#00D9FF] font-semibold">[{currentQuestion.question_id}] {currentQuestion.title}</span>
                <span>Diff: {currentQuestion.difficulty}</span>
              </div>
              <p className="text-[#E6F7FF] text-sm leading-relaxed whitespace-pre-wrap">{currentQuestion.problem_text}</p>
              {currentQuestion.code_snippet && (
                <pre className="p-3 bg-[#06080A] border border-[#1A2228] text-[#00D9FF] text-xs font-mono overflow-x-auto">
                  {currentQuestion.code_snippet}
                </pre>
              )}
              {currentQuestion.options && (
                <div className="space-y-2 pt-2">
                  {currentQuestion.options.map((opt: any) => (
                    <button
                      key={opt.id}
                      onClick={() => setSelectedOption(opt.id)}
                      className={`w-full text-left p-2.5 border text-xs font-mono transition-all flex items-center gap-2 ${
                        selectedOption === opt.id
                          ? 'border-[#00D9FF] bg-[#121A20] text-[#00D9FF]'
                          : 'border-[#1A2228] bg-[#0A0D10] text-[#8EA7B5] hover:text-[#E6F7FF] hover:border-[#2A3742]'
                      }`}
                    >
                      <span className="font-bold text-[#00D9FF]">{opt.id}:</span>
                      <span>{opt.text}</span>
                    </button>
                  ))}
                </div>
              )}

              {/* Reasoning Input for practice */}
              <div className="pt-2">
                <input
                  type="text"
                  value={practiceReasoning}
                  onChange={(e) => setPracticeReasoning(e.target.value)}
                  placeholder="Explain your reasoning (tested by Gemini AI)..."
                  className="w-full bg-[#080B0D] border border-[#1A2228] p-2 text-xs text-[#E6F7FF] placeholder-[#4D6270] focus:border-[#00D9FF] focus:outline-none font-mono"
                />
              </div>

              <button
                disabled={!selectedOption || isSubmittingPractice}
                onClick={handlePracticeAttempt}
                className="w-full py-2 bg-[#00D9FF]/20 border border-[#00D9FF] text-[#00D9FF] hover:bg-[#00D9FF]/30 disabled:opacity-40 text-xs font-mono uppercase tracking-wider font-semibold transition-all flex items-center justify-center gap-2"
              >
                {isSubmittingPractice ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}
                <span>Evaluate & Trace Mastery</span>
              </button>

              {latestDiagnosis && (
                <div className="p-3 bg-[#0A0E11] border border-[#1E2830] text-xs font-mono text-[#8EA7B5] space-y-1">
                  <div className="text-[#00D9FF] font-semibold flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>DIAGNOSIS ({latestDiagnosis.reasoning_quality})</span>
                  </div>
                  <p className="text-[#CBE7F5] font-sans text-xs">{latestDiagnosis.explanation}</p>
                </div>
              )}
            </div>
          )}

          {/* Conversation & Explanations */}
          {conversationHistory.length === 0 && mode !== 'practice' && (
            <div className="h-full flex flex-col items-center justify-center text-center text-[#4E6370] py-12">
              <Sparkles className="w-8 h-8 text-[#00D9FF]/40 mb-3" />
              <p className="text-sm font-sans text-[#7F95A3]">Ready for inquiry.</p>
              <p className="text-xs font-mono mt-1">Ask a question or select a topic to begin instruction.</p>
            </div>
          )}

          {conversationHistory.map((msg, i) => (
            <div
              key={i}
              className={`p-3.5 border text-xs sm:text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#10151A] border-[#1E2830] text-[#E6F7FF] ml-6'
                  : 'bg-[#080B0D] border-[#161D22] text-[#CBE7F5] mr-6'
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono text-[#4E6370] mb-1.5">
                <span>{msg.role === 'user' ? 'LEARNER QUERY' : 'JARVIS TUTOR'}</span>
                {msg.provider && <span className="text-[#00D9FF]">MODEL: {msg.provider}</span>}
              </div>
              <div className="whitespace-pre-wrap font-sans">{msg.text}</div>
            </div>
          ))}

          {isLoading && (
            <div className="p-3 bg-[#080B0D] border border-[#161D22] text-xs font-mono text-[#00D9FF] flex items-center gap-2 mr-6 animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>JARVIS synthesizing rigorous pedagogical breakdown...</span>
            </div>
          )}
        </div>

        {/* Input Composer */}
        <form onSubmit={handleSubmit} className="mt-3 flex gap-2 pt-2 border-t border-[#1A2228]">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            placeholder="Ask a question or explore a doubt..."
            className="flex-1 bg-[#090C0E] border border-[#1A2228] px-3 py-2 text-xs text-[#E6F7FF] placeholder-[#4D6270] focus:border-[#00D9FF] focus:outline-none font-sans"
          />
          <button
            type="submit"
            disabled={isLoading || !inputVal.trim()}
            className="px-3.5 py-2 bg-[#00D9FF]/20 border border-[#00D9FF] text-[#00D9FF] hover:bg-[#00D9FF]/30 disabled:opacity-40 text-xs font-mono font-semibold uppercase flex items-center gap-1.5 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Send</span>
          </button>
        </form>
      </main>

      {/* RIGHT PANEL: Compact Learning Context & Mastery */}
      <aside className="lg:col-span-3 bg-[#090C0E]/90 border border-[#1A2228] p-3.5 flex flex-col justify-between overflow-hidden backdrop-blur-md">
        <div>
          <div className="flex items-center gap-2 pb-2.5 border-b border-[#1A2228] mb-3 text-xs font-mono text-[#8EA7B5]">
            <BookOpen className="w-4 h-4 text-[#00D9FF]" />
            <span className="uppercase tracking-wider font-semibold">LEARNING CONTEXT</span>
          </div>

          <div className="space-y-3 font-mono text-xs text-[#8EA7B5]">
            <div>
              <span className="text-[10px] text-[#4E6370] uppercase">Active Subject</span>
              <p className="text-[#E6F7FF] text-xs font-sans mt-0.5">Computer Science</p>
            </div>
            <div>
              <span className="text-[10px] text-[#4E6370] uppercase">Selected Concept</span>
              <p className="text-[#00D9FF] text-xs font-sans mt-0.5">{activeConceptName || 'Pointers & Memory'}</p>
            </div>
            <div>
              <span className="text-[10px] text-[#4E6370] uppercase">Mastery State</span>
              <p className="text-[#E6F7FF] text-xs font-sans mt-0.5">Assessed via Binary BKT</p>
            </div>
          </div>
        </div>

        {/* Quiet footer tip */}
        <div className="p-2.5 bg-[#0D1216] border border-[#161D22] text-[11px] font-mono text-[#4E6370]">
          Casual doubts do not mutate BKT. Only formal practice updates your mastery.
        </div>
      </aside>
    </div>
  );
};
