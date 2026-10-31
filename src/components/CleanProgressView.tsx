import React from 'react';
import { CheckCircle2, Clock, Calendar, ShieldCheck } from 'lucide-react';

interface CleanProgressViewProps {
  masteries: Array<{
    concept_id: string;
    concept_name: string;
    p_mastery: number;
    leitner_box: number;
    assessment_state: 'UNASSESSED' | 'IN_PROGRESS' | 'ASSESSED';
    is_due_for_review: boolean;
    formal_attempt_count: number;
  }>;
}

export const CleanProgressView: React.FC<CleanProgressViewProps> = ({ masteries }) => {
  const assessed = masteries.filter((m) => m.assessment_state === 'ASSESSED');
  const inProgress = masteries.filter((m) => m.assessment_state === 'IN_PROGRESS');
  const unassessed = masteries.filter((m) => m.assessment_state === 'UNASSESSED');
  const dueReviews = masteries.filter((m) => m.is_due_for_review);

  return (
    <div className="w-full max-w-5xl mx-auto py-8 px-4 sm:px-6 space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-3.5 bg-[#0B0E11]/90 border border-[#1A2228] flex flex-col gap-1">
          <span className="text-[#6A8190] uppercase tracking-wider text-[10px]">Assessed Concepts</span>
          <span className="text-xl font-bold text-[#00D9FF]">{assessed.length}</span>
        </div>
        <div className="p-3.5 bg-[#0B0E11]/90 border border-[#1A2228] flex flex-col gap-1">
          <span className="text-[#6A8190] uppercase tracking-wider text-[10px]">In Progress</span>
          <span className="text-xl font-bold text-[#F59E0B]">{inProgress.length}</span>
        </div>
        <div className="p-3.5 bg-[#0B0E11]/90 border border-[#1A2228] flex flex-col gap-1">
          <span className="text-[#6A8190] uppercase tracking-wider text-[10px]">Unassessed</span>
          <span className="text-xl font-bold text-[#7F95A3]">{unassessed.length}</span>
        </div>
        <div className="p-3.5 bg-[#0B0E11]/90 border border-[#1A2228] flex flex-col gap-1">
          <span className="text-[#6A8190] uppercase tracking-wider text-[10px]">Due Revisions</span>
          <span className="text-xl font-bold text-[#38BDF8]">{dueReviews.length}</span>
        </div>
      </div>

      {/* Assessed & Evidence-Based Concepts */}
      <div className="bg-[#0B0E11]/90 border border-[#1A2228] p-4 space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-[#1A2228] text-xs font-mono">
          <div className="flex items-center gap-2 text-[#E6F7FF]">
            <ShieldCheck className="w-4 h-4 text-[#00D9FF]" />
            <span className="uppercase tracking-wider font-semibold">Assessed Knowledge State (BKT Evidence)</span>
          </div>
          <span className="text-[10px] text-[#4A5E6D]">NO FABRICATED METRICS</span>
        </div>

        {assessed.length === 0 && inProgress.length === 0 ? (
          <p className="text-xs text-[#6A8190] font-mono py-4 text-center">
            No formal attempts recorded yet. Begin practice in Practice Mode to calibrate your mastery.
          </p>
        ) : (
          <div className="divide-y divide-[#141A20]">
            {[...assessed, ...inProgress].map((m) => (
              <div key={m.concept_id} className="py-2.5 flex items-center justify-between text-xs">
                <div>
                  <p className="font-sans text-[#F0F6FC]">{m.concept_name}</p>
                  <span className="font-mono text-[10px] text-[#6A8190]">
                    Status: {m.assessment_state} • Attempts: {m.formal_attempt_count}
                  </span>
                </div>
                <div className="flex items-center gap-4 font-mono">
                  <span className="text-[11px] text-[#38BDF8]">Box {m.leitner_box}</span>
                  <span className="text-sm font-semibold text-[#00D9FF]">
                    {Math.round(m.p_mastery * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Unassessed Concepts Section */}
      {unassessed.length > 0 && (
        <div className="bg-[#0B0E11]/90 border border-[#1A2228] p-4 space-y-2">
          <div className="pb-2 border-b border-[#1A2228] text-xs font-mono text-[#8EA7B5] flex items-center justify-between">
            <span className="uppercase tracking-wider font-semibold">Unassessed Concepts</span>
            <span className="text-[10px] text-[#4A5E6D]">NEVER REPRESENTED AS ZERO</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
            {unassessed.map((u) => (
              <div key={u.concept_id} className="p-2.5 bg-[#080B0D] border border-[#161D22] text-xs font-sans text-[#7F95A3]">
                {u.concept_name}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

