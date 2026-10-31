import React, { useState } from 'react';
import { SessionMetrics } from '../types/hud';
import { RefreshCw, Target, Zap, ShieldCheck } from 'lucide-react';

interface OrbitalFocalHubProps {
  metrics: SessionMetrics;
  activeVectorLabel?: string;
  onCalibrateDial?: () => void;
}

export const OrbitalFocalHub: React.FC<OrbitalFocalHubProps> = ({
  metrics,
  activeVectorLabel = 'CYBER-PHYSICAL STABILIZATION',
  onCalibrateDial,
}) => {
  const [focalMetric, setFocalMetric] = useState<'bandwidth' | 'velocity' | 'retention'>('bandwidth');

  // Math calculations for SVG arcs
  // Radius definitions
  const rOuter = 160;
  const rBandwidth = 138;
  const rRetention = 116;
  const rInner = 94;

  const circumferenceBandwidth = 2 * Math.PI * rBandwidth;
  const circumferenceRetention = 2 * Math.PI * rRetention;

  // Arc lengths
  const bandwidthOffset = circumferenceBandwidth * (1 - (metrics.comprehensionBandwidth / 100) * 0.75);
  const retentionOffset = circumferenceRetention * (1 - (metrics.retentionCurve / 100) * 0.75);

  // Generate 72 degree tick marks (every 5 degrees)
  const ticks = Array.from({ length: 72 }, (_, i) => {
    const deg = i * 5;
    const isMajor = deg % 30 === 0;
    const isCard = deg % 90 === 0;
    const rad = (deg * Math.PI) / 180;
    const r1 = 168;
    const r2 = isCard ? 154 : isMajor ? 158 : 162;
    const x1 = 180 + r1 * Math.cos(rad);
    const y1 = 180 + r1 * Math.sin(rad);
    const x2 = 180 + r2 * Math.cos(rad);
    const y2 = 180 + r2 * Math.sin(rad);
    return { deg, x1, y1, x2, y2, isMajor, isCard };
  });

  return (
    <div className="relative w-full bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-6 reticle-box chamfer-card overflow-hidden">
      {/* Top Header Badge Bar */}
      <div className="flex items-center justify-between pb-3 border-b border-[#1E2830] mb-4 text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 bg-[#00D9FF] shadow-[0_0_6px_#00D9FF]" />
          <span className="text-[#8EA7B5] uppercase tracking-wider">
            ORBITAL FOCAL HUB // TELEMETRY CORE
          </span>
        </div>
        <div className="flex items-center gap-4 text-[10px] text-[#4D6270]">
          <span className="tabular-nums">AZ: 048.2°</span>
          <span className="tabular-nums">EL: +18.6°</span>
          <span className="text-[#00D9FF] border border-[#005366] px-1.5 py-0.5 bg-[#002833]/40">
            RADIAL ACTIVE
          </span>
        </div>
      </div>

      {/* Main HUD Viewport */}
      <div className="relative flex flex-col items-center justify-center">
        {/* Targeting Alignment Axes that slice like crosshairs */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-[#263844]/60 to-transparent" />
          <div className="absolute h-full w-[1px] bg-gradient-to-b from-transparent via-[#263844]/60 to-transparent" />
        </div>

        {/* Outer Corner Reticle Badges */}
        <div className="absolute top-1 left-2 text-[9px] font-mono text-[#4D6270] tracking-widest">
          SEC_01 // COGNITIVE_VECTOR
        </div>
        <div className="absolute top-1 right-2 text-[9px] font-mono text-[#4D6270] tracking-widest tabular-nums">
          DRIFT: {metrics.neuralFocusDrift} rad
        </div>

        {/* Central Concentric SVG Radial Instrumentation */}
        <div className="relative w-[300px] h-[300px] sm:w-[360px] sm:h-[360px] flex items-center justify-center my-2">
          <svg
            viewBox="0 0 360 360"
            className="w-full h-full select-none"
            aria-label="Radial HUD Cognitive Gauges"
          >
            <defs>
              {/* Cyan Arc Glow */}
              <filter id="cyanGlow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
              <linearGradient id="cyanArcGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00D9FF" />
                <stop offset="100%" stopColor="#79E8FF" />
              </linearGradient>
            </defs>

            {/* Calibrated Degree Ticks & Cardinal Labels */}
            {ticks.map((t) => (
              <line
                key={`tick-${t.deg}`}
                x1={t.x1}
                y1={t.y1}
                x2={t.x2}
                y2={t.y2}
                stroke={t.isCard ? '#00D9FF' : t.isMajor ? '#859398' : '#263844'}
                strokeWidth={t.isCard ? 1.5 : 1}
                opacity={t.isCard ? 0.9 : 0.6}
              />
            ))}

            {/* Cardinal Degree Readouts */}
            <text x="180" y="24" textAnchor="middle" fill="#8EA7B5" fontSize="8" fontFamily="JetBrains Mono" letterSpacing="0.1em">000° [N]</text>
            <text x="340" y="183" textAnchor="start" fill="#8EA7B5" fontSize="8" fontFamily="JetBrains Mono" letterSpacing="0.1em">090°</text>
            <text x="180" y="348" textAnchor="middle" fill="#8EA7B5" fontSize="8" fontFamily="JetBrains Mono" letterSpacing="0.1em">180° [S]</text>
            <text x="20" y="183" textAnchor="end" fill="#8EA7B5" fontSize="8" fontFamily="JetBrains Mono" letterSpacing="0.1em">270°</text>

            {/* Background Outer Guide Rings */}
            <circle cx="180" cy="180" r={rOuter} fill="none" stroke="#1E2830" strokeWidth="1" />
            <circle cx="180" cy="180" r={rOuter - 8} fill="none" stroke="#1E2830" strokeWidth="1" strokeDasharray="3 6" />

            {/* Slow Rotating Segmented Satellite Ring */}
            <g className="animate-orbit-slow" style={{ transformOrigin: '180px 180px' }}>
              <circle
                cx="180"
                cy="180"
                r={rOuter - 14}
                fill="none"
                stroke="#00D9FF"
                strokeWidth="1.2"
                strokeDasharray="40 80 20 60 90 70"
                opacity="0.4"
              />
              {/* Pointer Nodes on Satellite Ring */}
              <circle cx="180" cy={180 - (rOuter - 14)} r="2.5" fill="#00D9FF" />
              <circle cx={180 + (rOuter - 14)} cy="180" r="2.5" fill="#79E8FF" />
            </g>

            {/* Reverse Orbit Segmented Inner Reticle */}
            <g className="animate-orbit-reverse" style={{ transformOrigin: '180px 180px' }}>
              <circle
                cx="180"
                cy="180"
                r={rInner + 10}
                fill="none"
                stroke="#D7A65A"
                strokeWidth="1"
                strokeDasharray="15 35 10 50"
                opacity="0.5"
              />
            </g>

            {/* Bandwidth Track (Dormant Loop) */}
            <circle
              cx="180"
              cy="180"
              r={rBandwidth}
              fill="none"
              stroke="#005366"
              strokeWidth="5"
              strokeDasharray={`${circumferenceBandwidth * 0.75} ${circumferenceBandwidth * 0.25}`}
              strokeDashoffset={circumferenceBandwidth * 0.125}
              strokeLinecap="butt"
              opacity="0.3"
            />

            {/* Bandwidth Dynamic Active Arc */}
            <circle
              cx="180"
              cy="180"
              r={rBandwidth}
              fill="none"
              stroke="url(#cyanArcGrad)"
              strokeWidth="5"
              strokeDasharray={`${circumferenceBandwidth * 0.75} ${circumferenceBandwidth * 0.25}`}
              strokeDashoffset={bandwidthOffset}
              strokeLinecap="butt"
              filter="url(#cyanGlow)"
              className="transition-all duration-700 ease-out"
            />

            {/* Retention Track (Dormant Loop) */}
            <circle
              cx="180"
              cy="180"
              r={rRetention}
              fill="none"
              stroke="#263844"
              strokeWidth="3.5"
              strokeDasharray={`${circumferenceRetention * 0.75} ${circumferenceRetention * 0.25}`}
              strokeDashoffset={circumferenceRetention * 0.125}
              opacity="0.4"
            />

            {/* Retention Dynamic Active Arc */}
            <circle
              cx="180"
              cy="180"
              r={rRetention}
              fill="none"
              stroke="#D7A65A"
              strokeWidth="3.5"
              strokeDasharray={`${circumferenceRetention * 0.75} ${circumferenceRetention * 0.25}`}
              strokeDashoffset={retentionOffset}
              strokeLinecap="butt"
              className="transition-all duration-700 ease-out"
            />

            {/* Inner Core Scope Container */}
            <circle
              cx="180"
              cy="180"
              r={rInner}
              fill="#090B0D"
              stroke="#263844"
              strokeWidth="1.5"
            />
            <circle
              cx="180"
              cy="180"
              r={rInner - 4}
              fill="#111519"
              stroke="#1E2830"
              strokeWidth="1"
            />
          </svg>

          {/* Focal Hub Dynamic Center Display */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#8EA7B5] mb-0.5">
              {focalMetric === 'bandwidth' && 'COMPREHENSION BANDWIDTH'}
              {focalMetric === 'velocity' && 'MASTERY VELOCITY'}
              {focalMetric === 'retention' && 'RETENTION STABILITY'}
            </span>

            {/* Dynamic Value Display in Manrope */}
            <div className="flex items-baseline justify-center">
              <span className="text-3xl sm:text-4xl font-bold font-sans tracking-tight text-[#E6F7FF] tabular-nums">
                {focalMetric === 'bandwidth' && `${metrics.comprehensionBandwidth}`}
                {focalMetric === 'velocity' && `+${metrics.masteryVelocity}`}
                {focalMetric === 'retention' && `${metrics.retentionCurve}`}
              </span>
              <span className="font-mono text-xs text-[#00D9FF] ml-1 uppercase font-semibold">
                {focalMetric === 'bandwidth' && '%'}
                {focalMetric === 'velocity' && '%/h'}
                {focalMetric === 'retention' && '%'}
              </span>
            </div>

            {/* Active Micro-Status Pip */}
            <div className="flex items-center gap-1.5 mt-1 font-mono text-[10px] text-[#00D9FF]">
              <span className="w-1.5 h-1.5 bg-[#00D9FF] rounded-none animate-ping" />
              <span className="tracking-widest uppercase">NOMINAL COUPLING</span>
            </div>

            <span className="font-mono text-[9px] text-[#4D6270] mt-1 max-w-[140px] truncate">
              {activeVectorLabel}
            </span>
          </div>
        </div>

        {/* Tactical Metric Selector Switches (Segmented Mode Buttons) */}
        <div className="w-full max-w-sm mt-3 grid grid-cols-3 gap-2 font-mono text-xs">
          <button
            onClick={() => setFocalMetric('bandwidth')}
            className={`px-2 py-2 border transition-all text-center flex flex-col items-center gap-0.5 ${
              focalMetric === 'bandwidth'
                ? 'bg-[#171D22] border-[#00D9FF] text-[#00D9FF] shadow-[0_0_10px_rgba(0,217,255,0.2)]'
                : 'bg-[#090B0D] border-[#1E2830] text-[#8EA7B5] hover:border-[#263844] hover:text-[#E6F7FF]'
            }`}
          >
            <span className="text-[9px] tracking-wider uppercase text-[#4D6270]">BANDWIDTH</span>
            <span className="text-xs font-bold tabular-nums">{metrics.comprehensionBandwidth}%</span>
          </button>

          <button
            onClick={() => setFocalMetric('velocity')}
            className={`px-2 py-2 border transition-all text-center flex flex-col items-center gap-0.5 ${
              focalMetric === 'velocity'
                ? 'bg-[#171D22] border-[#00D9FF] text-[#00D9FF] shadow-[0_0_10px_rgba(0,217,255,0.2)]'
                : 'bg-[#090B0D] border-[#1E2830] text-[#8EA7B5] hover:border-[#263844] hover:text-[#E6F7FF]'
            }`}
          >
            <span className="text-[9px] tracking-wider uppercase text-[#4D6270]">VELOCITY</span>
            <span className="text-xs font-bold tabular-nums">+{metrics.masteryVelocity}%/h</span>
          </button>

          <button
            onClick={() => setFocalMetric('retention')}
            className={`px-2 py-2 border transition-all text-center flex flex-col items-center gap-0.5 ${
              focalMetric === 'retention'
                ? 'bg-[#171D22] border-[#D7A65A] text-[#D7A65A] shadow-[0_0_10px_rgba(215,166,90,0.2)]'
                : 'bg-[#090B0D] border-[#1E2830] text-[#8EA7B5] hover:border-[#263844] hover:text-[#E6F7FF]'
            }`}
          >
            <span className="text-[9px] tracking-wider uppercase text-[#4D6270]">RETENTION</span>
            <span className="text-xs font-bold tabular-nums">{metrics.retentionCurve}%</span>
          </button>
        </div>

        {/* Quick Calibration Bar Trigger */}
        <div className="w-full flex items-center justify-between mt-4 pt-3 border-t border-[#1E2830] text-[11px] font-mono text-[#8EA7B5]">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 border border-[#00D9FF] flex items-center justify-center">
              <span className="w-1 h-1 bg-[#00D9FF]" />
            </span>
            <span>TOTAL CYCLES: <strong className="text-[#E6F7FF] tabular-nums">{metrics.totalCycles}</strong></span>
          </span>

          {onCalibrateDial && (
            <button
              onClick={onCalibrateDial}
              className="text-[#00D9FF] hover:underline flex items-center gap-1 text-[10px] uppercase tracking-wider"
            >
              <RefreshCw className="w-3 h-3" />
              Recalibrate Gauges
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
