"use client";

import { useCallback } from "react";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { humanizeText } from "@/lib/api";

/**
 * Hook that handles the full flow:
 * tool click / tone select → validate → API call → populate results
 */
export function useHumanize() {
  const {
    setProcessing,
    addResult,
    setSelectedTool,
  } = useWorkspaceStore();

  const runTool = useCallback(
    async (toolId = "humanize", overrideTone = null) => {
      const state = useWorkspaceStore.getState();
      const textToProcess = state.editorContent;

      // Validate
      if (!textToProcess || textToProcess.trim().length < 10) {
        return { error: "Please enter at least 10 characters to process." };
      }

      const activeTone = overrideTone || state.selectedTone;
      const activeKeywords = state.lockedKeywords;

      setSelectedTool(toolId);
      setProcessing(true);

      try {
        const response = await humanizeText({
          text: textToProcess,
          tone: activeTone,
          lockedKeywords: activeKeywords,
          tool: toolId,
        });

        addResult(response);
        setProcessing(false);
        return { success: true, data: response };
      } catch (err) {
        setProcessing(false);
        return { error: err.message || "Failed to process text." };
      }
    },
    [setProcessing, addResult, setSelectedTool]
  );

  return { runTool };
}
