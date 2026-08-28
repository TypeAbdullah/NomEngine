"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Clock, Search, TrendingUp, X } from "lucide-react";
import { fetchSuggestions } from "@/lib/api";

interface SearchBarProps {
  initialQuery?: string;
  size?: "default" | "large";
  autoFocus?: boolean;
  onSearch?: (q: string) => void;
}

export function SearchBar({
  initialQuery = "",
  size = "default",
  autoFocus = false,
  onSearch,
}: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Sync initial query if changed
  useEffect(() => {
    setQuery(initialQuery);
  }, [initialQuery]);

  // Global '/' keyboard shortcut to focus search input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        e.key === "/" &&
        document.activeElement !== inputRef.current &&
        !["INPUT", "TEXTAREA"].includes((document.activeElement as HTMLElement)?.tagName)
      ) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Debounced autocomplete suggestions
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

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (searchQuery: string) => {
    const clean = searchQuery.trim();
    if (!clean) return;
    setIsOpen(false);
    if (onSearch) {
      onSearch(clean);
    } else {
      router.push(`/search?q=${encodeURIComponent(clean)}`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!isOpen && suggestions.length > 0) {
        setIsOpen(true);
        return;
      }
      setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSubmit(suggestions[selectedIndex]);
      } else {
        handleSubmit(query);
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const isLarge = size === "large";

  return (
    <div ref={containerRef} className="relative w-full max-w-2xl">
      <div
        className={`flex items-center w-full bg-white dark:bg-[#202124] border border-gray-200 dark:border-[#5f6368] rounded-full hover:shadow-md focus-within:shadow-md focus-within:border-nom-500 dark:focus-within:border-nom-400 transition-all ${
          isLarge ? "px-5 py-3.5 shadow-sm" : "px-4 py-2"
        }`}
      >
        <Search className={`${isLarge ? "w-5 h-5" : "w-4 h-4"} text-gray-400 dark:text-gray-400 mr-3 shrink-0`} />

        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (suggestions.length > 0) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Search documents, topics, code, or enter site:..."
          autoFocus={autoFocus}
          className="w-full bg-transparent outline-none text-gray-900 dark:text-white placeholder-gray-400 text-base"
        />

        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery("");
              setSuggestions([]);
              setIsOpen(false);
              inputRef.current?.focus();
            }}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 mr-1"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        <button
          type="button"
          onClick={() => handleSubmit(query)}
          aria-label="Submit search"
          className="p-1.5 rounded-full text-nom-600 dark:text-nom-400 hover:bg-nom-50 dark:hover:bg-[#303134] transition-colors"
        >
          <Search className="w-4 h-4" />
        </button>
      </div>

      {/* Autocomplete Suggestions Dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-[#303134] border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xl overflow-hidden z-50 py-2 animate-in fade-in duration-100">
          {suggestions.map((suggestion, index) => {
            const isSelected = index === selectedIndex;
            return (
              <button
                key={suggestion}
                type="button"
                onClick={() => handleSubmit(suggestion)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`w-full flex items-center gap-3 px-5 py-2.5 text-left text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-[#3c4043] transition-colors ${
                  isSelected ? "bg-gray-100 dark:bg-[#3c4043]" : ""
                }`}
              >
                <Search className="w-4 h-4 text-gray-400" />
                <span className="truncate">{suggestion}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
