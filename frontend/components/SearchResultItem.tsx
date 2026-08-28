"use client";

import { SearchResultItem as SearchResultItemType } from "@/lib/api";
import { ExternalLink, Globe } from "lucide-react";

interface SearchResultItemProps {
  result: SearchResultItemType;
}

export function SearchResultItem({ result }: SearchResultItemProps) {
  // Extract domain and path
  let domain = result.display_url.split("/")[0];
  let path = result.display_url.includes("/") ? result.display_url.substring(domain.length) : "";

  return (
    <article className="flex flex-col group max-w-2xl">
      {/* URL & Source header */}
      <div className="flex items-center gap-2 mb-1">
        <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-[#303134] flex items-center justify-center text-gray-500 dark:text-gray-400 shrink-0">
          <Globe className="w-3.5 h-3.5" />
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
            {domain}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-lg">
            {result.url}
          </span>
        </div>
      </div>

      {/* Title */}
      <h2 className="text-xl font-normal leading-snug">
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#1a0dab] dark:text-[#8ab4f8] hover:underline visited:text-[#609] dark:visited:text-[#c58af9]"
        >
          {result.title}
        </a>
      </h2>

      {/* Snippet with highlighted terms */}
      <p
        className="text-sm text-gray-700 dark:text-[#bdc1c6] mt-1 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: result.snippet || result.description }}
      />

      {/* Metadata tags */}
      <div className="flex items-center gap-3 mt-2 text-xs text-gray-400 dark:text-gray-500">
        {result.published_at && (
          <span>{new Date(result.published_at).toLocaleDateString()}</span>
        )}
        <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-[#303134] text-gray-500 dark:text-gray-400">
          Score: {result.score}
        </span>
      </div>
    </article>
  );
}
