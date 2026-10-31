import React from 'react';

interface JarvisRadialHudProps {
  status: 'IDLE' | 'LISTENING' | 'THINKING' | 'RESPONDING' | 'ASSESSING';
  size?: 'normal' | 'compact';
  activeConcept?: string;
}

export const JarvisRadialHud: React.FC<JarvisRadialHudProps> = ({
  status = 'IDLE',
  size = 'normal',
  activeConcept,
}) => {
  const isCompact = size === 'compact';
  const dim = isCompact ? 120 : 320;
  const center = dim / 2;

  // Status-based colors & glow
  const statusColors = {
    IDLE: { stroke: '#00D9FF', glow: 'rgba(0, 217, 255, 0.4)', text: 'SYSTEM IDLE' },
    LISTENING: { stroke: '#38BDF8', glow: 'rgba(56, 189, 248, 0.7)', text: 'LISTENING...' },
    THINKING: { stroke: '#818CF8', glow: 'rgba(129, 140, 248, 0.8)', text: 'SYNTHESIZING...' },
    RESPONDING: { stroke: '#00F0FF', glow: 'rgba(0, 240, 255, 0.9)', text: 'TRANSMITTING' },
    ASSESSING: { stroke: '#F59E0B', glow: 'rgba(245, 158, 11, 0.7)', text: 'ASSESSING' },
  };

  const currentTheme = statusColors[status] || statusColors.IDLE;

  // Neural network nodes in center
  const neuralNodes = isCompact
    ? [
        { cx: center, cy: center, r: 2.5 },
        { cx: center - 12, cy: center - 6, r: 1.8 },
        { cx: center + 12, cy: center - 6, r: 1.8 },
        { cx: center - 8, cy: center + 10, r: 1.8 },
        { cx: center + 8, cy: center + 10, r: 1.8 },
      ]
    : [
        { cx: center, cy: center, r: 4.5 },
        { cx: center - 26, cy: center - 14, r: 3 },
        { cx: center + 26, cy: center - 14, r: 3 },
        { cx: center - 18, cy: center + 22, r: 3 },
        { cx: center + 18, cy: center + 22, r: 3 },
        { cx: center, cy: center - 28, r: 2.5 },
      ];

  return (
    <div className={`relative flex flex-col items-center justify-center select-none ${isCompact ? '' : 'my-4'}`}>
      <svg
        width={dim}
        height={dim}
        viewBox={`0 0 ${dim} ${dim}`}
        className="overflow-visible"
        style={{ filter: `drop-shadow(0 0 16px ${currentTheme.glow})` }}
      >
        {/* Outermost Thin Reference Ring */}
        <circle
          cx={center}
          cy={center}
          r={center - (isCompact ? 8 : 16)}
          fill="none"
          stroke="#1E2830"
          strokeWidth="1"
          strokeDasharray="4 6"
        />

        {/* Orbiting Segmented Arcs (Slow Rotation) */}
        <circle
          cx={center}
          cy={center}
          r={center - (isCompact ? 16 : 32)}
          fill="none"
          stroke={currentTheme.stroke}
          strokeWidth={isCompact ? '1.5' : '2'}
          strokeDasharray={isCompact ? '40 20 15 25' : '110 50 40 60'}
          strokeLinecap="round"
          className="origin-center animate-[spin_24s_linear_infinite]"
          opacity="0.85"
        />

        {/* Counter-Rotating Precision Arc */}
        <circle
          cx={center}
          cy={center}
          r={center - (isCompact ? 24 : 52)}
          fill="none"
          stroke="#00D9FF"
          strokeWidth="1"
          strokeDasharray={isCompact ? '25 35' : '65 75'}
          className="origin-center animate-[spin_18s_linear_infinite_reverse]"
          opacity="0.6"
        />

        {/* Inner Glowing Reticle Ring */}
        <circle
          cx={center}
          cy={center}
          r={center - (isCompact ? 32 : 72)}
          fill="none"
          stroke={currentTheme.stroke}
          strokeWidth="1.5"
          className={status === 'THINKING' ? 'animate-pulse' : ''}
          opacity="0.9"
        />

        {/* Neural Interconnection Lines */}
        {neuralNodes.map((node, i) =>
          neuralNodes.slice(i + 1).map((targetNode, j) => (
            <line
              key={`${i}-${j}`}
              x1={node.cx}
              y1={node.cy}
              x2={targetNode.cx}
              y2={targetNode.cy}
              stroke={currentTheme.stroke}
              strokeWidth="0.8"
              opacity="0.35"
            />
          ))
        )}

        {/* Neural Nodes */}
        {neuralNodes.map((node, i) => (
          <circle
            key={i}
            cx={node.cx}
            cy={node.cy}
            r={node.r}
            fill={currentTheme.stroke}
            className="animate-pulse"
          />
        ))}

        {/* Central Pulsing Nucleus */}
        <circle
          cx={center}
          cy={center}
          r={isCompact ? 2 : 3.5}
          fill="#FFFFFF"
          className="animate-ping"
          style={{ animationDuration: '3s' }}
        />
      </svg>

      {/* Clean Status & Intelligence Label (Hidden in compact header mode) */}
      {!isCompact && (
        <div className="mt-4 flex flex-col items-center font-mono">
          <div className="flex items-center gap-2">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: currentTheme.stroke, boxShadow: `0 0 8px ${currentTheme.stroke}` }}
            />
            <span className="text-xs tracking-widest text-[#00D9FF] uppercase font-semibold">
              {currentTheme.text}
            </span>
          </div>
          {activeConcept && (
            <span className="text-[11px] text-[#8EA7B5] mt-1 tracking-wider uppercase">
              {activeConcept}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
