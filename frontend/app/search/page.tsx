"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { SearchBar } from "@/components/SearchBar";
import { FiltersBar, SearchTab } from "@/components/FiltersBar";
import { SearchResultItem } from "@/components/SearchResultItem";
import { ImageResultItem } from "@/components/ImageResultItem";
import { NewsResultItem } from "@/components/NewsResultItem";
import { Pagination } from "@/components/Pagination";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  fetchSearchResults,
  fetchImages,
  fetchNews,
  SearchResponse,
  ImageResultItem as ImageItemType,
  NewsResultItem as NewsItemType,
} from "@/lib/api";
import { Activity, AlertCircle, Info, Loader2, Sparkles } from "lucide-react";

function SearchResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);

  const [activeTab, setActiveTab] = useState<SearchTab>("all");
  const [safeSearch, setSafeSearch] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Results State
  const [webResults, setWebResults] = useState<SearchResponse | null>(null);
  const [imageResults, setImageResults] = useState<ImageItemType[]>([]);
  const [newsResults, setNewsResults] = useState<NewsItemType[]>([]);

  useEffect(() => {
    if (!query) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    if (activeTab === "all") {
      fetchSearchResults(query, page, 10, safeSearch)
        .then((data) => {
          setWebResults(data);
          setLoading(false);
        })
        .catch((err) => {
          setError("Failed to fetch search results from NomEngine backend.");
          setLoading(false);
        });
    } else if (activeTab === "images") {
      fetchImages(query, 24)
        .then((data) => {
          setImageResults(data.results);
          setLoading(false);
        })
        .catch(() => {
          setError("Failed to load image search results.");
          setLoading(false);
        });
    } else if (activeTab === "news") {
      fetchNews(query, 10)
        .then((data) => {
          setNewsResults(data.results);
          setLoading(false);
        })
        .catch(() => {
          setError("Failed to load news search results.");
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [query, page, activeTab, safeSearch]);

  const handleSearchSubmit = (newQuery: string) => {
    router.push(`/search?q=${encodeURIComponent(newQuery)}&page=1`);
  };

  const handlePageChange = (newPage: number) => {
    router.push(`/search?q=${encodeURIComponent(query)}&page=${newPage}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-[#202124]">
      {/* Sticky Header */}
      <header className="sticky top-0 z-40 bg-white/95 dark:bg-[#202124]/95 backdrop-blur-md border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-6 flex-1 max-w-3xl">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 group shrink-0">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-nom-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-nom-500/20 group-hover:scale-105 transition-transform">
                N
              </div>
              <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white hidden sm:inline">
                Nom<span className="text-nom-600 dark:text-nom-400">Engine</span>
              </span>
            </Link>

            {/* Top Search Bar */}
            <div className="w-full">
              <SearchBar initialQuery={query} onSearch={handleSearchSubmit} />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/admin"
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#303134] text-gray-600 dark:text-gray-300 transition-colors"
              title="Admin Dashboard"
            >
              <Activity className="w-5 h-5 text-nom-600 dark:text-nom-400" />
            </Link>
            <ThemeToggle />
          </div>
        </div>

        {/* Tabs & Tools Subheader */}
        <FiltersBar
          activeTab={activeTab}
          onTabChange={setActiveTab}
          safeSearch={safeSearch}
          onSafeSearchToggle={() => setSafeSearch(!safeSearch)}
          tookMs={webResults?.took_ms}
          totalResults={webResults?.total}
        />
      </header>

      {/* Main Results Container */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-6 w-full">
        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-gray-500 dark:text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin text-nom-600 dark:text-nom-400" />
            <p className="text-sm">Searching the indexed web...</p>
          </div>
        )}

        {!loading && error && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 my-8">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {!loading && !error && !query && (
          <div className="text-center py-20 text-gray-500">
            <p>Please enter a search query above.</p>
          </div>
        )}

        {/* Tab 1: All (Standard Web Results) */}
        {!loading && !error && activeTab === "all" && webResults && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left Results Column */}
            <div className="lg:col-span-8 flex flex-col gap-6">
              {webResults.results.length === 0 ? (
                <div className="py-12">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    No results found for &ldquo;{query}&rdquo;
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    Suggestions:
                  </p>
                  <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400 mt-2 space-y-1">
                    <li>Make sure all words are spelled correctly.</li>
                    <li>Try different keywords or broader search terms.</li>
                    <li>
                      Crawl more seed domains in the{" "}
                      <Link href="/admin" className="text-nom-600 dark:text-nom-400 underline">
                        Admin Dashboard
                      </Link>
                      .
                    </li>
                  </ul>
                </div>
              ) : (
                <>
                  {webResults.results.map((item) => (
                    <SearchResultItem key={item.id} result={item} />
                  ))}

                  <Pagination
                    currentPage={page}
                    totalResults={webResults.total}
                    pageSize={10}
                    onPageChange={handlePageChange}
                  />
                </>
              )}
            </div>

            {/* Right Information & Query Details Panel */}
            <aside className="lg:col-span-4 flex flex-col gap-4">
              <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-700/80 bg-gray-50/50 dark:bg-[#303134]/40 flex flex-col gap-3">
                <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                  <Sparkles className="w-4 h-4 text-nom-600 dark:text-nom-400" />
                  <span>Search Knowledge &amp; Filters</span>
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-300 space-y-2">
                  <p>
                    <span className="font-semibold">Query:</span> {query}
                  </p>
                  <p>
                    <span className="font-semibold">Total Matches:</span> {webResults.total}
                  </p>
                  <p>
                    <span className="font-semibold">Execution Latency:</span> {webResults.took_ms} ms
                  </p>
                </div>
                <div className="pt-2 border-t border-gray-200 dark:border-gray-700 text-[11px] text-gray-500 dark:text-gray-400">
                  Ranked via BM25 + PageRank graph calculations.
                </div>
              </div>
            </aside>
          </div>
        )}

        {/* Tab 2: Images */}
        {!loading && !error && activeTab === "images" && (
          <div>
            {imageResults.length === 0 ? (
              <p className="text-gray-500 py-12">No images found for this query.</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {imageResults.map((img) => (
                  <ImageResultItem key={img.id} image={img} />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: News */}
        {!loading && !error && activeTab === "news" && (
          <div className="flex flex-col gap-4">
            {newsResults.length === 0 ? (
              <p className="text-gray-500 py-12">No recent news articles found.</p>
            ) : (
              newsResults.map((news) => (
                <NewsResultItem key={news.id} news={news} />
              ))
            )}
          </div>
        )}

        {/* Tab 4: Videos */}
        {!loading && !error && activeTab === "videos" && (
          <div className="py-12 text-center text-gray-500">
            <p>Video indexing is enabled. No video feeds crawled for this query yet.</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function SearchResultsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-white dark:bg-[#202124]">
          <div className="w-8 h-8 rounded-full border-2 border-nom-600 border-t-transparent animate-spin" />
        </div>
      }
    >
      <SearchResultsContent />
    </Suspense>
  );
}
