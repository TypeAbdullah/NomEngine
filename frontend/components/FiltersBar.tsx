"use client";

import { Image as ImageIcon, Newspaper, Search, SlidersHorizontal, Video } from "lucide-react";

export type SearchTab = "all" | "images" | "news" | "videos";

interface FiltersBarProps {
  activeTab: SearchTab;
  onTabChange: (tab: SearchTab) => void;
  safeSearch: boolean;
  onSafeSearchToggle: () => void;
  tookMs?: number;
  totalResults?: number;
}

export function FiltersBar({
  activeTab,
  onTabChange,
  safeSearch,
  onSafeSearchToggle,
  tookMs,
  totalResults,
}: FiltersBarProps) {
  const tabs = [
    { id: "all" as SearchTab, label: "All", icon: Search },
    { id: "images" as SearchTab, label: "Images", icon: ImageIcon },
    { id: "news" as SearchTab, label: "News", icon: Newspaper },
    { id: "videos" as SearchTab, label: "Videos", icon: Video },
  ];

  return (
    <div className="w-full border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-[#202124]">
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row md:items-center justify-between gap-2">
        {/* Navigation Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto scrollbar-none">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  isActive
                    ? "border-nom-600 dark:border-nom-400 text-nom-600 dark:text-nom-400"
                    : "border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tools and latency indicator */}
        <div className="flex items-center gap-4 py-2 md:py-0 text-xs text-gray-500 dark:text-gray-400">
          {totalResults !== undefined && tookMs !== undefined && (
            <span>
              About {totalResults.toLocaleString()} results ({tookMs} ms)
            </span>
          )}

          <button
            onClick={onSafeSearchToggle}
            className={`px-2.5 py-1 rounded-md border text-xs font-medium transition-colors ${
              safeSearch
                ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-700 text-emerald-700 dark:text-emerald-300"
                : "bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400"
            }`}
          >
            SafeSearch: {safeSearch ? "Strict" : "Off"}
          </button>
        </div>
      </div>
    </div>
  );
}
