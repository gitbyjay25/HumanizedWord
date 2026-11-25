"use client";

import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import Sidebar from "@/components/sidebar/Sidebar";
import EditorPanel from "@/components/editor/EditorPanel";
import ResultsPanel from "@/components/results/ResultsPanel";

export default function WorkspaceLayout() {
  const isSidebarCollapsed = useWorkspaceStore((s) => s.isSidebarCollapsed);

  return (
    <div
      className="h-screen overflow-hidden grid"
      style={{
        gridTemplateColumns: isSidebarCollapsed
          ? "48px 1fr 340px"
          : "240px 1fr 340px",
      }}
    >
      {/* Left Sidebar */}
      <Sidebar />

      {/* Center Editor */}
      <EditorPanel />

      {/* Right Results Panel */}
      <ResultsPanel />
    </div>
  );
}
