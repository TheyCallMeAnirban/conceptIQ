import React, { useState, useMemo } from 'react';
import { simulateCyberPhysicalStep } from '../lib/tutor-engine';
import { Sliders, Play, RefreshCw, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';

interface SimulationLabProps {
  onLogTelemetry?: (msg: string) => void;
}

export const SimulationLab: React.FC<SimulationLabProps> = ({ onLogTelemetry }) => {
  const [kp, setKp] = useState<number>(1.45);
  const [ki, setKi] = useState<number>(0.20);
  const [kd, setKd] = useState<number>(0.45);
  const [disturbance, setDisturbance] = useState<number>(0);

  // Compute simulation steps
  const simulationData = useMemo(() => {
    return simulateCyberPhysicalStep(kp, ki, kd, 50);
  }, [kp, ki, kd]);

  // Telemetry metrics derived from response
  const maxVal = Math.max(...simulationData.map((d) => d.y));
  const finalVal = simulationData[simulationData.length - 1].y;
  const overshootPercent = Math.max(0, ((maxVal - 1.0) / 1.0) * 100);
  const steadyStateError = Math.abs(1.0 - finalVal);
  const isStable = overshootPercent < 35 && steadyStateError < 0.12;

  // SVG dimensions for chart
  const svgWidth = 680;
  const svgHeight = 260;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 20;
  const padBottom = 35;
  const plotW = svgWidth - padLeft - padRight;
  const plotH = svgHeight - padTop - padBottom;

  // Scale functions: time t: 0 -> 2.5s; y: -0.2 -> 1.8
  const minY = -0.2;
  const maxY = 2.0;

  const getX = (t: number) => padLeft + (t / 2.5) * plotW;
  const getY = (y: number) => padTop + plotH - ((y - minY) / (maxY - minY)) * plotH;

  const responsePoints = simulationData
    .map((d) => `${getX(d.t).toFixed(1)},${getY(d.y).toFixed(1)}`)
    .join(' ');

  const setpointY = getY(1.0);

  const applyPreset = (preset: 'optimal' | 'underdamped' | 'overdamped' | 'oscillatory') => {
    let pKp = 1.45;
    let pKi = 0.20;
    let pKd = 0.45;
    let desc = 'Optimal Critical Damping';

    if (preset === 'underdamped') {
      pKp = 3.2;
      pKi = 0.05;
      pKd = 0.1;
      desc = 'Underdamped Fast Rise with High Overshoot';
    } else if (preset === 'overdamped') {
      pKp = 0.6;
      pKi = 0.1;
      pKd = 1.2;
      desc = 'Overdamped Sluggish Step Settling';
    } else if (preset === 'oscillatory') {
      pKp = 4.5;
      pKi = 1.8;
      pKd = 0.05;
      desc = 'Sustained Hunting Resonant Chatter';
    }

    setKp(pKp);
    setKi(pKi);
    setKd(pKd);
    onLogTelemetry?.(`Simulation preset applied: [${desc}] (Kp=${pKp}, Ki=${pKi}, Kd=${pKd})`);
  };

  return (
    <div className="w-full space-y-6">
      {/* Viewport Header */}
      <div className="bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 reticle-box chamfer-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-[#00D9FF]">
              <span>// VIRTUAL WORKBENCH</span>
              <span className="text-[#4D6270]">·</span>
              <span className="text-[#8EA7B5]">CLOSED-LOOP PID STEP RESPONSE</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold font-sans text-[#E6F7FF]">
              Cyber-Physical Actuator Plant Simulator
            </h2>
          </div>

          {/* Quick Presets */}
          <div className="flex items-center gap-2 flex-wrap font-mono text-xs">
            <span className="text-[10px] text-[#4D6270] uppercase">PRESETS:</span>
            <button
              onClick={() => applyPreset('optimal')}
              className="px-2 py-1 bg-[#090B0D] border border-[#00D9FF] text-[#00D9FF] text-[10px] uppercase hover:bg-[#00D9FF] hover:text-[#090B0D] transition-colors"
            >
              Critical
            </button>
            <button
              onClick={() => applyPreset('underdamped')}
              className="px-2 py-1 bg-[#090B0D] border border-[#1E2830] text-[#8EA7B5] text-[10px] uppercase hover:border-[#D7A65A] hover:text-[#D7A65A] transition-colors"
            >
              Underdamped
            </button>
            <button
              onClick={() => applyPreset('overdamped')}
              className="px-2 py-1 bg-[#090B0D] border border-[#1E2830] text-[#8EA7B5] text-[10px] uppercase hover:border-[#8EA7B5] hover:text-white transition-colors"
            >
              Overdamped
            </button>
            <button
              onClick={() => applyPreset('oscillatory')}
              className="px-2 py-1 bg-[#090B0D] border border-[#93000A] text-[#FFB4AB] text-[10px] uppercase hover:bg-[#93000A] transition-colors"
            >
              Oscillatory
            </button>
          </div>
        </div>
      </div>

      {/* Main 2-Column Split: Dynamic Chart & Control Rails */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Step Response Scope (8 cols) */}
        <div className="lg:col-span-8 bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-5 reticle-box chamfer-card flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-[#1E2830] mb-4 text-xs font-mono">
              <span className="text-[#8EA7B5] uppercase">
                TIME-DOMAIN STEP RESPONSE // y(t) vs r(t)
              </span>
              <div className="flex items-center gap-3 text-[10px]">
                <span className="flex items-center gap-1 text-[#00D9FF]">
                  <span className="w-2 h-0.5 bg-[#00D9FF]" /> PLANT RESPONSE y(t)
                </span>
                <span className="flex items-center gap-1 text-[#D7A65A]">
                  <span className="w-2 h-0.5 bg-[#D7A65A] border-dashed" /> SETPOINT r(t)=1.0
                </span>
              </div>
            </div>

            {/* Live SVG Waveform Canvas */}
            <div className="relative w-full overflow-x-auto bg-[#090B0D] border border-[#263844] p-2">
              <svg
                viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                className="w-full h-auto min-w-[500px]"
                aria-label="PID Step Response Plot"
              >
                {/* Grid Lines */}
                {[0, 0.5, 1.0, 1.5, 2.0].map((val) => {
                  const yPos = getY(val);
                  return (
                    <g key={`y-grid-${val}`}>
                      <line
                        x1={padLeft}
                        y1={yPos}
                        x2={svgWidth - padRight}
                        y2={yPos}
                        stroke="#1E2830"
                        strokeWidth="1"
                        strokeDasharray="2 3"
                      />
                      <text
                        x={padLeft - 8}
                        y={yPos + 3}
                        textAnchor="end"
                        fill="#4D6270"
                        fontSize="9"
                        fontFamily="JetBrains Mono"
                      >
                        {val.toFixed(1)}
                      </text>
                    </g>
                  );
                })}

                {/* Time Grid Lines (0s to 2.5s) */}
                {[0.5, 1.0, 1.5, 2.0, 2.5].map((t) => {
                  const xPos = getX(t);
                  return (
                    <g key={`x-grid-${t}`}>
                      <line
                        x1={xPos}
                        y1={padTop}
                        x2={xPos}
                        y2={svgHeight - padBottom}
                        stroke="#1E2830"
                        strokeWidth="1"
                        strokeDasharray="2 3"
                      />
                      <text
                        x={xPos}
                        y={svgHeight - padBottom + 14}
                        textAnchor="middle"
                        fill="#4D6270"
                        fontSize="9"
                        fontFamily="JetBrains Mono"
                      >
                        {t}s
                      </text>
                    </g>
                  );
                })}

                {/* Target Setpoint Line r(t) = 1.0 */}
                <line
                  x1={padLeft}
                  y1={setpointY}
                  x2={svgWidth - padRight}
                  y2={setpointY}
                  stroke="#D7A65A"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />

                {/* Dynamic Plant Output Waveform y(t) */}
                <polyline
                  fill="none"
                  stroke="#00D9FF"
                  strokeWidth="2.2"
                  points={responsePoints}
                  strokeLinecap="round"
                  className="transition-all duration-300"
                />

                {/* Overshoot Marker */}
                {overshootPercent > 2 && (
                  <circle
                    cx={getX(simulationData.find((d) => d.y === maxVal)?.t || 0)}
                    cy={getY(maxVal)}
                    r="4"
                    fill="#00D9FF"
                    stroke="#090B0D"
                    strokeWidth="1.5"
                  />
                )}
              </svg>
            </div>
          </div>

          {/* Telemetry Readout Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-[#1E2830] font-mono text-xs">
            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">PEAK OVERSHOOT</span>
              <span
                className={`text-base font-bold tabular-nums ${
                  overshootPercent > 25 ? 'text-[#D7A65A]' : 'text-[#00D9FF]'
                }`}
              >
                {overshootPercent.toFixed(1)}%
              </span>
            </div>

            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">STEADY ERROR</span>
              <span className="text-base font-bold text-[#E6F7FF] tabular-nums">
                {steadyStateError.toFixed(4)}
              </span>
            </div>

            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">FINAL VALUE</span>
              <span className="text-base font-bold text-[#E6F7FF] tabular-nums">
                {finalVal.toFixed(3)}
              </span>
            </div>

            <div className="bg-[#090B0D] p-2.5 border border-[#1E2830]">
              <span className="text-[9px] text-[#4D6270] block uppercase">STABILITY STATUS</span>
              <span
                className={`text-xs font-bold uppercase tracking-wider block mt-1 ${
                  isStable ? 'text-[#00D9FF]' : 'text-[#D7A65A]'
                }`}
              >
                {isStable ? 'NOMINAL' : 'MARGINAL'}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Actuator Tuning Parameters & Scaffolding (4 cols) */}
        <div className="lg:col-span-4 bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-5 reticle-box chamfer-card space-y-4">
          <div className="flex items-center justify-between pb-2.5 border-b border-[#1E2830] text-xs font-mono">
            <div className="flex items-center gap-2">
              <Sliders className="w-3.5 h-3.5 text-[#00D9FF]" />
              <span className="text-[#8EA7B5] uppercase">PID TUNING RAILS</span>
            </div>
            <span className="text-[10px] text-[#4D6270]">CLOSED LOOP</span>
          </div>

          {/* Kp Slider */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <label htmlFor="sim-kp" className="text-[#8EA7B5]">Proportional (Kp)</label>
              <span className="text-[#00D9FF] font-bold tabular-nums">{kp.toFixed(2)}</span>
            </div>
            <input
              id="sim-kp"
              type="range"
              min="0.1"
              max="5.0"
              step="0.05"
              value={kp}
              onChange={(e) => setKp(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-[#171D22] appearance-none cursor-pointer accent-[#00D9FF] border border-[#263844]"
            />
            <span className="text-[9px] text-[#4D6270] block">Controls speed of initial transient rise</span>
          </div>

          {/* Ki Slider */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <label htmlFor="sim-ki" className="text-[#8EA7B5]">Integral (Ki)</label>
              <span className="text-[#00D9FF] font-bold tabular-nums">{ki.toFixed(2)}</span>
            </div>
            <input
              id="sim-ki"
              type="range"
              min="0.0"
              max="2.0"
              step="0.02"
              value={ki}
              onChange={(e) => setKi(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-[#171D22] appearance-none cursor-pointer accent-[#00D9FF] border border-[#263844]"
            />
            <span className="text-[9px] text-[#4D6270] block">Eliminates persistent steady-state offset</span>
          </div>

          {/* Kd Slider */}
          <div className="space-y-1.5 font-mono text-xs">
            <div className="flex justify-between">
              <label htmlFor="sim-kd" className="text-[#8EA7B5]">Derivative (Kd)</label>
              <span className="text-[#00D9FF] font-bold tabular-nums">{kd.toFixed(2)}</span>
            </div>
            <input
              id="sim-kd"
              type="range"
              min="0.0"
              max="2.5"
              step="0.05"
              value={kd}
              onChange={(e) => setKd(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-[#171D22] appearance-none cursor-pointer accent-[#00D9FF] border border-[#263844]"
            />
            <span className="text-[9px] text-[#4D6270] block">Damps oscillations and prevents runaway overshoot</span>
          </div>

          {/* Socratic Analytical Breakdown */}
          <div className="p-3 bg-[#090B0D] border border-[#263844] space-y-2 text-xs">
            <span className="font-mono text-[10px] text-[#00D9FF] uppercase tracking-wider block">
              ANALYSIS OF CURRENT CONFIGURATION
            </span>
            <p className="text-[#BBC9CE] font-sans leading-relaxed text-[11px]">
              {kp > 3.0 && kd < 0.3
                ? 'High proportional gain with inadequate damping creates severe resonant ringing. Increase Kd to restore phase margin.'
                : ki > 1.2
                ? 'Excessive integral accumulation is introducing phase lag, destabilizing low-frequency modes.'
                : 'System response demonstrates stable convergence towards the target setpoint.'}
            </p>
          </div>

          {/* Reset Action */}
          <button
            onClick={() => applyPreset('optimal')}
            className="w-full chamfer-btn py-2 px-3 bg-[#090B0D] border border-[#00D9FF] text-[#00D9FF] font-mono text-xs font-semibold uppercase tracking-wider hud-sweep-btn flex items-center justify-center gap-2"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset to Calibrated Base (1.45, 0.20, 0.45)</span>
          </button>
        </div>
      </div>
    </div>
  );
};
