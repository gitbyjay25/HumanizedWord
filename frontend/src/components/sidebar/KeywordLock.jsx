"use client";

import { useState } from "react";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { Lock, X } from "lucide-react";

export default function KeywordLock() {
  const [input, setInput] = useState("");
  const { lockedKeywords, addLockedKeyword, removeLockedKeyword } =
    useWorkspaceStore();

  const handleAdd = (e) => {
    if (e.key === "Enter" && input.trim()) {
      addLockedKeyword(input);
      setInput("");
    }
  };

  return (
    <div className="px-2 pb-2">
      <div className="flex items-center gap-1.5 mb-1.5">
        <Lock size={12} className="text-emerald" />
        <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
          Keyword Lock
        </span>
      </div>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleAdd}
        placeholder="Type + Enter to lock..."
        className="w-full bg-bg-elevated text-text-primary text-xs rounded-md px-2.5 py-1.5 border border-border-subtle focus:border-emerald focus:outline-none placeholder:text-text-muted mb-1.5"
      />

      {lockedKeywords.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {lockedKeywords.map((kw) => (
            <span
              key={kw}
              className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-emerald-dim text-emerald border border-emerald/30"
            >
              {kw}
              <button
                onClick={() => removeLockedKeyword(kw)}
                className="hover:text-red transition-colors"
              >
                <X size={10} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
