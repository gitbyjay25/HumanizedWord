"use client";

import { Sparkles } from "lucide-react";

export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12">
      <div className="w-16 h-16 rounded-full bg-accent-dim flex items-center justify-center mb-4">
        <Sparkles size={28} className="text-accent" />
      </div>
      <h3 className="text-sm font-medium text-text-primary mb-1">
        No AI results yet
      </h3>
      <p className="text-xs text-text-muted max-w-[200px]">
        Select text and use a tool from the sidebar
      </p>
    </div>
  );
}
