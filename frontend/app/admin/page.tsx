"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import {
  fetchAdminStats,
  fetchRankingWeights,
  updateRankingWeights,
  triggerCrawl,
  pauseCrawler,
  resumeCrawler,
  triggerReindex,
  triggerPageRank,
  AdminStats,
  RankingWeights,
} from "@/lib/api";
import {
  Activity,
  ArrowLeft,
  CheckCircle2,
  Database,
  Globe,
  Layers,
  Link as LinkIcon,
  Pause,
  Play,
  RefreshCw,
  Search,
  Settings2,
  Shield,
  Sliders,
  TrendingUp,
  Zap,
} from "lucide-react";

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
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
    "https://docs.python.org/3/\nhttps://www.python.org/\nhttps://www.djangoproject.com/"
  );
  const [concurrency, setConcurrency] = useState<number>(5);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = () => {
    fetchAdminStats().then(setStats).catch(() => {});
    fetchRankingWeights().then(setWeights).catch(() => {});
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
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
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-[#18191a] text-gray-900 dark:text-gray-100">
      <Navbar showSearch={true} />

      <main className="max-w-6xl mx-auto px-6 py-8 w-full flex flex-col gap-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Link
                href="/"
                className="p-1.5 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 text-gray-500"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight">Admin &amp; Operations Center</h1>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Real-time monitoring, crawler orchestration, ranking weights tuner, and inverted index controls.
            </p>
          </div>

          {stats && (
            <div className="flex items-center gap-2">
              <span
                className={`w-3 h-3 rounded-full ${
                  stats.crawler_is_running
                    ? stats.crawler_is_paused
                      ? "bg-amber-500 animate-pulse"
                      : "bg-emerald-500 animate-ping"
                    : "bg-gray-400"
                }`}
              />
              <span className="text-xs font-semibold uppercase tracking-wider text-gray-600 dark:text-gray-300">
                {stats.crawler_is_running
                  ? stats.crawler_is_paused
                    ? "Crawler Paused"
                    : "Crawler Active"
                  : "Crawler Idle"}
              </span>
            </div>
          )}
        </div>

        {/* Status Toast */}
        {statusMessage && (
          <div className="flex items-center justify-between p-4 rounded-xl bg-nom-50 dark:bg-nom-950/50 border border-nom-200 dark:border-nom-800 text-nom-900 dark:text-nom-100 text-sm animate-in fade-in duration-200">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-nom-600 dark:text-nom-400" />
              <span>{statusMessage}</span>
            </div>
            <button
              onClick={() => setStatusMessage(null)}
              className="text-xs font-semibold text-nom-700 dark:text-nom-300 hover:underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Telemetry Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="p-4 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-1">
            <div className="flex items-center justify-between text-gray-500 dark:text-gray-400 text-xs">
              <span>Indexed Pages</span>
              <Database className="w-4 h-4 text-nom-600" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.pages_indexed.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-1">
            <div className="flex items-center justify-between text-gray-500 dark:text-gray-400 text-xs">
              <span>Pages Crawled</span>
              <Globe className="w-4 h-4 text-cyan-500" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.pages_crawled.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-1">
            <div className="flex items-center justify-between text-gray-500 dark:text-gray-400 text-xs">
              <span>Frontier Queue</span>
              <Layers className="w-4 h-4 text-amber-500" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.frontier_queue_size.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-1">
            <div className="flex items-center justify-between text-gray-500 dark:text-gray-400 text-xs">
              <span>Index Terms</span>
              <Zap className="w-4 h-4 text-emerald-500" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.unique_terms_in_index.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-1">
            <div className="flex items-center justify-between text-gray-500 dark:text-gray-400 text-xs">
              <span>Graph Links</span>
              <LinkIcon className="w-4 h-4 text-indigo-500" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.total_links_graph.toLocaleString() ?? 0}
            </span>
          </div>

          <div className="p-4 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-1">
            <div className="flex items-center justify-between text-gray-500 dark:text-gray-400 text-xs">
              <span>Searches Run</span>
              <Search className="w-4 h-4 text-pink-500" />
            </div>
            <span className="text-2xl font-bold text-gray-900 dark:text-white">
              {stats?.searches_recorded.toLocaleString() ?? 0}
            </span>
          </div>
        </div>

        {/* Section: Crawler Controls & Ranking Tuner */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Crawler Seeds & Actions */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-base">
                  <Globe className="w-5 h-5 text-nom-600 dark:text-nom-400" />
                  <h2>Web Crawler Seed Manager</h2>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                  Seed URLs (One per line)
                </label>
                <textarea
                  rows={4}
                  value={seedInput}
                  onChange={(e) => setSeedInput(e.target.value)}
                  className="w-full p-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-[#18191a] text-sm font-mono text-gray-900 dark:text-gray-100 outline-none focus:border-nom-500"
                  placeholder="https://example.com"
                />
              </div>

              <div>
                <div className="flex items-center justify-between text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  <span>Worker Concurrency</span>
                  <span>{concurrency} workers</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={concurrency}
                  onChange={(e) => setConcurrency(parseInt(e.target.value, 10))}
                  className="w-full accent-nom-600"
                />
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={handleStartCrawl}
                  disabled={loadingAction === "crawl"}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-nom-600 hover:bg-nom-700 text-white font-medium text-sm shadow-md shadow-nom-600/20 disabled:opacity-50 transition-all"
                >
                  <Play className="w-4 h-4 fill-white" />
                  <span>Start Crawling</span>
                </button>

                {stats?.crawler_is_running && (
                  <button
                    onClick={handlePauseResume}
                    disabled={loadingAction === "pause"}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 font-medium text-sm transition-all"
                  >
                    {stats.crawler_is_paused ? (
                      <>
                        <Play className="w-4 h-4 text-emerald-500" />
                        <span>Resume</span>
                      </>
                    ) : (
                      <>
                        <Pause className="w-4 h-4 text-amber-500" />
                        <span>Pause</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Quick Maintenance Controls */}
            <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-4">
              <div className="flex items-center gap-2 font-semibold text-base">
                <RefreshCw className="w-5 h-5 text-indigo-500" />
                <h2>Index &amp; Graph Maintenance</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  onClick={handleReindex}
                  disabled={loadingAction === "reindex"}
                  className="flex flex-col items-start p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-nom-400 bg-gray-50/50 dark:bg-[#18191a] text-left transition-all"
                >
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    Re-Index All Pages
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Rebuilds positional posting lists from database.
                  </span>
                </button>

                <button
                  onClick={handlePageRank}
                  disabled={loadingAction === "pagerank"}
                  className="flex flex-col items-start p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-nom-400 bg-gray-50/50 dark:bg-[#18191a] text-left transition-all"
                >
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    Compute PageRank
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Power-iteration over the entire link graph.
                  </span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Dynamic Ranking Weights Sliders */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-base">
                  <Sliders className="w-5 h-5 text-nom-600 dark:text-nom-400" />
                  <h2>Ranking Formula Weight Tuner</h2>
                </div>
                <button
                  onClick={handleSaveWeights}
                  disabled={loadingAction === "weights"}
                  className="px-3 py-1.5 rounded-lg bg-nom-600 hover:bg-nom-700 text-white font-medium text-xs shadow-sm transition-all"
                >
                  Save Weights
                </button>
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400 -mt-2">
                Adjust multi-factor ranking signals in real time without restarting backend services.
              </p>

              <div className="space-y-3.5 pt-2">
                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>BM25 Lexical Score ({weights.w_bm25})</span>
                    <span className="text-gray-400">Default: 0.40</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={1.5}
                    step={0.05}
                    value={weights.w_bm25}
                    onChange={(e) => setWeights({ ...weights, w_bm25: parseFloat(e.target.value) })}
                    className="w-full accent-nom-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Title Match Bonus ({weights.w_title})</span>
                    <span className="text-gray-400">Default: 0.25</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={1.5}
                    step={0.05}
                    value={weights.w_title}
                    onChange={(e) => setWeights({ ...weights, w_title: parseFloat(e.target.value) })}
                    className="w-full accent-nom-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Exact Phrase Adjacency ({weights.w_phrase})</span>
                    <span className="text-gray-400">Default: 0.15</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={1.5}
                    step={0.05}
                    value={weights.w_phrase}
                    onChange={(e) => setWeights({ ...weights, w_phrase: parseFloat(e.target.value) })}
                    className="w-full accent-nom-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>PageRank Link Authority ({weights.w_pagerank})</span>
                    <span className="text-gray-400">Default: 0.10</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={1.5}
                    step={0.05}
                    value={weights.w_pagerank}
                    onChange={(e) => setWeights({ ...weights, w_pagerank: parseFloat(e.target.value) })}
                    className="w-full accent-nom-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Freshness Decay Bonus ({weights.w_freshness})</span>
                    <span className="text-gray-400">Default: 0.05</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={1.0}
                    step={0.05}
                    value={weights.w_freshness}
                    onChange={(e) => setWeights({ ...weights, w_freshness: parseFloat(e.target.value) })}
                    className="w-full accent-nom-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>Spam Penalty Multiplier ({weights.p_spam})</span>
                    <span className="text-gray-400">Default: 0.50</span>
                  </div>
                  <input
                    type="range"
                    min={0.0}
                    max={1.5}
                    step={0.05}
                    value={weights.p_spam}
                    onChange={(e) => setWeights({ ...weights, p_spam: parseFloat(e.target.value) })}
                    className="w-full accent-red-500"
                  />
                </div>
              </div>
            </div>

            {/* Top Domains Breakdown */}
            {stats && stats.top_domains.length > 0 && (
              <div className="p-6 rounded-2xl bg-white dark:bg-[#242526] border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col gap-3">
                <h3 className="font-semibold text-sm">Top Indexed Domains</h3>
                <div className="space-y-2 text-xs">
                  {stats.top_domains.map((dom) => (
                    <div key={dom.domain} className="flex justify-between items-center py-1 border-b border-gray-100 dark:border-gray-800">
                      <span className="font-mono text-gray-700 dark:text-gray-300">{dom.domain}</span>
                      <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-800 font-semibold">{dom.count} pages</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
