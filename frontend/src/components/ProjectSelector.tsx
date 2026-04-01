"use client";

import { useState } from "react";
import { indexProject } from "@/lib/api";
import type { Project } from "@/lib/types";

interface ProjectSelectorProps {
  projects: Project[];
  selected: string;
  onSelect: (name: string) => void;
  onRefresh: () => Promise<void>;
  serverReady: boolean;
}

export default function ProjectSelector({
  projects,
  selected,
  onSelect,
  onRefresh,
  serverReady,
}: ProjectSelectorProps) {
  const [showIndex, setShowIndex] = useState(false);
  const [indexPath, setIndexPath] = useState("");
  const [indexName, setIndexName] = useState("");
  const [indexing, setIndexing] = useState(false);
  const [indexResult, setIndexResult] = useState<string | null>(null);

  const handleIndex = async () => {
    if (!indexPath.trim()) return;
    setIndexing(true);
    setIndexResult(null);

    const result = await indexProject(indexPath.trim(), indexName.trim() || undefined);
    if (result.success) {
      const data = result.data as Record<string, unknown>;
      setIndexResult(`Indexed ${data.total_files} files, ${data.total_chunks} chunks`);
      await onRefresh();
      setShowIndex(false);
      setIndexPath("");
      setIndexName("");
      if (data.project) onSelect(String(data.project));
    } else {
      setIndexResult(`Error: ${result.error}`);
    }
    setIndexing(false);
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Select Project
      </label>

      {projects.length > 0 ? (
        <div className="space-y-2">
          <select
            value={selected}
            onChange={(e) => onSelect(e.target.value)}
            className="w-full rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Choose a project...</option>
            {projects.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name} ({p.total_files} files, {p.languages.join(", ")})
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="text-center py-4 px-3 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            No projects indexed yet
          </p>
        </div>
      )}

      {/* Index new project */}
      <div className="mt-3">
        {!showIndex ? (
          <button
            onClick={() => setShowIndex(true)}
            disabled={!serverReady}
            className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline disabled:opacity-50"
          >
            + Index a new project
          </button>
        ) : (
          <div className="space-y-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700">
            <input
              type="text"
              value={indexPath}
              onChange={(e) => setIndexPath(e.target.value)}
              placeholder="Project path (e.g., C:\Users\project)"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <input
              type="text"
              value={indexName}
              onChange={(e) => setIndexName(e.target.value)}
              placeholder="Project name (optional)"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-xs text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <div className="flex gap-2">
              <button
                onClick={handleIndex}
                disabled={indexing || !indexPath.trim()}
                className="flex-1 px-3 py-2 rounded-lg bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 disabled:opacity-40 transition-colors"
              >
                {indexing ? "Indexing..." : "Index Project"}
              </button>
              <button
                onClick={() => { setShowIndex(false); setIndexResult(null); }}
                className="px-3 py-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
            {indexResult && (
              <p className={`text-xs ${indexResult.startsWith("Error") ? "text-red-500" : "text-green-500"}`}>
                {indexResult}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
