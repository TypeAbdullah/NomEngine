"use client";

import { NewsResultItem as NewsResultItemType } from "@/lib/api";
import { Newspaper } from "lucide-react";

interface NewsResultItemProps {
  news: NewsResultItemType;
}

export function NewsResultItem({ news }: NewsResultItemProps) {
  return (
    <article className="flex flex-col p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-[#303134] hover:shadow-sm transition-all max-w-2xl">
      <div className="flex items-center gap-2 mb-1.5 text-xs text-gray-500 dark:text-gray-400">
        <Newspaper className="w-3.5 h-3.5 text-nom-600 dark:text-nom-400" />
        <span className="font-semibold text-gray-700 dark:text-gray-300">
          {news.publisher || "News Publisher"}
        </span>
        {news.published_date && (
          <span>• {new Date(news.published_date).toLocaleDateString()}</span>
        )}
      </div>

      <h3 className="text-base font-semibold leading-snug">
        <a
          href={news.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline"
        >
          {news.headline}
        </a>
      </h3>

      <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 line-clamp-2">
        {news.snippet}
      </p>
    </article>
  );
}
