import React from 'react';
import { Sparkles, Compass, BookOpen, CheckCircle, BarChart3 } from 'lucide-react';

export type DestinationTab = 'home' | 'learn' | 'ask' | 'practice' | 'progress';

interface MinimalNavProps {
  activeTab: DestinationTab;
  onSelectTab: (tab: DestinationTab) => void;
  learnerName?: string;
}

export const MinimalNav: React.FC<MinimalNavProps> = ({
  activeTab,
  onSelectTab,
  learnerName = 'Arjun Sharma',
}) => {
  const navItems: Array<{ id: DestinationTab; label: string; icon: React.ReactNode }> = [
    { id: 'home', label: 'Home', icon: <Sparkles className="w-3.5 h-3.5" /> },
    { id: 'learn', label: 'Learn', icon: <BookOpen className="w-3.5 h-3.5" /> },
    { id: 'ask', label: 'Ask', icon: <Compass className="w-3.5 h-3.5" /> },
    { id: 'practice', label: 'Practice', icon: <CheckCircle className="w-3.5 h-3.5" /> },
    { id: 'progress', label: 'Progress', icon: <BarChart3 className="w-3.5 h-3.5" /> },
  ];

  return (
    <header className="w-full bg-[#07090B]/90 backdrop-blur-md border-b border-[#1A2228] z-30 sticky top-0">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => onSelectTab('home')}
            className="flex items-center gap-2.5 text-left group transition-all"
          >
            <div className="w-2.5 h-2.5 bg-[#00D9FF] rotate-45 border border-[#B7F4FF] shadow-[0_0_10px_rgba(0,217,255,0.7)] group-hover:scale-110 transition-transform" />
            <span className="font-mono font-bold tracking-wider text-sm sm:text-base text-[#F0F6FC]">
              Concept<span className="text-[#00D9FF]">IQ</span>
            </span>
          </button>
          <span className="hidden sm:inline-block text-[10px] font-mono tracking-widest text-[#4D6270] uppercase px-1.5 py-0.5 border border-[#1A2228]">
            AI TUTOR
          </span>
        </div>

        {/* 5 Clean Destinations */}
        <nav className="flex items-center gap-2 sm:gap-6 font-mono text-xs tracking-wider uppercase text-[#8EA7B5]">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`flex items-center gap-1.5 py-1.5 px-2 relative transition-colors ${
                  isActive ? 'text-[#00D9FF] font-semibold' : 'hover:text-[#E6F7FF]'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
                {isActive && (
                  <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#00D9FF] shadow-[0_0_8px_#00D9FF]" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Learner Pill */}
        <div className="hidden md:flex items-center gap-2 text-xs font-mono text-[#8EA7B5] px-2.5 py-1 bg-[#101418] border border-[#1A2228]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#00D9FF] animate-pulse" />
          <span>{learnerName}</span>
        </div>
      </div>
    </header>
  );
};

