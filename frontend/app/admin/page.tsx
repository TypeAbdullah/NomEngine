"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import {
  fetchAdminStats,
  fetchRankingWeights,
  updateRankingWeights,
  triggerCrawl,
  pauseCrawler,
  resumeCrawler,
  triggerReindex,
  triggerPageRank,
  fetchCrawlActivity,
  AdminStats,
  RankingWeights,
  CrawlActivityItem,
} from "@/lib/api";
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Database,
  Globe,
  Layers,
  Link as LinkIcon,
  Pause,
  Play,
  Radio,
  RefreshCw,
  Search,
  Sliders,
  Terminal,
  Zap,
} from "lucide-react";

type AdminTab = "crawler" | "live_process" | "ranking" | "stats";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<AdminTab>("crawler");
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [liveActivity, setLiveActivity] = useState<CrawlActivityItem[]>([]);
  const [weights, setWeights] = useState<RankingWeights>({
    w_bm25: 0.4,
    w_title: 0.25,
    w_phrase: 0.15,
    w_pagerank: 0.1,
    w_freshness: 0.05,
    w_quality: 0.05,
    p_spam: 0.5,
  });

  const [seedInput, setSeedInput] = useState<string>(
    "https://docs.python.org/3/\nhttps://vercel.com\nhttps://www.djangoproject.com/"
  );
  const [concurrency, setConcurrency] = useState<number>(5);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = () => {
    fetchAdminStats().then(setStats).catch(() => {});
    fetchRankingWeights().then(setWeights).catch(() => {});
    fetchCrawlActivity()
      .then((res) => {
        if (res.activity) setLiveActivity(res.activity);
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleStartCrawl = async () => {
    const urls = seedInput
      .split("\n")
      .map((u) => u.trim())
      .filter((u) => u.length > 0 && !u.startsWith("#"));

    if (urls.length === 0) return;

    setLoadingAction("crawl");
    try {
      const res = await triggerCrawl(urls, concurrency);
      setStatusMessage(res.message || "Crawler started!");
      setActiveTab("live_process");
      loadData();
    } catch (err: any) {
      setStatusMessage("Failed to start crawler: " + err.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handlePauseResume = async () => {
    setLoadingAction("pause");
    try {
      if (stats?.crawler_is_paused) {
        await resumeCrawler();
        setStatusMessage("Crawler resumed.");
      } else {
        await pauseCrawler();
        setStatusMessage("Crawler paused.");
      }
      loadData();
    } catch (err: any) {
      setStatusMessage("Error: " + err.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleReindex = async () => {
    setLoadingAction("reindex");
    try {
      const res = await triggerReindex();
      setStatusMessage(res.message || "Reindexing complete!");
      loadData();
    } catch (err: any) {
      setStatusMessage("Reindexing failed: " + err.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handlePageRank = async () => {
    setLoadingAction("pagerank");
    try {
      const res = await triggerPageRank();
      setStatusMessage(res.message || "PageRank updated!");
      loadData();
    } catch (err: any) {
      setStatusMessage("PageRank update failed: " + err.message);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleSaveWeights = async () => {
    setLoadingAction("weights");
    try {
      await updateRankingWeights(weights);
      setStatusMessage("Ranking weights updated in real time!");
    } catch (err: any) {
      setStatusMessage("Failed to update weights: " + err.message);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8f9fa] dark:bg-[#18191a] text-[#202124] dark:text-[#e8eaed] font-sans antialiased">
      {/* Header */}
      <header className="w-full bg-white dark:bg-[#242526] border-b border-[#dadce0] dark:border-[#3c4043] px-6 py-3 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2">
            <Logo width={120} height={36} className="h-7 w-auto" />
          </Link>
          <span className="text-xs px-2.5 py-0.5 rounded-md bg-[#e8f0fe] dark:bg-[#303134] text-[#1a73e8] dark:text-[#8ab4f8] font-semibold uppercase tracking-wider">
            Admin Console
          </span>
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-1 text-xs text-[#1a73e8] dark:text-[#8ab4f8] hover:underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Search</span>
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-6 w-full flex flex-col gap-6">
        {/* Top Status Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] shadow-sm">
          <div>
            <h1 className="text-xl font-semibold">Search Engine Control &amp; Operations</h1>
            <p className="text-xs text-[#5f6368] dark:text-[#9aa0a6] mt-0.5">
              Live crawler management, real-time activity stream, and ranking weights tuner.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#f1f3f4] dark:bg-[#303134]">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  stats?.crawler_is_running
                    ? stats?.crawler_is_paused
                      ? "bg-amber-500"
                      : "bg-[#34A853] animate-ping"
                    : "bg-gray-400"
                }`}
              />
              <span className="text-xs font-medium">
                {stats?.crawler_is_running
                  ? stats?.crawler_is_paused
                    ? "Crawler Paused"
                    : "Crawler Running"
                  : "Crawler Idle"}
              </span>
            </div>

            {stats?.crawler_is_running && (
              <button
                onClick={handlePauseResume}
                disabled={loadingAction === "pause"}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#dadce0] dark:border-[#5f6368] text-xs font-medium hover:bg-gray-100 dark:hover:bg-[#303134] transition-colors"
              >
                {stats.crawler_is_paused ? (
                  <>
                    <Play className="w-3.5 h-3.5 text-[#34A853]" />
                    <span>Resume</span>
                  </>
                ) : (
                  <>
                    <Pause className="w-3.5 h-3.5 text-[#EA4335]" />
                    <span>Pause</span>
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {/* Status Toast */}
        {statusMessage && (
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-[#e8f0fe] dark:bg-[#1f2937] border border-[#d2e3fc] dark:border-[#374151] text-[#1a73e8] dark:text-[#93c5fd] text-xs">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{statusMessage}</span>
            </div>
            <button onClick={() => setStatusMessage(null)} className="font-semibold hover:underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3.5 rounded-xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-1">
            <span className="text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">Indexed Pages</span>
            <span className="text-xl font-bold text-[#4285F4]">
              {stats?.pages_indexed.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-1">
            <span className="text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">Pages Crawled</span>
            <span className="text-xl font-bold text-[#34A853]">
              {stats?.pages_crawled.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-1">
            <span className="text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">Queue Size</span>
            <span className="text-xl font-bold text-[#FBBC05]">
              {stats?.frontier_queue_size.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-1">
            <span className="text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">Index Terms</span>
            <span className="text-xl font-bold text-[#EA4335]">
              {stats?.unique_terms_in_index.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-1">
            <span className="text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">Graph Links</span>
            <span className="text-xl font-bold text-[#1a73e8]">
              {stats?.total_links_graph.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-1">
            <span className="text-[11px] text-[#5f6368] dark:text-[#9aa0a6]">Searches Run</span>
            <span className="text-xl font-bold text-[#9333ea]">
              {stats?.searches_recorded.toLocaleString() ?? 0}
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-[#dadce0] dark:border-[#3c4043] pb-1">
          <button
            onClick={() => setActiveTab("crawler")}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === "crawler"
                ? "bg-[#1a73e8] text-white"
                : "text-[#5f6368] dark:text-[#9aa0a6] hover:bg-gray-100 dark:hover:bg-[#303134]"
            }`}
          >
            <Globe className="w-4 h-4" />
            <span>Crawl Seed Manager</span>
          </button>

          <button
            onClick={() => setActiveTab("live_process")}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === "live_process"
                ? "bg-[#1a73e8] text-white"
                : "text-[#5f6368] dark:text-[#9aa0a6] hover:bg-gray-100 dark:hover:bg-[#303134]"
            }`}
          >
            <Radio className="w-4 h-4 text-[#34A853]" />
            <span>Live Crawl Process ({liveActivity.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("ranking")}
            className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors ${
              activeTab === "ranking"
                ? "bg-[#1a73e8] text-white"
                : "text-[#5f6368] dark:text-[#9aa0a6] hover:bg-gray-100 dark:hover:bg-[#303134]"
            }`}
          >
            <Sliders className="w-4 h-4" />
            <span>Ranking Weights Tuner</span>
          </button>
        </div>

        {/* TAB 1: CRAWL SEED MANAGER */}
        {activeTab === "crawler" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-7 p-6 rounded-2xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] flex flex-col gap-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-sm">Add URLs to Crawl</h2>
                <span className="text-xs text-[#5f6368] dark:text-[#9aa0a6]">One URL per line</span>
              </div>

              <textarea
                rows={5}
                value={seedInput}
                onChange={(e) => setSeedInput(e.target.value)}
                className="w-full p-3 rounded-xl border border-[#dadce0] dark:border-[#5f6368] bg-[#f8f9fa] dark:bg-[#18191a] text-xs font-mono outline-none focus:border-[#1a73e8]"
                placeholder="https://example.com"
              />

              <div className="flex items-center justify-between text-xs">
                <span className="text-[#5f6368] dark:text-[#9aa0a6]">Worker Concurrency: {concurrency}</span>
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={concurrency}
                  onChange={(e) => setConcurrency(parseInt(e.target.value, 10))}
                  className="w-48 accent-[#1a73e8]"
                />
              </div>

              <button
                onClick={handleStartCrawl}
                disabled={loadingAction === "crawl"}
                className="flex items-center justify-center gap-2 py-2.5 rounded-xl bg-[#1a73e8] hover:bg-[#1557b0] text-white font-medium text-xs shadow-sm transition-all"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>Start Crawling</span>
              </button>
            </div>

            <div className="lg:col-span-5 flex flex-col gap-4">
              <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] shadow-sm flex flex-col gap-3">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-[#1a73e8]" />
                  <span>Index &amp; PageRank Actions</span>
                </h3>

                <button
                  onClick={handleReindex}
                  disabled={loadingAction === "reindex"}
                  className="w-full py-2.5 px-3 rounded-xl border border-[#dadce0] dark:border-[#5f6368] hover:bg-gray-50 dark:hover:bg-[#303134] text-xs font-medium text-left flex justify-between items-center transition-colors"
                >
                  <span>Re-Index All Crawled Pages</span>
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={handlePageRank}
                  disabled={loadingAction === "pagerank"}
                  className="w-full py-2.5 px-3 rounded-xl border border-[#dadce0] dark:border-[#5f6368] hover:bg-gray-50 dark:hover:bg-[#303134] text-xs font-medium text-left flex justify-between items-center transition-colors"
                >
                  <span>Recompute PageRank Link Graph</span>
                  <LinkIcon className="w-3.5 h-3.5" />
                </button>
              </div>

              {stats && stats.top_domains.length > 0 && (
                <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] shadow-sm">
                  <h3 className="font-semibold text-xs mb-2">Top Indexed Domains</h3>
                  <div className="space-y-1.5 text-xs">
                    {stats.top_domains.map((d) => (
                      <div key={d.domain} className="flex justify-between py-1 border-b border-gray-100 dark:border-gray-800">
                        <span className="font-mono truncate max-w-[200px]">{d.domain}</span>
                        <span className="font-semibold text-[#1a73e8]">{d.count} docs</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: LIVE CRAWL PROCESS TAB */}
        {activeTab === "live_process" && (
          <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] shadow-sm flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-[#34A853] animate-pulse" />
                <h2 className="font-semibold text-sm">Real-Time Crawl Stream &amp; Process Log</h2>
              </div>
              <span className="text-xs text-[#5f6368] dark:text-[#9aa0a6]">Auto-refreshes every 2s</span>
            </div>

            {liveActivity.length === 0 ? (
              <div className="py-12 text-center text-xs text-[#5f6368] dark:text-[#9aa0a6]">
                <p>No active crawl events yet.</p>
                <p className="mt-1">Add a seed URL in the Seed Manager to start live crawling.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[#dadce0] dark:border-[#3c4043] text-[#5f6368] dark:text-[#9aa0a6]">
                      <th className="py-2.5 px-3">Time</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3">URL</th>
                      <th className="py-2.5 px-3">Title / Error</th>
                      <th className="py-2.5 px-3">Words</th>
                      <th className="py-2.5 px-3">Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {liveActivity.map((item, idx) => (
                      <tr
                        key={idx}
                        className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-[#303134] transition-colors font-mono"
                      >
                        <td className="py-2 px-3 text-[#5f6368] dark:text-[#9aa0a6]">{item.timestamp}</td>
                        <td className="py-2 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              item.status === "success"
                                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400"
                                : "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-400"
                            }`}
                          >
                            {item.status}
                          </span>
                        </td>
                        <td className="py-2 px-3 max-w-[280px] truncate font-sans text-[#1a73e8] dark:text-[#8ab4f8]">
                          <a href={item.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                            {item.url}
                          </a>
                        </td>
                        <td className="py-2 px-3 max-w-[240px] truncate text-[#202124] dark:text-[#e8eaed] font-sans">
                          {item.title || item.error || "—"}
                        </td>
                        <td className="py-2 px-3">{item.word_count?.toLocaleString() || "0"}</td>
                        <td className="py-2 px-3">{item.latency_ms} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: RANKING FORMULA TUNER */}
        {activeTab === "ranking" && (
          <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-[#dadce0] dark:border-[#3c4043] shadow-sm flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-sm">Relevance Scoring Signals</h2>
              <button
                onClick={handleSaveWeights}
                disabled={loadingAction === "weights"}
                className="px-4 py-1.5 rounded-lg bg-[#1a73e8] hover:bg-[#1557b0] text-white text-xs font-semibold shadow-sm transition-all"
              >
                Save Weights
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 pt-2">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>BM25 Lexical Weight ({weights.w_bm25})</span>
                  <span className="text-[#5f6368]">Default: 0.40</span>
                </div>
                <input
                  type="range"
                  min={0.0}
                  max={1.5}
                  step={0.05}
                  value={weights.w_bm25}
                  onChange={(e) => setWeights({ ...weights, w_bm25: parseFloat(e.target.value) })}
                  className="w-full accent-[#1a73e8]"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Title Match Bonus ({weights.w_title})</span>
                  <span className="text-[#5f6368]">Default: 0.25</span>
                </div>
                <input
                  type="range"
                  min={0.0}
                  max={1.5}
                  step={0.05}
                  value={weights.w_title}
                  onChange={(e) => setWeights({ ...weights, w_title: parseFloat(e.target.value) })}
                  className="w-full accent-[#1a73e8]"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Exact Phrase Match ({weights.w_phrase})</span>
                  <span className="text-[#5f6368]">Default: 0.15</span>
                </div>
                <input
                  type="range"
                  min={0.0}
                  max={1.5}
                  step={0.05}
                  value={weights.w_phrase}
                  onChange={(e) => setWeights({ ...weights, w_phrase: parseFloat(e.target.value) })}
                  className="w-full accent-[#1a73e8]"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>PageRank Link Authority ({weights.w_pagerank})</span>
                  <span className="text-[#5f6368]">Default: 0.10</span>
                </div>
                <input
                  type="range"
                  min={0.0}
                  max={1.5}
                  step={0.05}
                  value={weights.w_pagerank}
                  onChange={(e) => setWeights({ ...weights, w_pagerank: parseFloat(e.target.value) })}
                  className="w-full accent-[#1a73e8]"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Freshness Bonus ({weights.w_freshness})</span>
                  <span className="text-[#5f6368]">Default: 0.05</span>
                </div>
                <input
                  type="range"
                  min={0.0}
                  max={1.0}
                  step={0.05}
                  value={weights.w_freshness}
                  onChange={(e) => setWeights({ ...weights, w_freshness: parseFloat(e.target.value) })}
                  className="w-full accent-[#1a73e8]"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span>Spam Penalty ({weights.p_spam})</span>
                  <span className="text-[#5f6368]">Default: 0.50</span>
                </div>
                <input
                  type="range"
                  min={0.0}
                  max={1.5}
                  step={0.05}
                  value={weights.p_spam}
                  onChange={(e) => setWeights({ ...weights, p_spam: parseFloat(e.target.value) })}
                  className="w-full accent-[#EA4335]"
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
