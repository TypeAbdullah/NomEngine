"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { SearchBar } from "@/components/SearchBar";
import { fetchAdminStats } from "@/lib/api";
import { Sparkles, Terminal, Cpu, Database, Zap } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [stats, setStats] = useState<{ docs: number; terms: number } | null>(null);

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

  const sampleQueries = [
    "Python documentation",
    '"web framework"',
    "site:python.org release",
    "machine learning tutorial",
    "FastAPI async",
  ];

  const handleFeelingLucky = () => {
    router.push("/search?q=Python+documentation");
  };

  return (
    <div className="min-h-screen flex flex-col justify-between bg-white dark:bg-[#202124]">
      <Navbar showSearch={false} />

      {/* Main Search Center */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 -mt-16 text-center">
        {/* Brand Logo */}
        <div className="flex flex-col items-center gap-3 mb-8">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-nom-600 via-indigo-600 to-cyan-400 flex items-center justify-center text-white font-extrabold text-3xl shadow-xl shadow-nom-500/25 animate-pulse">
              N
            </div>
            <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-gray-900 dark:text-white">
              Nom<span className="text-nom-600 dark:text-nom-400">Engine</span>
            </h1>
          </div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            <span>Independent Web Search Engine</span>
            <span>•</span>
            <span className="text-nom-600 dark:text-nom-400">Built From Scratch</span>
          </p>
        </div>

        {/* Search Bar */}
        <SearchBar size="large" autoFocus={true} />

        {/* Search Buttons */}
        <div className="flex items-center gap-3 mt-8">
          <button
            onClick={() => {
              const input = document.querySelector('input[type="text"]') as HTMLInputElement;
              if (input && input.value.trim()) {
                router.push(`/search?q=${encodeURIComponent(input.value.trim())}`);
              }
            }}
            className="px-5 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-[#303134] text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-[#3c4043] border border-transparent dark:border-transparent transition-all shadow-sm"
          >
            Nom Search
          </button>
          <button
            onClick={handleFeelingLucky}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-[#303134] text-gray-800 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-[#3c4043] border border-transparent dark:border-transparent transition-all shadow-sm"
          >
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>I&apos;m Feeling Lucky</span>
          </button>
        </div>

        {/* Quick Sample Queries */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-8 max-w-xl">
          <span className="text-xs text-gray-400 mr-1">Trending:</span>
          {sampleQueries.map((sample) => (
            <button
              key={sample}
              onClick={() => router.push(`/search?q=${encodeURIComponent(sample)}`)}
              className="px-3 py-1 rounded-full text-xs bg-gray-50 dark:bg-[#303134] text-gray-600 dark:text-gray-300 hover:text-nom-600 dark:hover:text-nom-400 hover:border-nom-300 border border-gray-200 dark:border-gray-700 transition-all"
            >
              {sample}
            </button>
          ))}
        </div>

        {/* Live Index Status */}
        {stats && (
          <div className="mt-12 inline-flex items-center gap-4 px-4 py-2 rounded-full bg-nom-50/60 dark:bg-nom-950/30 border border-nom-200/50 dark:border-nom-800/40 text-xs text-nom-800 dark:text-nom-200">
            <span className="flex items-center gap-1.5 font-semibold">
              <Database className="w-3.5 h-3.5 text-nom-600 dark:text-nom-400" />
              {stats.docs.toLocaleString()} Pages Indexed
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              {stats.terms.toLocaleString()} Unique Terms
            </span>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-gray-100 dark:border-gray-800/60 px-6 py-4 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 dark:text-gray-400 gap-2">
        <div className="flex items-center gap-4">
          <span>NomEngine Architecture: BM25 + PageRank + Positional Inverted Index</span>
        </div>
        <div className="flex items-center gap-3">
          <span>Press <kbd className="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 font-mono text-[10px] text-gray-800 dark:text-gray-200">/</kbd> to search</span>
          <span>•</span>
          <a href="/api/docs" target="_blank" className="hover:underline text-nom-600 dark:text-nom-400">
            OpenAPI Docs
          </a>
        </div>
      </footer>
    </div>
  );
}
