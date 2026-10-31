import React from 'react';
import { JarvisRadialHud } from './JarvisRadialHud';
import { Mic, Paperclip, Send, BookOpen, HelpCircle, FileSearch, ArrowRight } from 'lucide-react';

interface CleanHomeScreenProps {
  status: 'IDLE' | 'LISTENING' | 'THINKING' | 'RESPONDING' | 'ASSESSING';
  query: string;
  onQueryChange: (val: string) => void;
  onSubmit: (e?: React.FormEvent) => void;
  isLoading: boolean;
  onSelectAction: (mode: 'learn' | 'ask' | 'practice') => void;
  activeConceptName?: string;
  recentModules: Array<{ id: string; title: string; mastery: number }>;
  onContinueConcept: (conceptId: string) => void;
}

export const CleanHomeScreen: React.FC<CleanHomeScreenProps> = ({
  status,
  query,
  onQueryChange,
  onSubmit,
  isLoading,
  onSelectAction,
  activeConceptName,
  recentModules,
  onContinueConcept,
}) => {
  return (
    <div className="w-full max-w-3xl mx-auto flex flex-col items-center justify-center py-6 sm:py-10 px-4">
      {/* 1. Centerpiece: One Elegant Circular JARVIS Radial HUD */}
      <JarvisRadialHud
        status={status}
        size="normal"
        activeConcept={activeConceptName}
      />

      {/* 2. Prominent Tutor Input Box */}
      <form
        onSubmit={onSubmit}
        className="w-full mt-6 bg-[#0E1216]/90 border border-[#1E2830] focus-within:border-[#00D9FF] focus-within:shadow-[0_0_15px_rgba(0,217,255,0.15)] transition-all p-2 rounded-none backdrop-blur-md"
      >
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            placeholder="What would you like to understand?"
            className="flex-1 bg-transparent px-3 py-2 text-sm text-[#F0F6FC] placeholder-[#4D6270] focus:outline-none font-sans"
          />

          {/* Action Icons */}
          <div className="flex items-center gap-1 shrink-0 text-[#8EA7B5]">
            <button
              type="button"
              title="Voice dictation (Wispr Flow compatible)"
              className="p-2 hover:text-[#00D9FF] hover:bg-[#161D23] transition-colors"
            >
              <Mic className="w-4 h-4" />
            </button>
            <button
              type="button"
              title="Attach diagram or document"
              className="p-2 hover:text-[#00D9FF] hover:bg-[#161D23] transition-colors"
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="px-3 py-1.5 bg-[#00D9FF]/20 border border-[#00D9FF] text-[#00D9FF] hover:bg-[#00D9FF]/30 disabled:opacity-40 text-xs font-mono font-semibold uppercase flex items-center gap-1.5 transition-colors"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Inquire</span>
            </button>
          </div>
        </div>
      </form>

      {/* 3. Three Compact Action Options */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full mt-4 font-mono text-xs">
        <button
          onClick={() => onSelectAction('learn')}
          className="flex items-center justify-center gap-2 p-3 bg-[#0B0E11]/80 border border-[#1A2228] hover:border-[#00D9FF] hover:bg-[#12171C] text-[#8EA7B5] hover:text-[#00D9FF] transition-all"
        >
          <BookOpen className="w-4 h-4 text-[#00D9FF]" />
          <span>Teach a topic</span>
        </button>

        <button
          onClick={() => onSelectAction('ask')}
          className="flex items-center justify-center gap-2 p-3 bg-[#0B0E11]/80 border border-[#1A2228] hover:border-[#00D9FF] hover:bg-[#12171C] text-[#8EA7B5] hover:text-[#00D9FF] transition-all"
        >
          <HelpCircle className="w-4 h-4 text-[#00D9FF]" />
          <span>Clear a doubt</span>
        </button>

        <button
          onClick={() => onSelectAction('practice')}
          className="flex items-center justify-center gap-2 p-3 bg-[#0B0E11]/80 border border-[#1A2228] hover:border-[#00D9FF] hover:bg-[#12171C] text-[#8EA7B5] hover:text-[#00D9FF] transition-all"
        >
          <FileSearch className="w-4 h-4 text-[#00D9FF]" />
          <span>Practice & Diagnose</span>
        </button>
      </div>

      {/* 4. Compact Continue Learning Section */}
      {recentModules.length > 0 && (
        <div className="w-full mt-8 pt-6 border-t border-[#161D22]">
          <div className="flex items-center justify-between mb-3 text-xs font-mono text-[#8EA7B5]">
            <span className="uppercase tracking-wider">Continue Learning</span>
            <span className="text-[10px] text-[#4D6270]">ACTIVE SYLLABUS FRONTIER</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {recentModules.slice(0, 4).map((mod) => (
              <button
                key={mod.id}
                onClick={() => onContinueConcept(mod.id)}
                className="group flex items-center justify-between p-3 bg-[#0A0D10]/90 border border-[#1A2228] hover:border-[#00D9FF] hover:bg-[#101418] transition-all text-left"
              >
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs font-sans text-[#E6F7FF] group-hover:text-[#00D9FF] transition-colors line-clamp-1">
                    {mod.title}
                  </span>
                  <span className="text-[10px] font-mono text-[#6A8190]">
                    Mastery: {mod.mastery}%
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 text-[#3C4E5B] group-hover:text-[#00D9FF] group-hover:translate-x-0.5 transition-all" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
