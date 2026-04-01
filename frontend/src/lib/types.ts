export type StepName = "searching" | "reranking" | "answering";

export type LLMProvider = "gemini" | "anthropic" | "groq";

export interface LLMSettings {
  provider: LLMProvider;
  apiKey: string; // empty = use server default
}

export interface StepStartEvent {
  type: "step_start";
  step: StepName;
  message: string;
}

export interface StepDataEvent {
  type: "step_data";
  step: StepName;
  data: Record<string, unknown>;
}

export interface ChunkEvent {
  type: "chunk";
  content: string;
}

export interface DoneEvent {
  type: "done";
  data: {
    answer: string;
    results: CodeResult[];
    session_id: string;
  };
}

export interface ErrorEvent {
  type: "error";
  content: string;
}

export type SSEEvent = StepStartEvent | StepDataEvent | ChunkEvent | DoneEvent | ErrorEvent;

export interface CodeResult {
  file_path: string;
  name: string;
  chunk_type: string;
  language: string;
  start_line: number;
  end_line: number;
  similarity: number;
  code?: string;
}

export interface Project {
  name: string;
  path: string;
  total_files: number;
  total_chunks: number;
  languages: string[];
}

export interface AgentStep {
  step: StepName;
  message: string;
  status: "active" | "done";
  data?: Record<string, unknown>;
  startTime: number;
  endTime?: number;
}
