"use client";

import { useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import type { CodeResult } from "@/lib/types";

interface AnswerViewProps {
  answer: string;
  results: CodeResult[];
  isStreaming: boolean;
}

export default function AnswerView({ answer, results, isStreaming }: AnswerViewProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [answer]);

  if (!answer) return null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-6 bg-emerald-500 rounded-full" />
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-200 uppercase tracking-wide">
            Answer
          </h3>
        </div>
        {!isStreaming && (
          <button
            onClick={handleCopy}
            className={`text-xs px-3 py-1.5 rounded-lg font-medium transition-all duration-200 ${
              copied
                ? "bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400"
                : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
            }`}
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        )}
      </div>

      {/* Answer content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <article className="prose prose-sm dark:prose-invert max-w-none
          prose-headings:text-gray-800 dark:prose-headings:text-gray-100
          prose-headings:font-semibold
          prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
          prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:leading-relaxed
          prose-a:text-emerald-600 dark:prose-a:text-emerald-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-gray-800 dark:prose-strong:text-gray-100
          prose-code:text-emerald-600 dark:prose-code:text-emerald-400 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:before:content-none prose-code:after:content-none
          prose-pre:bg-transparent prose-pre:p-0
        ">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {answer}
          </ReactMarkdown>
          {isStreaming && (
            <span className="inline-block w-2 h-5 bg-emerald-500 animate-pulse ml-0.5 rounded-sm" />
          )}
        </article>
      </div>

      {/* Referenced files */}
      {!isStreaming && results.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
            Referenced Code ({results.length})
          </h4>
          <div className="grid gap-2 max-h-48 overflow-y-auto custom-scrollbar">
            {results.map((r, i) => (
              <div
                key={i}
                className="flex items-start gap-2.5 p-2 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700/50"
              >
                <span className="w-5 h-5 rounded-md bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-gray-700 dark:text-gray-300 truncate">
                      {r.file_path}
                    </span>
                    <span className="text-[10px] text-gray-400 shrink-0">
                      L{r.start_line}-{r.end_line}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                      {r.chunk_type}
                    </span>
                    <span className="text-[10px] text-gray-500 dark:text-gray-400 font-mono">
                      {r.name}
                    </span>
                    <span className="text-[10px] text-emerald-500 ml-auto">
                      {Math.round(r.similarity * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
