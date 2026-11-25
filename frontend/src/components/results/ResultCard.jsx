"use client";

import { useState } from "react";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { Copy, Check, ArrowRight, ChevronDown, AlertTriangle } from "lucide-react";
import RadialScoreGauge from "./RadialScoreGauge";
import ScoreBreakdown from "./ScoreBreakdown";

export default function ResultCard({ result, index }) {
  const [copied, setCopied] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const { setEditorContent } = useWorkspaceStore();

  const meta = result.metadata || {};
  const hasScores = typeof meta.preservation_score === "number";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleUse = () => {
    setEditorContent(result.result);
  };

  return (
    <div className="rounded-lg bg-bg-elevated border border-border p-4 hover:border-accent/30 transition-colors">
      {/* Content */}
      <p className="text-sm text-text-primary leading-relaxed mb-3 whitespace-pre-wrap">
        {result.result}
      </p>

      {/* Preservation scores */}
      {hasScores && (
        <div className="mb-3 pb-3 border-b border-border-subtle space-y-3">
          <RadialScoreGauge score={meta.preservation_score} />
          <ScoreBreakdown scores={meta.scores} />

          {(meta.missing_entities?.length > 0 ||
            meta.missing_keywords?.length > 0) && (
            <div className="flex items-start gap-1.5 text-[10px] text-text-muted">
              <AlertTriangle size={11} className="mt-0.5 shrink-0 text-accent" />
              <span className="min-w-0">
                {meta.missing_entities?.length > 0 && (
                  <>
                    Dropped: {meta.missing_entities.join(", ")}
                    {meta.missing_keywords?.length > 0 ? " · " : ""}
                  </>
                )}
                {meta.missing_keywords?.length > 0 && (
                  <>Missing keywords: {meta.missing_keywords.join(", ")}</>
                )}
              </span>
            </div>
          )}

          {meta.warning && (
            <div className="flex items-start gap-1.5 text-[10px] text-accent">
              <AlertTriangle size={11} className="mt-0.5 shrink-0" />
              <span className="min-w-0">{meta.warning}</span>
            </div>
          )}

          {meta.diff?.length > 0 && (
            <div>
              <button
                onClick={() => setShowDiff((v) => !v)}
                className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-secondary transition-colors"
              >
                <ChevronDown
                  size={11}
                  style={{
                    transform: showDiff ? "rotate(180deg)" : "none",
                    transition: "transform 150ms ease",
                  }}
                />
                {showDiff ? "Hide" : "Show"} changes ({meta.diff.length})
              </button>
              {showDiff && (
                <div className="mt-2 max-h-48 overflow-y-auto space-y-1">
                  {meta.diff.map((op, i) => (
                    <div
                      key={i}
                      className="text-[11px] leading-relaxed font-mono"
                    >
                      {op.original && (
                        <span className="text-red line-through decoration-red/50">
                          {op.original}
                        </span>
                      )}
                      {op.revised && (
                        <span className="text-emerald"> {op.revised}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions + Meta */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-md bg-bg-hover text-text-secondary hover:text-text-primary transition-colors"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? "Copied" : "Copy"}
          </button>
          <button
            onClick={handleUse}
            className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-md bg-accent-dim text-accent hover:bg-accent/20 transition-colors"
          >
            <ArrowRight size={12} />
            Use this
          </button>
        </div>

        <div className="flex items-center gap-2 text-[10px] text-text-muted">
          {meta.tool && meta.tool !== "humanize" && (
            <>
              <span className="capitalize">{meta.tool}</span>
              <span>·</span>
            </>
          )}
          <span>{meta.tone_applied}</span>
          <span>·</span>
          <span>{result.processing_time}s</span>
          {typeof meta.repair_iterations === "number" &&
            meta.repair_iterations > 1 && (
              <>
                <span>·</span>
                <span>{meta.repair_iterations} passes</span>
              </>
            )}
        </div>
      </div>
    </div>
  );
}
