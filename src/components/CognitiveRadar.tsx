import React, { useState } from 'react';
import { CognitiveVector } from '../types/hud';
import { calculateSpiderRadarVertices, RadarPoint } from '../lib/tutor-engine';
import { Activity, Zap, AlertTriangle } from 'lucide-react';

interface CognitiveRadarProps {
  vectors: CognitiveVector[];
  selectedVectorId?: string;
  onSelectVector: (id: string) => void;
}

export const CognitiveRadar: React.FC<CognitiveRadarProps> = ({
  vectors,
  selectedVectorId,
  onSelectVector,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<RadarPoint | null>(null);

  const size = 320;
  const center = { x: size / 2, y: size / 2 };
  const radius = 105;

  // Calculate coordinates for current values
  const currentVertices = calculateSpiderRadarVertices(
    vectors.map((v) => ({ id: v.id, label: v.label, value: v.value })),
    radius,
    center
  );

  // Calculate coordinates for historical baseline values
  const baselineVertices = calculateSpiderRadarVertices(
    vectors.map((v) => ({ id: v.id, label: v.label, value: v.historicalValue })),
    radius,
    center
  );

  // Polygon path strings
  const currentPolygon = currentVertices.map((p) => `${p.x},${p.y}`).join(' ');
  const baselinePolygon = baselineVertices.map((p) => `${p.x},${p.y}`).join(' ');

  // Concentric grid rings (25%, 50%, 75%, 100%)
  const gridRings = [0.25, 0.5, 0.75, 1.0].map((scale) => {
    return vectors.map((_, i) => {
      const angle = (i * 2 * Math.PI) / vectors.length - Math.PI / 2;
      const r = radius * scale;
      return `${Number((center.x + r * Math.cos(angle)).toFixed(2))},${Number(
        (center.y + r * Math.sin(angle)).toFixed(2)
      )}`;
    }).join(' ');
  });

  const selectedVector = vectors.find((v) => v.id === selectedVectorId);

  return (
    <div className="w-full bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-5 reticle-box chamfer-card">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[#1E2830] mb-3 text-xs font-mono">
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-[#00D9FF]" />
          <span className="text-[#8EA7B5] uppercase tracking-wider">
            COGNITIVE KNOWLEDGE TOPOLOGY
          </span>
        </div>
        <span className="text-[10px] text-[#4D6270] uppercase">
          POLYGON RADIAL // 6-AXIS
        </span>
      </div>

      {/* Spider SVG & Data Overlay */}
      <div className="relative flex flex-col items-center justify-center">
        <div className="relative w-[280px] h-[280px] sm:w-[320px] sm:h-[320px]">
          <svg
            viewBox={`0 0 ${size} ${size}`}
            className="w-full h-full select-none"
            aria-label="Cognitive Knowledge Radar"
          >
            {/* Concentric Guide Polygons */}
            {gridRings.map((points, idx) => (
              <polygon
                key={`grid-ring-${idx}`}
                points={points}
                fill="none"
                stroke="#1E2830"
                strokeWidth="1"
                strokeDasharray={idx === 3 ? 'none' : '2 3'}
              />
            ))}

            {/* Radial Spoke Axes */}
            {vectors.map((_, i) => {
              const angle = (i * 2 * Math.PI) / vectors.length - Math.PI / 2;
              const x2 = center.x + radius * Math.cos(angle);
              const y2 = center.y + radius * Math.sin(angle);
              return (
                <line
                  key={`spoke-${i}`}
                  x1={center.x}
                  y1={center.y}
                  x2={x2}
                  y2={y2}
                  stroke="#263844"
                  strokeWidth="1"
                />
              );
            })}

            {/* Historical Baseline Polygon (Dashed Ghost) */}
            <polygon
              points={baselinePolygon}
              fill="rgba(38, 56, 68, 0.15)"
              stroke="#4D6270"
              strokeWidth="1"
              strokeDasharray="3 3"
            />

            {/* Active Current Knowledge Polygon */}
            <polygon
              points={currentPolygon}
              fill="rgba(0, 217, 255, 0.18)"
              stroke="#00D9FF"
              strokeWidth="1.8"
              className="transition-all duration-500 ease-out"
            />

            {/* Vertex Nodes */}
            {currentVertices.map((pt) => {
              const isSelected = pt.id === selectedVectorId;
              const isHovered = hoveredPoint?.id === pt.id;
              const vectorData = vectors.find((v) => v.id === pt.id);
              const isDivergent = vectorData?.status === 'divergent';

              return (
                <g key={`vertex-${pt.id}`}>
                  {/* Interactive Target Circle */}
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={isSelected || isHovered ? 6 : 4}
                    fill={isDivergent ? '#D7A65A' : '#00D9FF'}
                    stroke="#090B0D"
                    strokeWidth="1.5"
                    className="cursor-pointer transition-all duration-200"
                    onMouseEnter={() => setHoveredPoint(pt)}
                    onMouseLeave={() => setHoveredPoint(null)}
                    onClick={() => onSelectVector(pt.id)}
                  />

                  {/* Pulsing ring for selected node */}
                  {isSelected && (
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r="9"
                      fill="none"
                      stroke="#00D9FF"
                      strokeWidth="1"
                      className="animate-ping"
                      style={{ transformOrigin: `${pt.x}px ${pt.y}px` }}
                    />
                  )}
                </g>
              );
            })}

            {/* Vertex Monospace Text Labels */}
            {currentVertices.map((pt, i) => {
              const angle = (i * 2 * Math.PI) / vectors.length - Math.PI / 2;
              const labelDist = radius + 22;
              const lx = center.x + labelDist * Math.cos(angle);
              const ly = center.y + labelDist * Math.sin(angle);
              const isSelected = pt.id === selectedVectorId;

              return (
                <text
                  key={`lbl-${pt.id}`}
                  x={lx}
                  y={ly + 3}
                  textAnchor="middle"
                  fill={isSelected ? '#00D9FF' : '#8EA7B5'}
                  fontSize="8.5"
                  fontFamily="JetBrains Mono"
                  letterSpacing="0.08em"
                  className="cursor-pointer select-none uppercase hover:fill-[#E6F7FF] transition-colors"
                  onClick={() => onSelectVector(pt.id)}
                >
                  {pt.label}
                </text>
              );
            })}
          </svg>
        </div>

        {/* Selected Dimension Telemetry Card */}
        {selectedVector && (
          <div className="w-full mt-2 bg-[#090B0D] border border-[#263844] p-3 text-xs font-mono">
            <div className="flex items-center justify-between">
              <span className="text-[#00D9FF] font-bold tracking-wider uppercase">
                {selectedVector.label}
              </span>
              <span
                className={`text-[10px] px-1.5 py-0.5 border ${
                  selectedVector.status === 'nominal'
                    ? 'border-[#00D9FF]/40 text-[#00D9FF] bg-[#00D9FF]/10'
                    : 'border-[#D7A65A]/40 text-[#D7A65A] bg-[#D7A65A]/10'
                }`}
              >
                {selectedVector.status.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 mt-2 pt-2 border-t border-[#1E2830] text-[11px] tabular-nums">
              <div>
                <span className="text-[9px] text-[#4D6270] block">CURRENT</span>
                <span className="font-bold text-[#E6F7FF]">{selectedVector.value}%</span>
              </div>
              <div>
                <span className="text-[9px] text-[#4D6270] block">VELOCITY</span>
                <span
                  className={
                    selectedVector.velocity >= 0
                      ? 'text-[#00D9FF] font-semibold'
                      : 'text-[#D7A65A] font-semibold'
                  }
                >
                  {selectedVector.velocity >= 0 ? `+${selectedVector.velocity}` : selectedVector.velocity}%/c
                </span>
              </div>
              <div>
                <span className="text-[9px] text-[#4D6270] block">DECAY</span>
                <span className="text-[#8EA7B5]">-{selectedVector.decayRate}%/h</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
