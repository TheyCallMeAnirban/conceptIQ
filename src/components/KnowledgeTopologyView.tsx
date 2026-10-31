import React, { useState } from 'react';
import { CognitiveVector, ModuleTrack } from '../types/hud';
import { CognitiveRadar } from './CognitiveRadar';
import { calculateRetentionDecay } from '../lib/tutor-engine';
import { Activity, Clock, ShieldAlert, CheckCircle, TrendingUp } from 'lucide-react';

interface KnowledgeTopologyViewProps {
  vectors: CognitiveVector[];
  modules: ModuleTrack[];
  onSelectModule: (id: string) => void;
}

export const KnowledgeTopologyView: React.FC<KnowledgeTopologyViewProps> = ({
  vectors,
  modules,
  onSelectModule,
}) => {
  const [selectedVectorId, setSelectedVectorId] = useState<string>(vectors[0]?.id || 'vec_cyber');
  const [decayHours, setDecayHours] = useState<number>(24);

  const selectedVector = vectors.find((v) => v.id === selectedVectorId) || vectors[0];

  // Retention curve points across 0 to 72 hours
  const hoursArray = [0, 6, 12, 18, 24, 36, 48, 60, 72];
  const decayPoints = hoursArray.map((h) => ({
    hour: h,
    retained: calculateRetentionDecay(selectedVector.value, h, 28),
  }));

  const chartW = 500;
  const chartH = 180;
  const pLeft = 35;
  const pRight = 15;
  const pTop = 15;
  const pBottom = 25;
  const pw = chartW - pLeft - pRight;
  const ph = chartH - pTop - pBottom;

  const getX = (h: number) => pLeft + (h / 72) * pw;
  const getY = (v: number) => pTop + ph - (v / 100) * ph;

  const polylinePoints = decayPoints
    .map((p) => `${getX(p.hour).toFixed(1)},${getY(p.retained).toFixed(1)}`)
    .join(' ');

  const currentProjected = calculateRetentionDecay(selectedVector.value, decayHours, 28);

  return (
    <div className="w-full space-y-6">
      {/* Viewport Header */}
      <div className="bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 reticle-box chamfer-card">
        <div className="flex items-center gap-2 text-xs font-mono text-[#00D9FF]">
          <Activity className="w-4 h-4" />
          <span>// COGNITIVE MANIFOLD</span>
          <span className="text-[#4D6270]">·</span>
          <span className="text-[#8EA7B5]">EBBINGHAUS RETENTION & TOPOLOGY</span>
        </div>
        <h2 className="text-xl sm:text-2xl font-bold font-sans text-[#E6F7FF] mt-1">
          Knowledge Vector Stability & Neural Decay
        </h2>
      </div>

      {/* 2-Column Layout: Radar + Retention Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: 6-Axis Radar (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <CognitiveRadar
            vectors={vectors}
            selectedVectorId={selectedVectorId}
            onSelectVector={(id) => setSelectedVectorId(id)}
          />
        </div>

        {/* Right Column: Ebbinghaus Retention Decay Model (7 cols) */}
        <div className="lg:col-span-7 bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-5 reticle-box chamfer-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#1E2830] mb-4 text-xs font-mono">
              <div className="flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-[#00D9FF]" />
                <span className="text-[#8EA7B5] uppercase">
                  RETENTION DECAY MODEL // {selectedVector.label}
                </span>
              </div>
              <span className="text-[10px] text-[#4D6270] tabular-nums">
                STABILITY COEFF: S = 28h
              </span>
            </div>

            {/* Retention SVG Curve */}
            <div className="bg-[#090B0D] border border-[#263844] p-3 overflow-x-auto">
              <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full h-auto min-w-[400px]">
                {/* Horizontal Guides (0%, 25%, 50%, 75%, 100%) */}
                {[0, 25, 50, 75, 100].map((val) => {
                  const y = getY(val);
                  return (
                    <g key={`ret-guide-${val}`}>
                      <line
                        x1={pLeft}
                        y1={y}
                        x2={chartW - pRight}
                        y2={y}
                        stroke="#1E2830"
                        strokeWidth="1"
                        strokeDasharray="2 3"
                      />
                      <text
                        x={pLeft - 6}
                        y={y + 3}
                        textAnchor="end"
                        fill="#4D6270"
                        fontSize="8.5"
                        fontFamily="JetBrains Mono"
                      >
                        {val}%
                      </text>
                    </g>
                  );
                })}

                {/* Vertical Time Guides (0h, 24h, 48h, 72h) */}
                {[0, 24, 48, 72].map((h) => {
                  const x = getX(h);
                  return (
                    <g key={`time-guide-${h}`}>
                      <line
                        x1={x}
                        y1={pTop}
                        x2={x}
                        y2={chartH - pBottom}
                        stroke="#1E2830"
                        strokeWidth="1"
                        strokeDasharray="2 3"
                      />
                      <text
                        x={x}
                        y={chartH - pBottom + 12}
                        textAnchor="middle"
                        fill="#4D6270"
                        fontSize="8.5"
                        fontFamily="JetBrains Mono"
                      >
                        {h}h
                      </text>
                    </g>
                  );
                })}

                {/* Decay Curve Polyline */}
                <polyline
                  points={polylinePoints}
                  fill="none"
                  stroke="#D7A65A"
                  strokeWidth="2"
                  strokeLinecap="round"
                />

                {/* Dynamic Projected Node at decayHours */}
                <circle
                  cx={getX(decayHours)}
                  cy={getY(currentProjected)}
                  r="5"
                  fill="#00D9FF"
                  stroke="#090B0D"
                  strokeWidth="2"
                />
              </svg>
            </div>

            {/* Time Horizon Interactive Scrubber */}
            <div className="mt-4 p-3 bg-[#090B0D] border border-[#1E2830] space-y-2">
              <div className="flex justify-between items-center text-xs font-mono">
                <span className="text-[#8EA7B5]">Simulate Elapsed Horizon:</span>
                <span className="text-[#00D9FF] font-bold tabular-nums">
                  T + {decayHours} HOURS
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="72"
                step="2"
                value={decayHours}
                onChange={(e) => setDecayHours(parseInt(e.target.value))}
                className="w-full h-1.5 bg-[#171D22] appearance-none cursor-pointer accent-[#00D9FF] border border-[#263844]"
              />
              <div className="flex justify-between text-[10px] font-mono text-[#4D6270]">
                <span>Immediate (0h)</span>
                <span>Interval: 1 Day (24h)</span>
                <span>Horizon (72h)</span>
              </div>
            </div>
          </div>

          {/* Retention Telemetry Metrics */}
          <div className="grid grid-cols-3 gap-3 mt-4 pt-4 border-t border-[#1E2830] font-mono text-xs">
            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">BASE MASTERY</span>
              <span className="text-base font-bold text-[#E6F7FF] tabular-nums">
                {selectedVector.value}%
              </span>
            </div>

            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">PROJECTED AT T+{decayHours}h</span>
              <span
                className={`text-base font-bold tabular-nums ${
                  currentProjected < 60 ? 'text-[#D7A65A]' : 'text-[#00D9FF]'
                }`}
              >
                {currentProjected}%
              </span>
            </div>

            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">RECOMMENDATION</span>
              <span className="text-[11px] font-semibold text-[#8EA7B5] block mt-1">
                {currentProjected < 70 ? 'SPACED REVIEW REQ' : 'MASTERY CONSOLIDATED'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Sub-Concept Curriculum Matrix */}
      <div className="bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-5 reticle-box chamfer-card">
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2830] mb-4 text-xs font-mono">
          <span className="text-[#8EA7B5] uppercase">
            CROSS-DISCIPLINARY COGNITIVE MATRIX
          </span>
          <span className="text-[10px] text-[#4D6270]">
            TOTAL TRACKS: {modules.length}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {modules.map((m) => (
            <div
              key={m.id}
              onClick={() => onSelectModule(m.id)}
              className="p-3 bg-[#090B0D] border border-[#1E2830] hover:border-[#00D9FF] cursor-pointer transition-colors group flex flex-col justify-between"
            >
              <div>
                <span className="font-mono text-[10px] text-[#00D9FF] block mb-1">
                  {m.code}
                </span>
                <h4 className="font-sans text-xs font-semibold text-[#E6F7FF] group-hover:text-[#00D9FF] transition-colors line-clamp-1">
                  {m.title}
                </h4>
                <p className="font-sans text-[11px] text-[#8EA7B5] mt-1 line-clamp-2">
                  {m.problemPrompt.description}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-[#1E2830] flex items-center justify-between font-mono text-[10px] text-[#4D6270] tabular-nums">
                <span>MASTERY: <strong className="text-[#E6F7FF]">{m.mastery}%</strong></span>
                <span
                  className={m.status === 'review_required' ? 'text-[#D7A65A]' : 'text-[#00D9FF]'}
                >
                  {m.status.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
