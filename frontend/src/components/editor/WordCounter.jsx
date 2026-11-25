"use client";

import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { useHumanize } from "@/hooks/useHumanize";
import { useToast } from "@/components/ui/Toast";
import { Sparkles, Loader2 } from "lucide-react";

export default function WordCounter() {
  const { wordCount, charCount, isProcessing, selectedTone, editorContent } = useWorkspaceStore();
  const { runTool } = useHumanize();
  const { addToast } = useToast();

  const handleHumanize = async () => {
    const res = await runTool("humanize");
    if (res?.error) {
      addToast(res.error, "error");
    } else if (res?.success) {
      addToast("Text humanized successfully!", "success");
    }
  };

  const isTooShort = !editorContent || editorContent.trim().length < 10;

  return (
    <div className="px-6 py-2.5 border-t border-border flex items-center justify-between bg-bg-secondary/40">
      <div className="flex items-center gap-4">
        <span className="text-xs text-text-muted">
          {wordCount} words
        </span>
        <span className="text-xs text-text-muted">
          {charCount} characters
        </span>
      </div>

      <button
        onClick={handleHumanize}
        disabled={isProcessing || isTooShort}
        className={`
          flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold
          transition-all duration-150 shadow-sm
          ${
            isProcessing || isTooShort
              ? "bg-bg-elevated text-text-muted border border-border cursor-not-allowed opacity-60"
              : "bg-accent text-bg-primary hover:bg-accent/90 active:scale-95 cursor-pointer"
          }
        `}
      >
        {isProcessing ? (
          <>
            <Loader2 size={13} className="animate-spin" />
            <span>Humanizing...</span>
          </>
        ) : (
          <>
            <Sparkles size={13} />
            <span className="capitalize">Humanize ({selectedTone})</span>
          </>
        )}
      </button>
    </div>
  );
}
