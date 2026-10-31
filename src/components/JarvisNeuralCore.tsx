import React from 'react';

export type IntelligenceState = 'IDLE' | 'LISTENING' | 'THINKING' | 'RESPONDING' | 'ERROR';

interface JarvisNeuralCoreProps {
  state: IntelligenceState;
  size?: 'workspace-header' | 'centerpiece';
  activeTopic?: string;
}

export const JarvisNeuralCore: React.FC<JarvisNeuralCoreProps> = ({
  state = 'IDLE',
  size = 'workspace-header',
  activeTopic,
}) => {
  const isHeader = size === 'workspace-header';
  const dim = isHeader ? 72 : 280;
  const center = dim / 2;

  // Visual palettes based on actual intelligence state
  const statePalettes = {
    IDLE: {
      primary: '#00D9FF',
      amber: '#F59E0B',
      glow: 'rgba(0, 217, 255, 0.35)',
      statusText: 'JARVIS IDLE',
      speed: '32s',
      pulse: false,
    },
    LISTENING: {
      primary: '#38BDF8',
      amber: '#FBBF24',
      glow: 'rgba(56, 189, 248, 0.7)',
      statusText: 'LISTENING...',
      speed: '16s',
      pulse: true,
    },
    THINKING: {
      primary: '#818CF8',
      amber: '#F59E0B',
      glow: 'rgba(129, 140, 248, 0.85)',
      statusText: 'THINKING',
      speed: '8s',
      pulse: true,
    },
    RESPONDING: {
      primary: '#00F0FF',
      amber: '#F59E0B',
      glow: 'rgba(0, 240, 255, 0.9)',
      statusText: 'RESPONDING',
      speed: '12s',
      pulse: true,
    },
    ERROR: {
      primary: '#EF4444',
      amber: '#DC2626',
      glow: 'rgba(239, 68, 68, 0.8)',
      statusText: 'CAUTION',
      speed: '40s',
      pulse: false,
    },
  };

  const palette = statePalettes[state] || statePalettes.IDLE;

  // Interconnected neural nodes
  const nodes = isHeader
    ? [
        { cx: center, cy: center, r: 2.2, isAmber: false },
        { cx: center - 9, cy: center - 5, r: 1.5, isAmber: true },
        { cx: center + 9, cy: center - 5, r: 1.5, isAmber: false },
        { cx: center - 6, cy: center + 8, r: 1.5, isAmber: false },
        { cx: center + 6, cy: center + 8, r: 1.5, isAmber: true },
      ]
    : [
        { cx: center, cy: center, r: 4.5, isAmber: false },
        { cx: center - 24, cy: center - 14, r: 3, isAmber: true },
        { cx: center + 24, cy: center - 14, r: 3, isAmber: false },
        { cx: center - 16, cy: center + 20, r: 3, isAmber: false },
        { cx: center + 16, cy: center + 20, r: 3, isAmber: true },
        { cx: center, cy: center - 26, r: 2.5, isAmber: false },
      ];

  return (
    <div className="flex items-center gap-3 select-none">
      <div className="relative shrink-0 flex items-center justify-center">
        <svg
          width={dim}
          height={dim}
          viewBox={`0 0 ${dim} ${dim}`}
          className="overflow-visible"
          style={{ filter: `drop-shadow(0 0 12px ${palette.glow})` }}
        >
          {/* Outer Segmented Calibration Arc */}
          <circle
            cx={center}
            cy={center}
            r={center - (isHeader ? 4 : 12)}
            fill="none"
            stroke="#1B2631"
            strokeWidth="1"
            strokeDasharray={isHeader ? '12 8' : '40 20'}
          />

          {/* Clockwise Segmented Arc with Cyan and Amber accents */}
          <circle
            cx={center}
            cy={center}
            r={center - (isHeader ? 9 : 28)}
            fill="none"
            stroke={palette.primary}
            strokeWidth={isHeader ? '1.5' : '2'}
            strokeDasharray={isHeader ? '25 15 10 20' : '90 40 30 50'}
            strokeLinecap="round"
            className="origin-center animate-[spin_linear_infinite]"
            style={{ animationDuration: palette.speed }}
          />

          {/* Counter-Rotating Inner Guidance Ring */}
          <circle
            cx={center}
            cy={center}
            r={center - (isHeader ? 15 : 48)}
            fill="none"
            stroke={palette.amber}
            strokeWidth="1"
            strokeDasharray={isHeader ? '15 25' : '40 60'}
            className="origin-center animate-[spin_linear_infinite_reverse]"
            style={{ animationDuration: isHeader ? '20s' : '15s', opacity: 0.7 }}
          />

          {/* Neural Pathways (Interconnections) */}
          {nodes.map((node, i) =>
            nodes.slice(i + 1).map((target, j) => (
              <line
                key={`${i}-${j}`}
                x1={node.cx}
                y1={node.cy}
                x2={target.cx}
                y2={target.cy}
                stroke={node.isAmber ? palette.amber : palette.primary}
                strokeWidth={isHeader ? '0.6' : '0.9'}
                opacity={state === 'THINKING' ? 0.7 : 0.35}
              />
            ))
          )}

          {/* Neural Nodes */}
          {nodes.map((node, i) => (
            <circle
              key={i}
              cx={node.cx}
              cy={node.cy}
              r={node.r}
              fill={node.isAmber ? palette.amber : palette.primary}
              className={palette.pulse ? 'animate-pulse' : ''}
            />
          ))}

          {/* Central Core Nucleus */}
          <circle
            cx={center}
            cy={center}
            r={isHeader ? 1.8 : 3}
            fill="#FFFFFF"
            className="animate-ping"
            style={{ animationDuration: state === 'THINKING' ? '1.5s' : '3.5s' }}
          />
        </svg>
      </div>

      {/* Accompanying Identity & State Details */}
      <div className="flex flex-col font-mono leading-tight">
        <div className="flex items-center gap-2">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: palette.primary, boxShadow: `0 0 6px ${palette.primary}` }}
          />
          <span className="text-[11px] font-bold text-[#F0F6FC] tracking-wider uppercase">
            CONCEPTIQ // <span style={{ color: palette.primary }}>{palette.statusText}</span>
          </span>
        </div>
        {activeTopic && (
          <span className="text-[10px] text-[#8EA7B5] mt-0.5 tracking-wide line-clamp-1">
            {activeTopic}
          </span>
        )}
      </div>
    </div>
  );
};

