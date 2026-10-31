import React, { useState } from 'react';
import { parseTerminalCommand } from '../lib/tutor-engine';
import { Terminal, Send, HelpCircle } from 'lucide-react';

interface TerminalBarProps {
  onExecuteCommand: (cmd: string, result: ReturnType<typeof parseTerminalCommand>) => void;
  recentOutput?: string;
}

export const TerminalBar: React.FC<TerminalBarProps> = ({
  onExecuteCommand,
  recentOutput,
}) => {
  const [inputVal, setInputVal] = useState<string>('');
  const [isFocused, setIsFocused] = useState<boolean>(false);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!inputVal.trim()) return;

    const res = parseTerminalCommand(inputVal);
    onExecuteCommand(inputVal, res);
    setInputVal('');
  };

  const handleQuickCommand = (cmd: string) => {
    const res = parseTerminalCommand(cmd);
    onExecuteCommand(cmd, res);
  };

  return (
    <div className="w-full bg-[#0A0D10] border border-[#263844] p-3 reticle-box font-mono">
      {/* Top Header with Quick Shortcuts */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2 mb-2 border-b border-[#1E2830] text-[11px]">
        <div className="flex items-center gap-2 text-[#00D9FF]">
          <Terminal className="w-3.5 h-3.5" />
          <span className="font-semibold uppercase tracking-wider">
            TACTICAL COMMAND CONSOLE
          </span>
        </div>

        {/* Quick Shortcut Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] text-[#4D6270]">QUICK DIRECTIVES:</span>
          <button
            type="button"
            onClick={() => handleQuickCommand('calibrate 1.45')}
            className="px-1.5 py-0.5 bg-[#111519] border border-[#1E2830] text-[10px] text-[#8EA7B5] hover:border-[#00D9FF] hover:text-[#00D9FF] transition-colors"
          >
            calibrate 1.45
          </button>
          <button
            type="button"
            onClick={() => handleQuickCommand('diagnose MOD: CYBER_PHYS_01')}
            className="px-1.5 py-0.5 bg-[#111519] border border-[#1E2830] text-[10px] text-[#8EA7B5] hover:border-[#00D9FF] hover:text-[#00D9FF] transition-colors"
          >
            diagnose mod
          </button>
          <button
            type="button"
            onClick={() => handleQuickCommand('help')}
            className="px-1.5 py-0.5 bg-[#111519] border border-[#1E2830] text-[10px] text-[#8EA7B5] hover:border-[#00D9FF] hover:text-[#00D9FF] transition-colors"
          >
            help
          </button>
          <button
            type="button"
            onClick={() => handleQuickCommand('reset')}
            className="px-1.5 py-0.5 bg-[#111519] border border-[#1E2830] text-[10px] text-[#8EA7B5] hover:border-[#D7A65A] hover:text-[#D7A65A] transition-colors"
          >
            reset
          </button>
        </div>
      </div>

      {/* Input Form with Crisp Bottom Border and Blinking Cursor */}
      <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
        <span className="text-[#00D9FF] font-bold text-xs select-none">&gt;_</span>

        <div className="relative flex-1">
          <input
            type="text"
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="Type directive (e.g. 'calibrate 1.45', 'diagnose mod_1', 'help')..."
            className={`w-full bg-transparent text-xs text-[#E6F7FF] placeholder-[#4D6270] focus:outline-none py-1.5 pr-6 ${
              isFocused ? 'border-b border-[#00D9FF]' : 'border-b border-[#263844]'
            }`}
          />
          {/* Blinking block cursor when empty and focused */}
          {isFocused && inputVal === '' && (
            <span className="absolute left-0 top-1.5 text-[#00D9FF] cursor-blink select-none pointer-events-none">
              ▋
            </span>
          )}
        </div>

        <button
          type="submit"
          aria-label="Submit tactical directive"
          className="px-3 py-1 bg-[#111519] border border-[#00D9FF] text-[#00D9FF] text-xs font-semibold hover:bg-[#00D9FF] hover:text-[#090B0D] transition-colors flex items-center gap-1"
        >
          <Send className="w-3 h-3" />
          <span className="hidden sm:inline uppercase">Execute</span>
        </button>
      </form>

      {/* Recent Feedback Feed */}
      {recentOutput && (
        <div className="mt-2 pt-2 border-t border-[#1E2830] text-[11px] text-[#00D9FF] flex items-start gap-1.5">
          <span className="text-[#4D6270] select-none">[SYS]:</span>
          <span className="text-[#BBC9CE] break-words">{recentOutput}</span>
        </div>
      )}
    </div>
  );
};
