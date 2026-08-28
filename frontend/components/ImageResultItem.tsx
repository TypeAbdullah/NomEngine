"use client";

import { ImageResultItem as ImageResultItemType } from "@/lib/api";
import { ExternalLink, Image as ImageIcon } from "lucide-react";

interface ImageResultItemProps {
  image: ImageResultItemType;
}

export function ImageResultItem({ image }: ImageResultItemProps) {
  let domain = "";
  try {
    domain = new URL(image.page_url).hostname;
  } catch (e) {
    domain = image.page_url;
  }

  return (
    <div className="flex flex-col group overflow-hidden rounded-xl bg-gray-50 dark:bg-[#303134] border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all">
      <div className="relative aspect-video w-full bg-gray-200 dark:bg-gray-800 overflow-hidden flex items-center justify-center">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={image.image_url}
          alt={image.alt_text || "Search image"}
          loading="lazy"
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          onError={(e) => {
            // Hide broken image link
            (e.target as HTMLElement).style.display = "none";
          }}
        />
        <ImageIcon className="w-8 h-8 text-gray-400 absolute opacity-20 pointer-events-none" />
      </div>

      <div className="p-3 flex flex-col gap-1">
        <a
          href={image.page_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-gray-900 dark:text-white truncate hover:underline"
        >
          {image.alt_text || image.title || "Image Result"}
        </a>
        <span className="text-[11px] text-gray-500 dark:text-gray-400 truncate">
          {domain}
        </span>
      </div>
    </div>
  );
}
