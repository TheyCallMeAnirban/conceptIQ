import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { Copy, Check, Terminal } from 'lucide-react';

interface EducationalRendererProps {
  content: string;
  isStreaming?: boolean;
}

export const EducationalRenderer: React.FC<EducationalRendererProps> = ({
  content,
  isStreaming = false,
}) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const handleCopyCode = (codeText: string, idx: number) => {
    navigator.clipboard.writeText(codeText);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="educational-content text-[#CBE7F5] font-sans leading-relaxed space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h1: ({ node, ...props }) => (
            <h1 className="text-base sm:text-lg font-bold text-[#00D9FF] font-mono tracking-wide pt-2 pb-1 border-b border-[#1A2530]" {...props} />
          ),
          h2: ({ node, ...props }) => (
            <h2 className="text-sm sm:text-base font-semibold text-[#E6F7FF] font-mono tracking-wide pt-3 pb-1" {...props} />
          ),
          h3: ({ node, ...props }) => (
            <h3 className="text-xs sm:text-sm font-semibold text-[#38BDF8] font-mono tracking-wide pt-2" {...props} />
          ),
          p: ({ node, ...props }) => (
            <p className="text-xs sm:text-sm leading-relaxed text-[#D0E6F5] my-2" {...props} />
          ),
          ul: ({ node, ...props }) => (
            <ul className="list-disc list-inside space-y-1 text-xs sm:text-sm text-[#C4DDF0] my-2 pl-2" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal list-inside space-y-1 text-xs sm:text-sm text-[#C4DDF0] my-2 pl-2" {...props} />
          ),
          blockquote: ({ node, ...props }) => (
            <blockquote className="border-l-2 border-[#00D9FF] pl-3 py-1 my-2 bg-[#090D11] text-xs sm:text-sm text-[#8EA7B5] italic font-sans" {...props} />
          ),
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-3 border border-[#1E2830]">
              <table className="min-w-full divide-y divide-[#1E2830] text-xs font-mono" {...props} />
            </div>
          ),
          thead: ({ node, ...props }) => <thead className="bg-[#11171D] text-[#00D9FF]" {...props} />,
          th: ({ node, ...props }) => <th className="px-3 py-2 text-left font-semibold uppercase tracking-wider" {...props} />,
          td: ({ node, ...props }) => <td className="px-3 py-2 border-t border-[#161F26] text-[#CBE7F5]" {...props} />,
          code: ({ node, inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');

            if (inline) {
              return (
                <code className="px-1.5 py-0.5 mx-0.5 rounded-none bg-[#111820] border border-[#223340] text-[#00D9FF] font-mono text-[11px]" {...props}>
                  {children}
                </code>
              );
            }

            return (
              <div className="my-3 border border-[#1E2C36] bg-[#070A0D] overflow-hidden">
                <div className="flex items-center justify-between px-3 py-1.5 bg-[#0F161C] border-b border-[#1A2530] text-[10px] font-mono text-[#8EA7B5]">
                  <div className="flex items-center gap-1.5">
                    <Terminal className="w-3 h-3 text-[#00D9FF]" />
                    <span className="uppercase tracking-wider font-semibold">
                      {match ? match[1] : 'CODE'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleCopyCode(codeString, Math.random())}
                    className="flex items-center gap-1 px-1.5 py-0.5 border border-[#1E2830] hover:border-[#00D9FF] hover:text-[#00D9FF] transition-colors"
                  >
                    {copiedIndex !== null ? (
                      <>
                        <Check className="w-3 h-3 text-[#00D9FF]" />
                        <span>COPIED</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>COPY</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="p-3 overflow-x-auto font-mono text-xs text-[#00E5FF] leading-normal selection:bg-[#00D9FF]/20">
                  <code>{children}</code>
                </pre>
              </div>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
      {isStreaming && (
        <span className="inline-block w-2 h-4 ml-1 bg-[#00D9FF] animate-pulse align-middle" />
      )}
    </div>
  );
};

