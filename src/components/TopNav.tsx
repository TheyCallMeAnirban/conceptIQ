import React from 'react';
import { Crosshair, Sliders, Activity } from 'lucide-react';

interface TopNavProps {
  activeTab: 'telemetry' | 'simulation' | 'topology' | 'socratic';
  onSelectTab: (tab: 'telemetry' | 'simulation' | 'topology' | 'socratic') => void;
  onOpenCalibration: () => void;
  sessionTime: string;
}

export const TopNav: React.FC<TopNavProps> = ({
  activeTab,
  onSelectTab,
  onOpenCalibration,
  sessionTime,
}) => {
  return (
    <header className="w-full bg-[#090B0D]/95 backdrop-blur-md border-b border-[#1E2830] z-40 sticky top-0">
      <div className="max-w-[1720px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-8">
        {/* Zone 1: Brand Wordmark */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-2.5 h-2.5 bg-[#00D9FF] rotate-45 border border-[#B7F4FF] shadow-[0_0_8px_rgba(0,217,255,0.8)]" />
          <button
            onClick={() => onSelectTab('telemetry')}
            className="text-left font-mono font-bold tracking-wider text-sm sm:text-base text-[#E6F7FF] hover:text-[#00D9FF] transition-colors whitespace-nowrap"
          >
            RADIAL HUD <span className="text-[#00D9FF] font-light">CYBER-PHYSICAL TUTOR</span>
          </button>
          <span className="hidden xl:inline-block text-[10px] font-mono tracking-widest text-[#4D6270] uppercase px-1.5 py-0.5 border border-[#1E2830]">
            GRID: 1440.ORTHO
          </span>
        </div>

        {/* Zone 2: Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 font-mono text-xs tracking-wider uppercase text-[#8EA7B5]">
          <button
            onClick={() => onSelectTab('telemetry')}
            className={`transition-colors whitespace-nowrap py-1 relative ${
              activeTab === 'telemetry'
                ? 'text-[#00D9FF] font-semibold'
                : 'hover:text-[#E6F7FF]'
            }`}
          >
            Telemetry Hub
            {activeTab === 'telemetry' && (
              <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#00D9FF] shadow-[0_0_6px_#00D9FF]" />
            )}
          </button>

          <button
            onClick={() => onSelectTab('simulation')}
            className={`transition-colors whitespace-nowrap py-1 relative ${
              activeTab === 'simulation'
                ? 'text-[#00D9FF] font-semibold'
                : 'hover:text-[#E6F7FF]'
            }`}
          >
            Simulation Lab
            {activeTab === 'simulation' && (
              <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#00D9FF] shadow-[0_0_6px_#00D9FF]" />
            )}
          </button>

          <button
            onClick={() => onSelectTab('topology')}
            className={`transition-colors whitespace-nowrap py-1 relative ${
              activeTab === 'topology'
                ? 'text-[#00D9FF] font-semibold'
                : 'hover:text-[#E6F7FF]'
            }`}
          >
            Knowledge Topology
            {activeTab === 'topology' && (
              <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#00D9FF] shadow-[0_0_6px_#00D9FF]" />
            )}
          </button>

          <button
            onClick={() => onSelectTab('socratic')}
            className={`transition-colors whitespace-nowrap py-1 relative ${
              activeTab === 'socratic'
                ? 'text-[#00D9FF] font-semibold'
                : 'hover:text-[#E6F7FF]'
            }`}
          >
            Socratic Stream
            {activeTab === 'socratic' && (
              <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#00D9FF] shadow-[0_0_6px_#00D9FF]" />
            )}
          </button>
        </nav>

        {/* Zone 3: Primary Action & MET Clock */}
        <div className="flex items-center gap-2 sm:gap-4 shrink-0">
          <div className="hidden sm:flex items-center gap-2 font-mono text-[11px] text-[#8EA7B5] tabular-nums border border-[#1E2830] px-2.5 py-1 bg-[#111519]/70">
            <span className="text-[#4D6270]">MET:</span>
            <span className="text-[#00D9FF] font-medium">{sessionTime}</span>
          </div>

          <button
            onClick={onOpenCalibration}
            aria-label="Calibrate system sensors"
            className="chamfer-btn px-2.5 sm:px-3.5 py-1.5 bg-[#090B0D] border border-[#00D9FF] text-[#00D9FF] font-mono text-[11px] sm:text-xs font-bold uppercase tracking-wider hud-sweep-btn flex items-center gap-1.5 shadow-[0_0_8px_rgba(0,217,255,0.25)]"
          >
            <Crosshair className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Calibrate</span>
          </button>
        </div>
      </div>

      {/* Mobile Navigation Strip (< md screens) */}
      <div className="md:hidden flex items-center justify-around border-t border-[#1E2830] bg-[#090B0D] px-2 py-1.5 font-mono text-[10px] uppercase tracking-wider overflow-x-auto">
        <button
          onClick={() => onSelectTab('telemetry')}
          className={`px-2 py-1 whitespace-nowrap ${
            activeTab === 'telemetry' ? 'text-[#00D9FF] border-b border-[#00D9FF] font-bold' : 'text-[#8EA7B5]'
          }`}
        >
          Telemetry
        </button>
        <button
          onClick={() => onSelectTab('simulation')}
          className={`px-2 py-1 whitespace-nowrap ${
            activeTab === 'simulation' ? 'text-[#00D9FF] border-b border-[#00D9FF] font-bold' : 'text-[#8EA7B5]'
          }`}
        >
          Simulation
        </button>
        <button
          onClick={() => onSelectTab('topology')}
          className={`px-2 py-1 whitespace-nowrap ${
            activeTab === 'topology' ? 'text-[#00D9FF] border-b border-[#00D9FF] font-bold' : 'text-[#8EA7B5]'
          }`}
        >
          Topology
        </button>
        <button
          onClick={() => onSelectTab('socratic')}
          className={`px-2 py-1 whitespace-nowrap ${
            activeTab === 'socratic' ? 'text-[#00D9FF] border-b border-[#00D9FF] font-bold' : 'text-[#8EA7B5]'
          }`}
        >
          Socratic
        </button>
      </div>
    </header>
  );
};
