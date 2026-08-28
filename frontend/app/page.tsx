"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { fetchAdminStats, fetchSuggestions } from "@/lib/api";
import { Activity, Grid, Search, X } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [stats, setStats] = useState<{ docs: number; terms: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAdminStats()
      .then((data) => {
        setStats({
          docs: data.pages_indexed,
          terms: data.unique_terms_in_index,
        });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!query.trim()) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }
    const timer = setTimeout(async () => {
      const results = await fetchSuggestions(query);
      setSuggestions(results);
      setIsOpen(results.length > 0);
      setSelectedIndex(-1);
    }, 150);
    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSearch = (searchQuery?: string) => {
    const q = (searchQuery !== undefined ? searchQuery : query).trim();
    if (!q) return;
    setIsOpen(false);
    router.push(`/search?q=${encodeURIComponent(q)}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSearch(suggestions[selectedIndex]);
      } else {
        handleSearch();
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-white dark:bg-[#202124] text-gray-900 dark:text-[#e8eaed] font-sans antialiased select-none">
      {/* Top Google-style Navigation */}
      <header className="w-full flex items-center justify-end px-6 py-4 gap-4 text-sm text-[#1f1f1f] dark:text-[#e8eaed]">
        <Link
          href="/admin"
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 dark:bg-[#303134] dark:hover:bg-[#3c4043] text-gray-800 dark:text-gray-200 text-xs font-medium transition-all shadow-sm"
        >
          <Activity className="w-3.5 h-3.5 text-[#4285F4]" />
          <span>Admin &amp; Monitoring</span>
        </Link>

        <Link
          href="/admin"
          className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#303134] text-gray-600 dark:text-gray-300"
          title="NomEngine Admin &amp; Tools"
          aria-label="Apps"
        >
          <Grid className="w-5 h-5" />
        </Link>

        <ThemeToggle />
      </header>

      {/* Main Center Search Area */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 -mt-16 w-full max-w-2xl mx-auto">
        {/* Colorful NomEngine Logo */}
        <div className="mb-7 flex flex-col items-center">
          <Logo width={320} height={92} className="h-20 w-auto" />
        </div>

        {/* Unified Google Search Box with Integrated Dropdown */}
        <div ref={containerRef} className="relative w-full max-w-[584px] z-50">
          <div
            className={`w-full transition-all duration-150 ${
              isOpen && suggestions.length > 0
                ? "bg-white dark:bg-[#303134] rounded-3xl shadow-lg border border-transparent py-1.5"
                : "bg-white dark:bg-[#202124] border border-[#dfe1e5] dark:border-[#5f6368] rounded-full hover:shadow-md hover:border-transparent focus-within:shadow-md focus-within:border-transparent"
            }`}
          >
            {/* Input Row */}
            <div className="h-[46px] flex items-center px-4">
              <Search className="w-5 h-5 text-[#9aa0a6] mr-3 shrink-0" />

              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => {
                  if (suggestions.length > 0) setIsOpen(true);
                }}
                onKeyDown={handleKeyDown}
                placeholder=""
                autoFocus
                className="w-full bg-transparent outline-none text-base text-gray-900 dark:text-white"
              />

              {query && (
                <button
                  type="button"
                  onClick={() => {
                    setQuery("");
                    setSuggestions([]);
                    setIsOpen(false);
                  }}
                  className="p-1 text-[#70757a] dark:text-[#9aa0a6] hover:text-gray-900 dark:hover:text-white mr-1"
                >
                  <X className="w-5 h-5" />
                </button>
              )}

              <button
                type="button"
                onClick={() => handleSearch()}
                className="p-1 text-[#4285F4] hover:opacity-80 transition-opacity shrink-0"
                aria-label="Search"
              >
                <Search className="w-5 h-5" />
              </button>
            </div>

            {/* Seamless Google Dropdown List */}
            {isOpen && suggestions.length > 0 && (
              <div className="pt-1 pb-2">
                <div className="border-t border-[#dfe1e5] dark:border-[#5f6368] mx-3 mb-1" />
                {suggestions.map((suggestion, index) => {
                  const isSelected = index === selectedIndex;
                  return (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => handleSearch(suggestion)}
                      onMouseEnter={() => setSelectedIndex(index)}
                      className={`w-full flex items-center gap-3 px-4 py-2 text-left text-sm text-gray-800 dark:text-gray-200 transition-colors ${
                        isSelected
                          ? "bg-[#f1f3f4] dark:bg-[#3c4043]"
                          : "hover:bg-[#f1f3f4] dark:hover:bg-[#3c4043]"
                      }`}
                    >
                      <Search className="w-4 h-4 text-[#9aa0a6] shrink-0" />
                      <span className="truncate">{suggestion}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-3 mt-7">
          <button
            type="button"
            onClick={() => handleSearch()}
            className="px-4 py-2 rounded-[4px] text-[14px] bg-[#f8f9fa] dark:bg-[#303134] text-[#3c4043] dark:text-[#e8eaed] border border-[#f8f9fa] dark:border-[#303134] hover:border-[#dadce0] dark:hover:border-[#5f6368] hover:shadow-sm transition-all"
          >
            NomEngine Search
          </button>
          <button
            type="button"
            onClick={() => handleSearch("python documentation")}
            className="px-4 py-2 rounded-[4px] text-[14px] bg-[#f8f9fa] dark:bg-[#303134] text-[#3c4043] dark:text-[#e8eaed] border border-[#f8f9fa] dark:border-[#303134] hover:border-[#dadce0] dark:hover:border-[#5f6368] hover:shadow-sm transition-all"
          >
            I&apos;m Feeling Lucky
          </button>
        </div>

        {/* Language Line */}
        <div className="mt-7 text-xs text-[#4d5156] dark:text-[#bdc1c6] flex flex-wrap items-center justify-center gap-1.5">
          <span>NomEngine offered in:</span>
          <button onClick={() => handleSearch("python")} className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline">English</button>
          <span>•</span>
          <button onClick={() => handleSearch("español")} className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline">Español</button>
          <span>•</span>
          <button onClick={() => handleSearch("français")} className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline">Français</button>
          <span>•</span>
          <button onClick={() => handleSearch("deutsch")} className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline">Deutsch</button>
        </div>

        {/* Live Index Pill */}
        {stats && (
          <div className="mt-8 inline-flex items-center gap-3 px-3.5 py-1.5 rounded-full bg-[#f8f9fa] dark:bg-[#303134] border border-[#dadce0] dark:border-[#5f6368] text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">
            <span>{stats.docs.toLocaleString()} Pages Indexed</span>
            <span>•</span>
            <span>{stats.terms.toLocaleString()} Terms in Index</span>
          </div>
        )}
      </main>

      {/* Google-Style 2-Row Footer */}
      <footer className="w-full bg-[#f2f2f2] dark:bg-[#171717] text-[#70757a] dark:text-[#9aa0a6] text-[14px]">
        <div className="px-7 py-3 border-b border-[#dadce0] dark:border-[#3c4043] text-[14px]">
          Web Search Engine • Global
        </div>
        <div className="px-7 py-3 flex flex-col sm:flex-row items-center justify-between gap-3 text-[13px]">
          <div className="flex flex-wrap items-center gap-6">
            <Link href="/admin" className="hover:underline text-[#1a0dab] dark:text-[#8ab4f8] font-medium">
              Admin &amp; Crawler
            </Link>
            <Link href="/search?q=how+search+works" className="hover:underline">
              How Search Works
            </Link>
            <a href="/api/docs" target="_blank" rel="noopener noreferrer" className="hover:underline">
              API Docs
            </a>
          </div>
          <div className="flex flex-wrap items-center gap-6">
            <Link href="/search?q=privacy" className="hover:underline">
              Privacy
            </Link>
            <Link href="/search?q=terms" className="hover:underline">
              Terms
            </Link>
            <Link href="/admin" className="hover:underline">
              Settings
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
