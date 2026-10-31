import React, { useState } from 'react';
import { ModuleTrack } from '../types/hud';
import { evaluateStateVectorResponse } from '../lib/tutor-engine';
import { Compass, Lightbulb, Check, AlertTriangle, ArrowRight, Play } from 'lucide-react';

interface SocraticDialogueWingProps {
  module: ModuleTrack;
  onUpdateScore: (scoreDelta: number, isNominal: boolean, logMessage: string) => void;
}

export const SocraticDialogueWing: React.FC<SocraticDialogueWingProps> = ({
  module,
  onUpdateScore,
}) => {
  const prompt = module.problemPrompt;
  const [paramValue, setParamValue] = useState<number>(prompt.currentValue);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [showHints, setShowHints] = useState<boolean>(false);
  const [evaluation, setEvaluation] = useState<{
    tested: boolean;
    isNominal: boolean;
    deviation: number;
    score: number;
    statusMsg: string;
    optionExplanation?: string;
  } | null>(null);

  const handleTestParameter = () => {
    const res = evaluateStateVectorResponse(
      paramValue,
      prompt.nominalTarget,
      prompt.tolerance
    );

    let optionExplanation: string | undefined;
    let finalNominal = res.isNominal;

    if (prompt.options && selectedOptionId) {
      const selected = prompt.options.find((o) => o.id === selectedOptionId);
      if (selected) {
        optionExplanation = selected.explanation;
        if (!selected.isNominal) {
          finalNominal = false;
        }
      }
    }

    setEvaluation({
      tested: true,
      isNominal: finalNominal,
      deviation: res.deviation,
      score: res.score,
      statusMsg: res.statusMsg,
      optionExplanation,
    });

    const scoreDelta = finalNominal ? 2.5 : -1.2;
    const msg = `Diagnostic verification for [${module.code}]: param=${paramValue} ${prompt.parameterUnit} -> ${
      finalNominal ? 'NOMINAL MATCH' : 'DIVERGENT DISPERSION'
    } (Score: ${res.score}%)`;
    onUpdateScore(scoreDelta, finalNominal, msg);
  };

  const handleReset = () => {
    setParamValue(prompt.currentValue);
    setSelectedOptionId(null);
    setEvaluation(null);
  };

  return (
    <div className="w-full bg-[#111519]/80 border border-[#1E2830] backdrop-blur-md p-4 sm:p-5 reticle-box chamfer-card flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[#1E2830] text-xs font-mono">
        <div className="flex items-center gap-2">
          <Compass className="w-3.5 h-3.5 text-[#00D9FF]" />
          <span className="text-[#8EA7B5] uppercase tracking-wider">
            SOCRATIC PROBLEM SCAFFOLDING
          </span>
        </div>
        <span className="text-[10px] text-[#00D9FF] px-1.5 py-0.5 border border-[#005366] bg-[#002833]/40">
          DIAGNOSTIC MODE
        </span>
      </div>

      {/* Narrative Problem Prompt in Manrope */}
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs font-mono text-[#00D9FF]">
          <span>// ACTIVE TASK</span>
          <span className="text-[#4D6270]">·</span>
          <span className="text-[#8EA7B5]">{module.activeConcept}</span>
        </div>

        <h3 className="text-base sm:text-lg font-bold font-sans text-[#E6F7FF] tracking-tight">
          {prompt.title}
        </h3>

        <p className="text-xs sm:text-sm text-[#BBC9CE] font-sans leading-relaxed">
          {prompt.description}
        </p>
      </div>

      {/* Mathematical System Equation Card */}
      <div className="bg-[#090B0D] border border-[#263844] p-3 text-center reticle-box">
        <span className="block font-mono text-[9px] uppercase tracking-widest text-[#4D6270] mb-1">
          SYSTEM GOVERNING DYNAMICS
        </span>
        <code className="font-mono text-sm sm:text-base font-semibold text-[#00D9FF] tracking-wide block">
          {prompt.systemEquation}
        </code>
      </div>

      {/* Interactive Parameter Scrubber */}
      <div className="bg-[#090B0D]/90 border border-[#1E2830] p-3 space-y-2">
        <div className="flex items-center justify-between text-xs font-mono">
          <label htmlFor="param-slider" className="text-[#8EA7B5] font-semibold">
            {prompt.parameterName}
          </label>
          <div className="flex items-baseline gap-1 tabular-nums">
            <span className="text-sm font-bold text-[#E6F7FF]">{paramValue.toFixed(3)}</span>
            <span className="text-[10px] text-[#4D6270]">{prompt.parameterUnit}</span>
          </div>
        </div>

        <div className="relative flex items-center">
          <input
            id="param-slider"
            type="range"
            min={prompt.targetMin}
            max={prompt.targetMax}
            step="0.005"
            value={paramValue}
            onChange={(e) => setParamValue(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-[#171D22] appearance-none cursor-pointer accent-[#00D9FF] border border-[#263844]"
          />
        </div>

        <div className="flex justify-between text-[10px] font-mono text-[#4D6270] tabular-nums">
          <span>MIN: {prompt.targetMin}</span>
          <span className="text-[#00D9FF]">TARGET REGION: ~{prompt.nominalTarget}</span>
          <span>MAX: {prompt.targetMax}</span>
        </div>
      </div>

      {/* Qualitative Scenario Selection (Concentric Radio Nodes) */}
      {prompt.options && (
        <div className="space-y-1.5">
          <span className="font-mono text-[10px] uppercase tracking-wider text-[#8EA7B5] block">
            SELECT ADAPTIVE CONTROL ACTION:
          </span>

          <div className="space-y-1.5">
            {prompt.options.map((opt) => {
              const isSelected = selectedOptionId === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => setSelectedOptionId(opt.id)}
                  className={`w-full text-left p-2.5 border transition-all text-xs font-sans flex items-start gap-2.5 ${
                    isSelected
                      ? 'bg-[#171D22] border-[#00D9FF] text-[#E6F7FF] shadow-[inset_0_0_8px_rgba(0,217,255,0.15)]'
                      : 'bg-[#090B0D] border-[#1E2830] text-[#BBC9CE] hover:border-[#263844]'
                  }`}
                >
                  {/* Concentric Dual-Ring Reticle Radio */}
                  <span className="relative flex items-center justify-center w-4 h-4 shrink-0 mt-0.5 border border-[#263844]">
                    {isSelected && (
                      <span className="w-2 h-2 bg-[#00D9FF] shadow-[0_0_6px_#00D9FF]" />
                    )}
                  </span>
                  <span className="leading-snug">{opt.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Socratic Hints Accordion */}
      <div className="border border-[#1E2830] bg-[#090B0D]/60 p-2.5">
        <button
          onClick={() => setShowHints(!showHints)}
          className="w-full flex items-center justify-between text-xs font-mono text-[#8EA7B5] hover:text-[#E6F7FF]"
        >
          <span className="flex items-center gap-1.5">
            <Lightbulb className="w-3.5 h-3.5 text-[#D7A65A]" />
            <span>SOCRATIC REASONING HINTS ({prompt.socraticHints.length})</span>
          </span>
          <span className="text-[10px] text-[#4D6270]">
            {showHints ? 'COLLAPSE [-]' : 'EXPAND [+]'}
          </span>
        </button>

        {showHints && (
          <ul className="mt-2.5 space-y-1.5 text-xs text-[#8EA7B5] font-sans pl-2 border-l border-[#263844]">
            {prompt.socraticHints.map((hint, idx) => (
              <li key={idx} className="leading-relaxed">
                <span className="font-mono text-[#00D9FF] mr-1">0{idx + 1}.</span>
                {hint}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Action Buttons: Run Test + Reset */}
      <div className="flex items-center gap-3 pt-2">
        <button
          onClick={handleTestParameter}
          className="flex-1 chamfer-btn py-2.5 px-4 bg-[#090B0D] border border-[#00D9FF] text-[#00D9FF] font-mono text-xs font-bold uppercase tracking-wider hud-sweep-btn flex items-center justify-center gap-2 shadow-[0_0_12px_rgba(0,217,255,0.25)]"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>Execute Diagnostic Test</span>
        </button>

        <button
          onClick={handleReset}
          className="chamfer-btn py-2.5 px-3 bg-[#090B0D] border border-[#263844] text-[#8EA7B5] hover:border-[#00D9FF] hover:text-[#E6F7FF] font-mono text-xs uppercase tracking-wider"
        >
          Reset
        </button>
      </div>

      {/* Evaluation Feedback Banner */}
      {evaluation && evaluation.tested && (
        <div
          className={`p-3 border font-mono text-xs ${
            evaluation.isNominal
              ? 'bg-[#002833]/50 border-[#00D9FF] text-[#E6F7FF] hud-glow-cyan'
              : 'bg-[#2b1f0e]/50 border-[#D7A65A] text-[#E6F7FF] hud-glow-amber'
          }`}
        >
          <div className="flex items-center gap-2 font-bold mb-1">
            {evaluation.isNominal ? (
              <Check className="w-4 h-4 text-[#00D9FF]" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-[#D7A65A]" />
            )}
            <span
              className={evaluation.isNominal ? 'text-[#00D9FF]' : 'text-[#D7A65A]'}
            >
              {evaluation.statusMsg}
            </span>
          </div>

          <div className="text-[11px] space-y-1 font-sans text-[#BBC9CE]">
            <p className="font-mono text-[10px] text-[#8EA7B5]">
              DEVIATION: <strong className="tabular-nums text-[#E6F7FF]">{evaluation.deviation}</strong> · FIDELITY: <strong className="tabular-nums text-[#00D9FF]">{evaluation.score}%</strong>
            </p>
            {evaluation.optionExplanation && (
              <p className="mt-1 pt-1 border-t border-[#1E2830]">
                {evaluation.optionExplanation}
              </p>
            )}
            <p className="text-[11px] text-[#8EA7B5]">
              {prompt.contextExplanation}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
