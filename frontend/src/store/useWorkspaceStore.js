import { create } from "zustand";

export const useWorkspaceStore = create((set, get) => ({
  // ─── Editor ───
  documentTitle: "Untitled Document",
  editorContent: "",
  wordCount: 0,
  charCount: 0,

  // ─── Sidebar ───
  selectedTool: null,
  selectedTone: "general",
  lockedKeywords: [],
  isSidebarCollapsed: false,
  searchQuery: "",

  // ─── Results ───
  results: [],
  isProcessing: false,

  // ─── Auth (display only) ───
  user: null,
  quota: { used: 0, limit: 2000 },

  // ─── Actions ───
  setDocumentTitle: (title) => set({ documentTitle: title }),

  setEditorContent: (content) => {
    const words = content.trim() ? content.trim().split(/\s+/) : [];
    set({
      editorContent: content,
      wordCount: words.length,
      charCount: content.length,
    });
  },

  setSelectedTool: (tool) => set({ selectedTool: tool }),
  setSelectedTone: (tone) => set({ selectedTone: tone }),

  addLockedKeyword: (keyword) => {
    const current = get().lockedKeywords;
    if (keyword.trim() && !current.includes(keyword.trim())) {
      set({ lockedKeywords: [...current, keyword.trim()] });
    }
  },

  removeLockedKeyword: (keyword) => {
    set({
      lockedKeywords: get().lockedKeywords.filter((k) => k !== keyword),
    });
  },

  toggleSidebar: () =>
    set((s) => ({ isSidebarCollapsed: !s.isSidebarCollapsed })),

  setSearchQuery: (query) => set({ searchQuery: query }),

  setProcessing: (state) => set({ isProcessing: state }),

  addResult: (result) =>
    set((s) => ({ results: [result, ...s.results] })),

}));
