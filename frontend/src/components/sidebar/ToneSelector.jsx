"use client";

import { useState } from "react";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { useHumanize } from "@/hooks/useHumanize";
import { useToast } from "@/components/ui/Toast";
import { ChevronDown, ChevronRight } from "lucide-react";

const TONES = [
  { id: "general", label: "General" },
  { id: "academic", label: "Academic" },
  { id: "professional", label: "Professional" },
  { id: "friendly", label: "Friendly" },
  { id: "casual", label: "Casual" },
];

export default function ToneSelector() {
  const [isOpen, setIsOpen] = useState(true);
  const { selectedTone, setSelectedTone, editorContent } = useWorkspaceStore();
  const { runTool } = useHumanize();
  const { addToast } = useToast();

  const handleToneSelect = async (toneId) => {
    setSelectedTone(toneId);
    if (editorContent && editorContent.trim().length >= 10) {
      const res = await runTool("humanize", toneId);
      if (res?.error) {
        addToast(res.error, "error");
      }
    }
  };

  return (
    <div className="mb-1">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-2 py-1.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider hover:text-text-secondary transition-colors"
      >
        <span>Tone</span>
        {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>

      {isOpen && (
        <div className="flex flex-wrap gap-1 px-2 pb-2">
          {TONES.map((tone) => (
            <button
              key={tone.id}
              onClick={() => handleToneSelect(tone.id)}
              className={`
                text-xs px-2.5 py-1 rounded-full border transition-all duration-150
                ${
                  selectedTone === tone.id
                    ? "border-accent text-accent bg-accent-dim font-medium"
                    : "border-border-subtle text-text-muted hover:border-text-muted hover:text-text-secondary"
                }
              `}
            >
              {tone.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
