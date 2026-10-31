import React from 'react';
import { ModuleTrack, TelemetryLog } from '../types/hud';
import { Terminal, Shield, AlertOctagon, CheckCircle2, ChevronRight } from 'lucide-react';

interface SystemStreamWingProps {
  modules: ModuleTrack[];
  activeModuleId: string;
  onSelectModule: (id: string) => void;
  logs: TelemetryLog[];
}

export const SystemStreamWing: React.FC<SystemStreamWingProps> = ({
  modules,
  activeModuleId,
  onSelectModule,
  logs,
}) => {
  return (
    <div className="w-full flex flex-col gap-4">
      {/* Module Tracks Panel */}
      <div className="w-full bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 reticle-box chamfer-card">
        {/* Header */}
        <div className="flex items-center justify-between pb-2.5 border-b border-[#1E2830] mb-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <Shield className="w-3.5 h-3.5 text-[#00D9FF]" />
            <span className="text-[#8EA7B5] uppercase tracking-wider">
              CURRICULUM SYLLABUS TRACKS
            </span>
          </div>
          <span className="text-[10px] text-[#4D6270] uppercase">
            CH: 4 ACTIVE
          </span>
        </div>

        {/* Modules List */}
        <div className="space-y-1.5 font-mono">
          {modules.map((mod, idx) => {
            const isActive = mod.id === activeModuleId;
            const isReview = mod.status === 'review_required';

            return (
              <button
                key={mod.id}
                onClick={() => onSelectModule(mod.id)}
                className={`w-full group text-left px-3 py-2.5 border transition-all relative overflow-hidden flex flex-col gap-1 ${
                  isActive
                    ? 'bg-[#171D22] border-[#00D9FF] shadow-[inset_0_0_12px_rgba(0,217,255,0.12)]'
                    : 'bg-[#090B0D]/80 border-[#1E2830] hover:border-[#263844]'
                }`}
                style={{
                  background: isActive
                    ? undefined
                    : undefined,
                }}
              >
                {/* Active indicator bar on left */}
                {isActive && (
                  <span className="absolute top-0 left-0 w-1 h-full bg-[#00D9FF] shadow-[0_0_8px_#00D9FF]" />
                )}

                {/* Top Row: Channel Label + Status Pip */}
                <div className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-2">
                    <span className="text-[#4D6270] text-[10px] tabular-nums">
                      L{String(idx + 1).padStart(2, '0')}
                    </span>
                    <span
                      className={`text-xs font-semibold tracking-wider ${
                        isActive ? 'text-[#00D9FF]' : 'text-[#E6F7FF] group-hover:text-[#00D9FF]'
                      }`}
                    >
                      {mod.code}
                    </span>
                  </div>

                  {/* Diagnostic Status Chip */}
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`w-1.5 h-1.5 rounded-none ${
                        isReview ? 'bg-[#D7A65A] shadow-[0_0_4px_#D7A65A]' : 'bg-[#00D9FF] shadow-[0_0_4px_#00D9FF]'
                      }`}
                    />
                    <span
                      className={`text-[9px] uppercase tracking-wider ${
                        isReview ? 'text-[#D7A65A]' : 'text-[#8EA7B5]'
                      }`}
                    >
                      {isReview ? 'REVIEW' : 'NOMINAL'}
                    </span>
                  </div>
                </div>

                {/* Module Title */}
                <div className="text-xs font-sans text-[#BBC9CE] font-medium line-clamp-1 group-hover:text-white transition-colors">
                  {mod.title}
                </div>

                {/* Mastery & Retention Metrics Bar */}
                <div className="flex items-center justify-between text-[10px] text-[#4D6270] pt-1 border-t border-[#1E2830]/60 mt-0.5 tabular-nums">
                  <span>MASTERY: <strong className="text-[#E6F7FF]">{mod.mastery}%</strong></span>
                  <span>RETENTION: <strong className="text-[#8EA7B5]">{mod.retention}%</strong></span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Real-time Telemetry Stream / Console Logs */}
      <div className="w-full bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 reticle-box chamfer-card">
        {/* Header */}
        <div className="flex items-center justify-between pb-2.5 border-b border-[#1E2830] mb-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <Terminal className="w-3.5 h-3.5 text-[#00D9FF]" />
            <span className="text-[#8EA7B5] uppercase tracking-wider">
              TELEMETRY SENSOR LOGS
            </span>
          </div>
          <span className="text-[10px] text-[#00D9FF] tabular-nums">
            REC // STREAM
          </span>
        </div>

        {/* Log Entries with Line Numbers & Gradient Hover */}
        <div className="space-y-1 font-mono text-[11px] max-h-[220px] overflow-y-auto pr-1">
          {logs.map((log) => {
            const isWarning = log.type === 'warning';
            const isCritical = log.type === 'critical';

            return (
              <div
                key={log.id}
                className="group p-1.5 border-b border-dashed border-[#1E2830] transition-colors hover:bg-gradient-to-r hover:from-[rgba(0,217,255,0.08)] hover:to-transparent"
              >
                <div className="flex items-center gap-2 text-[10px] text-[#4D6270] mb-0.5 tabular-nums">
                  <span className="text-[#4D6270] group-hover:text-[#00D9FF] transition-colors">
                    #{log.line}
                  </span>
                  <span>{log.timestamp}</span>
                  <span className="text-[#8EA7B5] font-semibold">{log.channel}</span>
                </div>
                <div
                  className={`text-[11px] leading-relaxed break-words ${
                    isWarning
                      ? 'text-[#D7A65A]'
                      : isCritical
                      ? 'text-[#FFB4AB]'
                      : 'text-[#BBC9CE]'
                  }`}
                >
                  {log.message}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
