"use client";

import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import ResultCard from "./ResultCard";
import EmptyState from "./EmptyState";
import { Sparkles } from "lucide-react";

export default function ResultsPanel() {
  const { results, isProcessing } = useWorkspaceStore();

  return (
    <div className="h-screen flex flex-col bg-bg-secondary">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-accent" />
          <h2 className="text-sm font-semibold text-text-primary">
            AI Results
          </h2>
          <span className="text-xs text-text-muted">
            {results.length} result{results.length !== 1 ? "s" : ""}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {isProcessing && (
          <div className="space-y-3 mb-3">
            <div className="rounded-lg bg-bg-elevated border border-border p-4 space-y-2">
              <div className="skeleton h-4 rounded w-3/4" />
              <div className="skeleton h-4 rounded w-full" />
              <div className="skeleton h-4 rounded w-5/6" />
              <div className="skeleton h-3 rounded w-1/2 mt-3" />
            </div>
          </div>
        )}

        {results.length > 0 ? (
          <div className="space-y-3">
            {results.map((result, idx) => (
              <ResultCard key={idx} result={result} index={idx} />
            ))}
          </div>
        ) : (
          !isProcessing && <EmptyState />
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-border text-xs text-text-muted">
        <div className="flex items-center gap-1.5">
          <Sparkles size={12} />
          <span>Results</span>
        </div>
      </div>
    </div>
  );
}
