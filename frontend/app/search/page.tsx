"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  fetchSearchResults,
  fetchImages,
  fetchNews,
  fetchSuggestions,
  SearchResponse,
  ImageResultItem as ImageItemType,
  NewsResultItem as NewsItemType,
} from "@/lib/api";
import {
  Activity,
  AlertCircle,
  Camera,
  ChevronLeft,
  ChevronRight,
  Globe,
  Grid,
  Image as ImageIcon,
  Loader2,
  Mic,
  MoreVertical,
  Newspaper,
  Search,
  SlidersHorizontal,
  Video,
  X,
} from "lucide-react";

type SearchTab = "all" | "images" | "news" | "videos";

function SearchResultsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawQuery = searchParams.get("q") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);

  const [inputQuery, setInputQuery] = useState(rawQuery);
  const [activeTab, setActiveTab] = useState<SearchTab>("all");
  const [safeSearch, setSafeSearch] = useState<boolean>(true);
  const [showTools, setShowTools] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isSuggestOpen, setIsSuggestOpen] = useState(false);

  const [webResults, setWebResults] = useState<SearchResponse | null>(null);
  const [imageResults, setImageResults] = useState<ImageItemType[]>([]);
  const [newsResults, setNewsResults] = useState<NewsItemType[]>([]);

  useEffect(() => {
    setInputQuery(rawQuery);
  }, [rawQuery]);

  useEffect(() => {
    if (!rawQuery) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    if (activeTab === "all") {
      fetchSearchResults(rawQuery, page, 10, safeSearch)
        .then((data) => {
          setWebResults(data);
          setLoading(false);
        })
        .catch(() => {
          setError("Failed to fetch search results from NomEngine backend.");
          setLoading(false);
        });
    } else if (activeTab === "images") {
      fetchImages(rawQuery, 24)
        .then((data) => {
          setImageResults(data.results);
          setLoading(false);
        })
        .catch(() => {
          setError("Failed to load image search results.");
          setLoading(false);
        });
    } else if (activeTab === "news") {
      fetchNews(rawQuery, 10)
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
  }, [rawQuery, page, activeTab, safeSearch]);

  const handleSearchSubmit = (newQuery: string) => {
    const clean = newQuery.trim();
    if (!clean) return;
    setIsSuggestOpen(false);
    router.push(`/search?q=${encodeURIComponent(clean)}&page=1`);
  };

  const handlePageChange = (newPage: number) => {
    router.push(`/search?q=${encodeURIComponent(rawQuery)}&page=${newPage}`);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const tabs = [
    { id: "all" as SearchTab, label: "All", icon: Search },
    { id: "images" as SearchTab, label: "Images", icon: ImageIcon },
    { id: "videos" as SearchTab, label: "Videos", icon: Video },
    { id: "news" as SearchTab, label: "News", icon: Newspaper },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-[#202124] text-[#1f1f1f] dark:text-[#e8eaed] font-sans antialiased">
      {/* Sticky Google Header */}
      <header className="sticky top-0 z-40 bg-white dark:bg-[#202124] border-b border-[#ebebeb] dark:border-[#3c4043]">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 pt-5 pb-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-6 flex-1 max-w-3xl">
            {/* Logo */}
            <Link href="/" className="shrink-0">
              <Logo width={120} height={36} className="h-8 w-auto" />
            </Link>

            {/* Google Search Bar in Header */}
            <div className="relative w-full">
              <div className="flex items-center w-full bg-white dark:bg-[#202124] border border-[#dfe1e5] dark:border-[#5f6368] rounded-full shadow-sm hover:shadow-md focus-within:shadow-md px-4 py-2.5 transition-all">
                <input
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleSearchSubmit(inputQuery);
                  }}
                  className="w-full bg-transparent outline-none text-[15px] text-gray-900 dark:text-white"
                />

                {inputQuery && (
                  <button
                    type="button"
                    onClick={() => setInputQuery("")}
                    className="p-1 text-[#70757a] hover:text-gray-900 dark:hover:text-white mr-2 border-r border-[#dfe1e5] dark:border-[#5f6368] pr-2"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}

                <div className="flex items-center gap-1.5 shrink-0 pl-1 text-[#4285F4]">
                  <button
                    type="button"
                    onClick={() => handleSearchSubmit(inputQuery)}
                    className="p-1 hover:opacity-80"
                    aria-label="Search"
                  >
                    <Search className="w-4 h-4 text-[#4285F4]" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/admin"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#f8f9fa] hover:bg-[#e8eaed] dark:bg-[#303134] dark:hover:bg-[#3c4043] text-xs font-medium text-[#3c4043] dark:text-[#e8eaed] transition-colors"
            >
              <Activity className="w-3.5 h-3.5 text-[#4285F4]" />
              <span className="hidden sm:inline">Admin &amp; Crawler</span>
            </Link>
            <ThemeToggle />
          </div>
        </div>

        {/* Google Tabs Subheader */}
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 flex items-center justify-between text-[13px] border-t border-transparent">
          <div className="flex items-center gap-1 sm:pl-[144px] overflow-x-auto scrollbar-none">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-3 border-b-[3px] font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? "border-[#1a73e8] text-[#1a73e8] dark:border-[#8ab4f8] dark:text-[#8ab4f8]"
                      : "border-transparent text-[#70757a] dark:text-[#9aa0a6] hover:text-[#202124] dark:hover:text-white"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}

            <button
              onClick={() => setShowTools(!showTools)}
              className={`flex items-center gap-1.5 px-3 py-3 border-b-[3px] border-transparent font-medium text-[#70757a] dark:text-[#9aa0a6] hover:text-[#202124] dark:hover:text-white transition-colors`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Tools</span>
            </button>
          </div>
        </div>

        {/* Tools bar */}
        {showTools && (
          <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-2 sm:pl-[144px] flex items-center gap-4 text-xs text-[#70757a] dark:text-[#9aa0a6] border-t border-[#ebebeb] dark:border-[#3c4043] bg-[#fafafa] dark:bg-[#1a1a1a]">
            <button
              onClick={() => setSafeSearch(!safeSearch)}
              className="hover:text-gray-900 dark:hover:text-white font-medium"
            >
              SafeSearch: <span className="font-semibold">{safeSearch ? "On" : "Off"}</span>
            </button>
            <span>•</span>
            <span>Any time</span>
            <span>•</span>
            <span>All results</span>
          </div>
        )}
      </header>

      {/* Main Results Container */}
      <main className="flex-1 max-w-[1280px] mx-auto px-4 sm:px-6 py-3 w-full sm:pl-[168px]">
        {/* Result Stats Line */}
        {webResults && !loading && (
          <div className="text-[14px] text-[#70757a] dark:text-[#9aa0a6] mb-5">
            About {webResults.total.toLocaleString()} results ({(webResults.took_ms / 1000).toFixed(2)} seconds)
          </div>
        )}

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-[#70757a]">
            <Loader2 className="w-8 h-8 animate-spin text-[#4285F4]" />
            <p className="text-sm">Searching the indexed web...</p>
          </div>
        )}

        {!loading && error && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 my-4 max-w-xl">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* Tab 1: All Web Results */}
        {!loading && !error && activeTab === "all" && webResults && (
          <div className="flex flex-col gap-7 max-w-[652px]">
            {webResults.results.length === 0 ? (
              <div className="py-8">
                <h3 className="text-lg text-[#202124] dark:text-white">
                  Your search - <b>{rawQuery}</b> - did not match any documents.
                </h3>
                <p className="text-sm text-[#4d5156] dark:text-[#bdc1c6] mt-4">Suggestions:</p>
                <ul className="list-disc list-inside text-sm text-[#4d5156] dark:text-[#bdc1c6] mt-2 space-y-1.5">
                  <li>Make sure all words are spelled correctly.</li>
                  <li>Try different keywords or broader terms.</li>
                  <li>
                    Crawl more URLs in the{" "}
                    <Link href="/admin" className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline">
                      Admin Dashboard
                    </Link>
                    .
                  </li>
                </ul>
              </div>
            ) : (
              <>
                {webResults.results.map((item) => {
                  const domain = item.display_url.split("/")[0];
                  return (
                    <article key={item.id} className="flex flex-col group">
                      {/* URL & Site info */}
                      <div className="flex items-center gap-3 mb-1">
                        <div className="w-7 h-7 rounded-full bg-[#f1f3f4] dark:bg-[#303134] flex items-center justify-center text-[#5f6368] dark:text-[#9aa0a6] shrink-0 text-xs">
                          <Globe className="w-4 h-4" />
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[14px] leading-tight text-[#202124] dark:text-[#dadce0] font-normal">
                            {domain}
                          </span>
                          <span className="text-[12px] text-[#4d5156] dark:text-[#bdc1c6] truncate max-w-lg">
                            {item.url}
                          </span>
                        </div>
                      </div>

                      {/* Title */}
                      <h2 className="text-[20px] leading-[26px] font-normal mt-0.5">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline visited:text-[#609] dark:visited:text-[#c58af9]"
                        >
                          {item.title}
                        </a>
                      </h2>

                      {/* Highlighted Snippet */}
                      <p
                        className="text-[14px] leading-[22px] text-[#4d5156] dark:text-[#bdc1c6] mt-1"
                        dangerouslySetInnerHTML={{ __html: item.snippet || item.description }}
                      />
                    </article>
                  );
                })}

                {/* Google-Style Pagination */}
                <div className="flex items-center gap-3 my-10 text-[14px] text-[#1a0dab] dark:text-[#8ab4f8]">
                  {page > 1 && (
                    <button
                      onClick={() => handlePageChange(page - 1)}
                      className="flex items-center gap-1 hover:underline"
                    >
                      <ChevronLeft className="w-4 h-4" />
                      <span>Previous</span>
                    </button>
                  )}

                  {Array.from({ length: Math.min(6, Math.ceil(webResults.total / 10)) }, (_, i) => i + 1).map((p) => (
                    <button
                      key={p}
                      onClick={() => handlePageChange(p)}
                      className={`w-8 h-8 rounded-full flex items-center justify-center font-medium ${
                        p === page
                          ? "bg-[#e8f0fe] dark:bg-[#303134] text-[#1a73e8] dark:text-[#8ab4f8] font-bold"
                          : "hover:underline text-[#70757a] dark:text-[#9aa0a6]"
                      }`}
                    >
                      {p}
                    </button>
                  ))}

                  {page < Math.ceil(webResults.total / 10) && (
                    <button
                      onClick={() => handlePageChange(page + 1)}
                      className="flex items-center gap-1 hover:underline"
                    >
                      <span>Next</span>
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </>
            )}
          </div>
        )}

        {/* Tab 2: Images */}
        {!loading && !error && activeTab === "images" && (
          <div>
            {imageResults.length === 0 ? (
              <p className="text-[#70757a] py-8">No images found for &ldquo;{rawQuery}&rdquo;.</p>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {imageResults.map((img) => (
                  <a
                    key={img.id}
                    href={img.page_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex flex-col rounded-xl overflow-hidden bg-gray-50 dark:bg-[#303134] border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all group"
                  >
                    <div className="aspect-square bg-gray-200 dark:bg-gray-800 overflow-hidden">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={img.image_url}
                        alt={img.alt_text || "Result image"}
                        loading="lazy"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    </div>
                    <div className="p-2 text-[12px] truncate text-gray-800 dark:text-gray-200">
                      {img.alt_text || img.title || "Image"}
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: News */}
        {!loading && !error && activeTab === "news" && (
          <div className="flex flex-col gap-4 max-w-[652px]">
            {newsResults.length === 0 ? (
              <p className="text-[#70757a] py-8">No news articles found for &ldquo;{rawQuery}&rdquo;.</p>
            ) : (
              newsResults.map((news) => (
                <article key={news.id} className="p-4 rounded-xl border border-[#dfe1e5] dark:border-[#3c4043] bg-white dark:bg-[#202124]">
                  <div className="text-xs text-[#70757a] mb-1">
                    {news.publisher || "Publisher"} • {news.published_date ? new Date(news.published_date).toLocaleDateString() : "Recent"}
                  </div>
                  <h3 className="text-[18px] leading-snug font-normal">
                    <a href={news.url} target="_blank" rel="noopener noreferrer" className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline">
                      {news.headline}
                    </a>
                  </h3>
                  <p className="text-[13px] text-[#4d5156] dark:text-[#bdc1c6] mt-1.5">
                    {news.snippet}
                  </p>
                </article>
              ))
            )}
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
          <div className="w-8 h-8 rounded-full border-2 border-[#4285F4] border-t-transparent animate-spin" />
        </div>
      }
    >
      <SearchResultsContent />
    </Suspense>
  );
}
