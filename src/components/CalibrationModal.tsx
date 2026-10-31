import React, { useState } from 'react';
import { Crosshair, Check, RefreshCw, X, ShieldCheck } from 'lucide-react';

interface CalibrationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCalibrationComplete: () => void;
}

export const CalibrationModal: React.FC<CalibrationModalProps> = ({
  isOpen,
  onClose,
  onCalibrationComplete,
}) => {
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<string>('Ready for sweep initialization');
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleStartSweep = () => {
    setIsRunning(true);
    setProgress(15);
    setCurrentStep('Aligning orbital concentric degree reticles (360°)...');

    setTimeout(() => {
      setProgress(45);
      setCurrentStep('Normalizing neural focus drift coordinates...');
    }, 400);

    setTimeout(() => {
      setProgress(75);
      setCurrentStep('Synchronizing Ebbinghaus decay matrix with active syllabus...');
    }, 800);

    setTimeout(() => {
      setProgress(100);
      setCurrentStep('Calibration sweep complete: All parameters in nominal state.');
      setIsRunning(false);
      setIsCompleted(true);
      onCalibrationComplete();
    }, 1200);
  };

  const handleDone = () => {
    setIsCompleted(false);
    setProgress(0);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#090B0D]/85 backdrop-blur-md">
      <div className="relative w-full max-w-lg bg-[#111519] border border-[#00D9FF] p-6 reticle-box chamfer-card shadow-[0_0_24px_rgba(0,217,255,0.25)] font-mono">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[#1E2830] mb-4">
          <div className="flex items-center gap-2">
            <Crosshair className="w-4 h-4 text-[#00D9FF]" />
            <span className="text-xs font-bold text-[#E6F7FF] uppercase tracking-wider">
              SYSTEM SENSOR RE-CALIBRATION
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close modal"
            className="text-[#8EA7B5] hover:text-[#00D9FF] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Diagnostic Scope Viewport */}
        <div className="bg-[#090B0D] border border-[#263844] p-4 text-center my-3 space-y-3">
          <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
            <svg viewBox="0 0 100 100" className="w-full h-full select-none">
              <circle cx="50" cy="50" r="42" fill="none" stroke="#1E2830" strokeWidth="1" />
              <circle
                cx="50"
                cy="50"
                r="36"
                fill="none"
                stroke="#00D9FF"
                strokeWidth="1.5"
                strokeDasharray="6 4"
                className={isRunning ? 'animate-spin' : ''}
                style={{ transformOrigin: '50px 50px' }}
              />
              <circle cx="50" cy="50" r="14" fill="#090B0D" stroke="#00D9FF" strokeWidth="1" />
              <line x1="10" y1="50" x2="90" y2="50" stroke="#263844" strokeWidth="1" />
              <line x1="50" y1="10" x2="50" y2="90" stroke="#263844" strokeWidth="1" />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center text-xs font-bold text-[#00D9FF] tabular-nums">
              {progress}%
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] text-[#4D6270] uppercase tracking-widest block">
              STATUS CHANNEL
            </span>
            <p className="text-xs text-[#BBC9CE] font-sans h-8 flex items-center justify-center">
              {currentStep}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full h-1 bg-[#171D22] border border-[#1E2830] overflow-hidden my-3">
          <div
            className="h-full bg-[#00D9FF] transition-all duration-300 shadow-[0_0_8px_#00D9FF]"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Calibration Checklist */}
        <div className="space-y-2 text-xs text-[#8EA7B5] my-4 border-t border-[#1E2830] pt-3">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 ${progress >= 30 ? 'bg-[#00D9FF]' : 'bg-[#4D6270]'}`} />
              <span>Concentric Arc Geometry</span>
            </span>
            <span className="tabular-nums text-[#00D9FF] text-[10px]">
              {progress >= 30 ? 'CALIBRATED' : 'WAITING'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 ${progress >= 60 ? 'bg-[#00D9FF]' : 'bg-[#4D6270]'}`} />
              <span>Neural Focus Stability Margin</span>
            </span>
            <span className="tabular-nums text-[#00D9FF] text-[10px]">
              {progress >= 60 ? '0.02 rad' : 'WAITING'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 ${progress === 100 ? 'bg-[#00D9FF]' : 'bg-[#4D6270]'}`} />
              <span>Ebbinghaus Temporal Retention Loop</span>
            </span>
            <span className="tabular-nums text-[#00D9FF] text-[10px]">
              {progress === 100 ? 'SYNCHRONIZED' : 'WAITING'}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          {!isCompleted ? (
            <button
              onClick={handleStartSweep}
              disabled={isRunning}
              className="w-full chamfer-btn py-2.5 bg-[#090B0D] border border-[#00D9FF] text-[#00D9FF] font-mono text-xs font-bold uppercase tracking-wider hud-sweep-btn flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'Executing Sweep...' : 'Initiate Full Calibration'}</span>
            </button>
          ) : (
            <button
              onClick={handleDone}
              className="w-full chamfer-btn py-2.5 bg-[#00D9FF] text-[#090B0D] font-mono text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 shadow-[0_0_12px_rgba(0,217,255,0.6)]"
            >
              <Check className="w-4 h-4 stroke-[2.5]" />
              <span>Apply & Return to Telemetry Hub</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
