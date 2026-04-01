"use client";

import type { AgentStep, StepName } from "@/lib/types";

const STEP_ICONS: Record<StepName, string> = {
  searching: "🔍",
  reranking: "🧠",
  answering: "✍️",
};

const STEP_LABELS: Record<StepName, string> = {
  searching: "Code Search",
  reranking: "Analyzing Relevance",
  answering: "Generating Answer",
};

function formatDuration(start: number, end?: number): string {
  const ms = (end || Date.now()) - start;
  const secs = Math.round(ms / 1000);
  if (secs < 60) return `${secs}s`;
  return `${Math.floor(secs / 60)}m ${secs % 60}s`;
}

interface StepTimelineProps {
  steps: AgentStep[];
}

export default function StepTimeline({ steps }: StepTimelineProps) {
  if (steps.length === 0) return null;

  return (
    <div className="space-y-1">
      <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        Agent Steps
      </h3>
      {steps.map((step, i) => (
        <div key={i} className="flex items-start gap-3">
          <div className="flex flex-col items-center">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs shrink-0 transition-all duration-300 ${
                step.status === "active"
                  ? "bg-emerald-100 dark:bg-emerald-900/40 ring-2 ring-emerald-400 ring-offset-1 ring-offset-white dark:ring-offset-gray-900"
                  : "bg-green-100 dark:bg-green-900/30"
              }`}
            >
              {step.status === "active" ? (
                <div className="w-3.5 h-3.5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
              ) : (
                <span className="text-xs">{STEP_ICONS[step.step]}</span>
              )}
            </div>
            {i < steps.length - 1 && (
              <div className={`w-px h-full min-h-[16px] mt-1 transition-colors ${
                step.status === "done" ? "bg-green-200 dark:bg-green-800/40" : "bg-gray-200 dark:bg-gray-700"
              }`} />
            )}
          </div>

          <div className="flex-1 min-w-0 pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                {STEP_LABELS[step.step]}
              </span>
              {step.endTime ? (
                <span className="text-[10px] text-gray-400 dark:text-gray-500 tabular-nums bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">
                  {formatDuration(step.startTime, step.endTime)}
                </span>
              ) : null}
              {step.status === "active" ? (
                <span className="text-[10px] text-emerald-500 dark:text-emerald-400 font-medium animate-pulse">
                  In progress
                </span>
              ) : null}
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
              {step.message}
            </p>

            {step.data && step.step === "searching" && step.data.count ? (
              <div className="mt-1.5">
                <div className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Found {String(step.data.count)} code snippets
                </div>
                {step.data.files ? (
                  <div className="mt-1 space-y-0.5">
                    {(step.data.files as string[]).slice(0, 5).map((f: string, j: number) => (
                      <div key={j} className="text-[10px] text-gray-500 dark:text-gray-400 font-mono truncate">
                        {f}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}

            {step.data && step.step === "reranking" && step.data.selected ? (
              <div className="text-xs text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Selected {String(step.data.selected)} most relevant snippets
              </div>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
