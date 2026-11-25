"use client";

export default function SidebarToolItem({
  icon: Icon,
  label,
  isActive,
  collapsed,
  onClick,
}) {
  return (
    <button
      onClick={onClick}
      title={collapsed ? label : undefined}
      className={`
        w-full flex items-center gap-2 rounded-md transition-all duration-150
        ${collapsed ? "justify-center px-0 py-2 mx-auto" : "px-2 py-1.5"}
        ${
          isActive
            ? "bg-accent-dim text-accent"
            : "text-text-secondary hover:bg-bg-hover hover:text-text-primary"
        }
      `}
    >
      <Icon size={16} className="shrink-0" />
      {!collapsed && <span className="text-sm truncate">{label}</span>}
    </button>
  );
}
