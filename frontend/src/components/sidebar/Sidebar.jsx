"use client";

import { useWorkspaceStore } from "@/store/useWorkspaceStore";
import { useHumanize } from "@/hooks/useHumanize";
import { useToast } from "@/components/ui/Toast";
import SidebarToolItem from "./SidebarToolItem";
import ToneSelector from "./ToneSelector";
import KeywordLock from "./KeywordLock";
import {
  Sparkles,
  RefreshCw,
  FileEdit,
  Maximize2,
  Minimize2,
  AlignLeft,
  PenLine,
  CheckCircle,
  Languages,
  Lightbulb,
  FileText,
  Search,
  Settings,
  LogIn,
  ChevronLeft,
  ChevronRight,
  User,
} from "lucide-react";

const ENHANCE_TOOLS = [
  { id: "humanize", label: "Humanize", icon: Sparkles },
  { id: "rewrite", label: "Rewrite", icon: RefreshCw },
  { id: "simplify", label: "Simplify", icon: FileEdit },
];

const TRANSFORM_TOOLS = [
  { id: "expand", label: "Expand", icon: Maximize2 },
  { id: "shorten", label: "Shorten", icon: Minimize2 },
  { id: "summarize", label: "Summarize", icon: AlignLeft },
  { id: "continue", label: "Continue Writing", icon: PenLine },
];

const UTILITY_TOOLS = [
  { id: "grammar", label: "Grammar", icon: CheckCircle },
  { id: "translate", label: "Translate", icon: Languages },
  { id: "explain", label: "Explain", icon: Lightbulb },
  { id: "title", label: "Generate Title", icon: FileText },
];

export default function Sidebar() {
  const {
    isSidebarCollapsed,
    toggleSidebar,
    selectedTool,
    setSelectedTool,
    searchQuery,
    setSearchQuery,
    user,
    quota,
  } = useWorkspaceStore();

  const collapsed = isSidebarCollapsed;
  const { runTool } = useHumanize();
  const { addToast } = useToast();

  const handleToolClick = async (toolId) => {
    setSelectedTool(toolId);
    const res = await runTool(toolId);
    if (res?.error) {
      addToast(res.error, "error");
    } else if (res?.success) {
      addToast("Processed successfully!", "success");
    }
  };

  const filterTools = (tools) => {
    if (!searchQuery) return tools;
    return tools.filter((t) =>
      t.label.toLowerCase().includes(searchQuery.toLowerCase())
    );
  };

  return (
    <aside
      className="h-screen bg-bg-secondary border-r border-border flex flex-col transition-sidebar overflow-hidden"
      style={{ width: collapsed ? 48 : 240 }}
    >
      {/* User Info */}
      <div className="p-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-bg-elevated flex items-center justify-center shrink-0">
            <User size={16} className="text-text-muted" />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">
                {user?.name || "Guest"}
              </p>
            </div>
          )}
        </div>
        {!collapsed && (
          <div className="mt-2">
            <div className="flex justify-between text-xs text-text-muted mb-1">
              <span>Guest</span>
              <span>
                {quota.used} / {quota.limit}
              </span>
            </div>
            <div className="w-full h-1.5 bg-bg-elevated rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-300"
                style={{
                  width: `${Math.min((quota.used / quota.limit) * 100, 100)}%`,
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* AI Tools Header + Search */}
      {!collapsed && (
        <div className="px-3 pt-3 pb-1">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <Sparkles size={14} className="text-accent" />
              <span className="text-xs font-semibold text-text-secondary uppercase tracking-wide">
                AI Tools
              </span>
            </div>
            <Settings
              size={14}
              className="text-text-muted hover:text-text-primary cursor-pointer transition-colors"
            />
          </div>
          <div className="relative">
            <Search
              size={14}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted"
            />
            <input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-bg-elevated text-text-primary text-xs rounded-md pl-8 pr-3 py-1.5 border border-border-subtle focus:border-accent focus:outline-none placeholder:text-text-muted"
            />
          </div>
        </div>
      )}

      {/* Tool Groups */}
      <div className="flex-1 overflow-y-auto px-1.5 py-1">
        {/* ENHANCE */}
        <ToolGroup label="ENHANCE" collapsed={collapsed}>
          {filterTools(ENHANCE_TOOLS).map((tool) => (
            <SidebarToolItem
              key={tool.id}
              icon={tool.icon}
              label={tool.label}
              isActive={selectedTool === tool.id}
              collapsed={collapsed}
              onClick={() => handleToolClick(tool.id)}
            />
          ))}
        </ToolGroup>

        {/* TRANSFORM */}
        <ToolGroup label="TRANSFORM" collapsed={collapsed}>
          {filterTools(TRANSFORM_TOOLS).map((tool) => (
            <SidebarToolItem
              key={tool.id}
              icon={tool.icon}
              label={tool.label}
              isActive={selectedTool === tool.id}
              collapsed={collapsed}
              onClick={() => handleToolClick(tool.id)}
            />
          ))}
        </ToolGroup>

        {/* TONE */}
        {!collapsed && <ToneSelector />}

        {/* UTILITY */}
        <ToolGroup label="UTILITY" collapsed={collapsed}>
          {filterTools(UTILITY_TOOLS).map((tool) => (
            <SidebarToolItem
              key={tool.id}
              icon={tool.icon}
              label={tool.label}
              isActive={selectedTool === tool.id}
              collapsed={collapsed}
              onClick={() => handleToolClick(tool.id)}
            />
          ))}
        </ToolGroup>

        {/* Keyword Lock */}
        {!collapsed && <KeywordLock />}
      </div>

      {/* Footer */}
      <div className="border-t border-border p-2 flex items-center justify-between">
        {!collapsed && (
          <button className="flex items-center gap-2 text-xs text-text-muted hover:text-accent transition-colors px-1.5 py-1 rounded">
            <LogIn size={14} />
            <span>Sign in</span>
          </button>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded hover:bg-bg-hover text-text-muted hover:text-text-primary transition-colors ml-auto"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
}

function ToolGroup({ label, collapsed, children }) {
  return (
    <div className="mb-1">
      {!collapsed && (
        <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider px-2 py-1.5">
          {label}
        </p>
      )}
      {collapsed && <div className="my-1 mx-2 border-t border-border-subtle" />}
      {children}
    </div>
  );
}
