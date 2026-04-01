"use client";

import { useState } from "react";

const EXAMPLES = [
  "Where is the main entry point?",
  "How does authentication work?",
  "Find all API endpoints",
  "Show me the database schema",
];

interface SearchInputProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
  compact?: boolean;
}

export default function SearchInput({ onSubmit, disabled, compact }: SearchInputProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = () => {
    if (!query.trim() || disabled) return;
    onSubmit(query.trim());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (compact) {
    return (
      <div className="flex gap-1.5">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your code..."
          disabled={disabled}
          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || disabled}
          className="px-3 py-2 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shrink-0"
        >
          {disabled ? (
            <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            "Go"
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="w-full">
      <h2 className="text-xl sm:text-2xl font-semibold text-gray-800 dark:text-gray-100 text-center mb-1">
        Search your codebase
      </h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-4">
        Ask questions about your code in natural language
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your code..."
          disabled={disabled}
          className="flex-1 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || disabled}
          className="px-6 py-3 rounded-xl bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {disabled ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            "Search"
          )}
        </button>
      </div>

      <div className="flex flex-wrap gap-2 mt-3 justify-center">
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            onClick={() => {
              setQuery(ex);
              if (!disabled) onSubmit(ex);
            }}
            disabled={disabled}
            className="text-xs px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/30 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors disabled:opacity-50"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
