"use client";

import { useRef, useCallback } from "react";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import EditorToolbar from "./EditorToolbar";
import WordCounter from "./WordCounter";

export default function EditorPanel() {
  const { editorContent, setEditorContent } = useWorkspaceStore();
  const textareaRef = useRef(null);

  const handleChange = useCallback(
    (e) => {
      setEditorContent(e.target.value);
    },
    [setEditorContent]
  );

  return (
    <div className="flex flex-col h-screen bg-bg-primary border-r border-border">
      {/* Top toolbar */}
      <EditorToolbar />

      {/* Editor body */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <textarea
          ref={textareaRef}
          value={editorContent}
          onChange={handleChange}
          placeholder="Paste your AI-generated text here to humanize it..."
          className="w-full h-full resize-none bg-transparent text-text-primary text-base leading-relaxed placeholder:text-text-muted focus:outline-none"
          spellCheck={false}
        />
      </div>

      {/* Bottom counter bar */}
      <WordCounter />
    </div>
  );
}
