"use client";

/**
 * Radial gauge for the composite context-preservation score (S_total).
 * Colour follows the acceptance threshold used by the P5 repair loop (0.85).
 */
export default function RadialScoreGauge({ score, size = 64, threshold = 0.85 }) {
  const value = typeof score === "number" ? Math.max(0, Math.min(1, score)) : null;
  const radius = size / 2 - 5;
  const circumference = 2 * Math.PI * radius;
  const offset = value === null ? circumference : circumference * (1 - value);

  const tone = (v) => {
    if (v >= threshold) return "var(--emerald)";
    if (v >= 0.6) return "var(--accent)";
    return "var(--red)";
  };

  const colour = value === null ? "var(--text-muted)" : tone(value);

  return (
    <div className="flex items-center gap-2.5">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--bg-hover)"
            strokeWidth="4"
          />
          {value !== null && (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={colour}
              strokeWidth="4"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 400ms ease" }}
            />
          )}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span
            className="text-sm font-semibold tabular-nums"
            style={{ color: colour }}
          >
            {value === null ? "—" : Math.round(value * 100)}
          </span>
        </div>
      </div>
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-wider text-text-muted">
          Preservation
        </p>
        <p className="text-[11px] text-text-secondary">
          {value === null
            ? "not scored"
            : value >= threshold
              ? "meaning preserved"
              : value >= 0.6
                ? "minor drift"
                : "significant drift"}
        </p>
      </div>
    </div>
  );
}
