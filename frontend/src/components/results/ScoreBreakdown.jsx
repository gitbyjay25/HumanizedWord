"use client";

/**
 * The five context-preservation dimensions (P4), each as a labelled bar.
 */
const DIMENSIONS = [
  { key: "semantic", label: "Semantic", hint: "SBERT cosine similarity" },
  { key: "ner", label: "Entities", hint: "Named entity retention" },
  { key: "keyword", label: "Keywords", hint: "Locked keyword satisfaction" },
  { key: "factual", label: "Factual", hint: "Numbers, negation, polarity" },
  { key: "intent", label: "Intent", hint: "Modality and register" },
];

export default function ScoreBreakdown({ scores }) {
  if (!scores) return null;

  return (
    <div className="space-y-1.5">
      {DIMENSIONS.map(({ key, label, hint }) => {
        const raw = scores[key];
        const value = typeof raw === "number" ? Math.max(0, Math.min(1, raw)) : 0;
        const colour =
          value >= 0.85
            ? "var(--emerald)"
            : value >= 0.6
              ? "var(--accent)"
              : "var(--red)";
        return (
          <div key={key} className="flex items-center gap-2" title={hint}>
            <span className="w-14 shrink-0 text-[10px] text-text-muted">
              {label}
            </span>
            <div className="h-1.5 flex-1 rounded-full bg-bg-hover overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-300"
                style={{ width: `${value * 100}%`, background: colour }}
              />
            </div>
            <span className="w-7 shrink-0 text-right text-[10px] tabular-nums text-text-secondary">
              {Math.round(value * 100)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
