"use client";

import { useEffect, useRef, useState } from "react";
import { wakeServer, getProjects } from "@/lib/api";
import { useSearch } from "@/hooks/useSearch";
import type { LLMSettings, Project } from "@/lib/types";
import ProjectSelector from "./ProjectSelector";
import SearchInput from "./SearchInput";
import StepTimeline from "./StepTimeline";
import AnswerView from "./AnswerView";
import LLMSettingsPanel from "./LLMSettingsPanel";

export default function SearchWindow() {
  const { steps, answer, results, status, error, search, reset } = useSearch();
  const [serverStatus, setServerStatus] = useState<"waking" | "ready" | "error">("waking");
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>("");
  const llmSettingsRef = useRef<LLMSettings>({ provider: "gemini", apiKey: "" });

  useEffect(() => {
    wakeServer().then((ok) => {
      setServerStatus(ok ? "ready" : "error");
      if (ok) {
        getProjects().then(setProjects);
      }
    });
  }, []);

  const refreshProjects = async () => {
    const p = await getProjects();
    setProjects(p);
    if (p.length > 0 && !selectedProject) {
      setSelectedProject(p[0].name);
    }
  };

  const isRunning = status === "running";
  const isDone = status === "done";
  const showResults = isRunning || isDone || status === "error";

  const handleSearch = (query: string) => {
    if (!selectedProject) return;
    search(query, selectedProject, llmSettingsRef.current);
  };

  return (
    <div className="flex flex-col h-full max-w-7xl mx-auto w-full">
      {/* Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-600 flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              Code Search Agent
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              AI-powered codebase search with LangGraph
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <LLMSettingsPanel onChange={(s) => (llmSettingsRef.current = s)} />
          {showResults && (
            <button
              onClick={reset}
              disabled={isRunning}
              className="text-sm px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              New Search
            </button>
          )}
        </div>
      </header>

      {/* Server status banner */}
      {serverStatus === "waking" && (
        <div className="flex items-center gap-2 px-4 sm:px-6 py-2 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-400 text-xs">
          <div className="w-3 h-3 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin shrink-0" />
          Starting server... First visit may take up to 30 seconds.
        </div>
      )}
      {serverStatus === "error" && (
        <div className="flex items-center gap-2 px-4 sm:px-6 py-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 text-xs">
          Cannot connect to server. Please try again later.
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {!showResults ? (
          <div className="flex items-center justify-center h-full px-4">
            <div className="w-full max-w-2xl">
              <div className="mb-6 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 dark:from-emerald-500/20 dark:to-cyan-500/20 flex items-center justify-center">
                  <svg className="w-8 h-8 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                </div>
              </div>
              <ProjectSelector
                projects={projects}
                selected={selectedProject}
                onSelect={setSelectedProject}
                onRefresh={refreshProjects}
                serverReady={serverStatus === "ready"}
              />
              <div className="mt-4">
                <SearchInput
                  onSubmit={handleSearch}
                  disabled={isRunning || serverStatus !== "ready" || !selectedProject}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col lg:flex-row h-full">
            {/* Left panel */}
            <div className="lg:w-[340px] shrink-0 border-b lg:border-b-0 lg:border-r border-gray-200 dark:border-gray-700 p-3 sm:p-4 overflow-y-auto custom-scrollbar max-h-[30vh] lg:max-h-none">
              <div className="mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">
                  Project: <span className="font-medium text-gray-700 dark:text-gray-300">{selectedProject}</span>
                </div>
                <SearchInput
                  onSubmit={handleSearch}
                  disabled={isRunning || !selectedProject}
                  compact
                />
              </div>
              <StepTimeline steps={steps} />
            </div>

            {/* Right panel */}
            <div className="flex-1 p-3 sm:p-6 overflow-y-auto custom-scrollbar">
              {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2">
                  <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                </div>
              )}
              <AnswerView
                answer={answer}
                results={results}
                isStreaming={isRunning}
              />
              {isRunning && !answer && (
                <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-500">
                  <div className="text-center">
                    <div className="relative w-16 h-16 mx-auto mb-4">
                      <div className="absolute inset-0 border-4 border-emerald-200 dark:border-emerald-900 rounded-full" />
                      <div className="absolute inset-0 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    </div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Searching codebase...</p>
                    <p className="text-xs mt-1">AI is analyzing your code</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
