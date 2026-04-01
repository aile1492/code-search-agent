"use client";

import { useState, useCallback } from "react";
import { startSearch } from "@/lib/api";
import type { SSEEvent, AgentStep, CodeResult, StepName, LLMSettings } from "@/lib/types";

export type SearchStatus = "idle" | "running" | "done" | "error";

export function useSearch() {
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [answer, setAnswer] = useState("");
  const [results, setResults] = useState<CodeResult[]>([]);
  const [status, setStatus] = useState<SearchStatus>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleEvent = useCallback((event: SSEEvent) => {
    switch (event.type) {
      case "step_start": {
        setSteps((prev) => {
          const updated = prev.map((s) =>
            s.status === "active" && s.step !== event.step
              ? { ...s, status: "done" as const, endTime: Date.now() }
              : s
          );
          return [
            ...updated,
            {
              step: event.step,
              message: event.message,
              status: "active" as const,
              startTime: Date.now(),
            },
          ];
        });
        break;
      }

      case "step_data": {
        setSteps((prev) =>
          prev.map((s) =>
            s.step === event.step && s.status === "active"
              ? { ...s, data: { ...s.data, ...event.data } }
              : s
          )
        );
        break;
      }

      case "chunk": {
        setAnswer((prev) => prev + event.content);
        break;
      }

      case "done": {
        setSteps((prev) =>
          prev.map((s) =>
            s.status === "active"
              ? { ...s, status: "done" as const, endTime: Date.now() }
              : s
          )
        );
        if (event.data.results) setResults(event.data.results);
        if (event.data.session_id) setSessionId(event.data.session_id);
        setStatus("done");
        break;
      }

      case "error": {
        setError(event.content);
        setStatus("error");
        break;
      }
    }
  }, []);

  const search = useCallback(
    async (query: string, project: string, llmSettings?: LLMSettings) => {
      setSteps([]);
      setAnswer("");
      setResults([]);
      setError(null);
      setStatus("running");

      try {
        await startSearch(query, project, sessionId, handleEvent, llmSettings);
      } catch {
        setError("Failed to connect to the server.");
        setStatus("error");
      }
    },
    [sessionId, handleEvent]
  );

  const reset = useCallback(() => {
    setSteps([]);
    setAnswer("");
    setResults([]);
    setError(null);
    setStatus("idle");
    setSessionId(null);
  }, []);

  return {
    steps,
    answer,
    results,
    status,
    error,
    search,
    reset,
  };
}
