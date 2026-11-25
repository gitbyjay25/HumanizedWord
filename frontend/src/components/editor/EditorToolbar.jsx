"use client";

import { useState } from "react";
import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { Copy } from "lucide-react";

export default function EditorToolbar() {
  const {
    documentTitle,
    setDocumentTitle,
    wordCount,
    editorContent,
  } = useWorkspaceStore();
  const [isEditing, setIsEditing] = useState(false);
  const [copied, setCopied] = useState(false);

  const tokenCount = Math.ceil(editorContent.length / 4); // Rough token estimate

  const handleCopy = async () => {
    if (editorContent) {
      await navigator.clipboard.writeText(editorContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-bg-secondary/50">
      {/* Left: Title + Stats */}
      <div className="flex items-center gap-3 min-w-0">
        {isEditing ? (
          <input
            type="text"
            value={documentTitle}
            onChange={(e) => setDocumentTitle(e.target.value)}
            onBlur={() => setIsEditing(false)}
            onKeyDown={(e) => e.key === "Enter" && setIsEditing(false)}
            autoFocus
            className="text-sm font-medium bg-bg-elevated text-text-primary border border-accent rounded px-2 py-0.5 focus:outline-none"
          />
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="text-sm font-medium text-text-primary hover:text-accent transition-colors truncate"
          >
            {documentTitle}
          </button>
        )}

        <span className="text-xs text-text-muted whitespace-nowrap">
          {wordCount} words
        </span>
        <span className="text-xs text-text-muted whitespace-nowrap">
          {tokenCount} tokens
        </span>
      </div>

      {/* Right: Action buttons */}
      <div className="flex items-center gap-1">
        <button
          onClick={handleCopy}
          className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-text-primary transition-colors"
          title={copied ? "Copied!" : "Copy all"}
        >
          <Copy size={15} />
        </button>
      </div>
    </div>
  );
}
