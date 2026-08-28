"use client";

import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";
import { Activity, Database, Search, ShieldCheck } from "lucide-react";

interface NavbarProps {
  showSearch?: boolean;
}

export function Navbar({ showSearch = false }: NavbarProps) {
  return (
    <header className="w-full flex items-center justify-between px-6 py-4 border-b border-transparent dark:border-gray-800">
      <div className="flex items-center gap-6">
        {showSearch && (
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-nom-600 to-indigo-500 flex items-center justify-center text-white font-bold text-lg shadow-md shadow-nom-500/20 group-hover:scale-105 transition-transform">
              N
            </div>
            <span className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
              Nom<span className="text-nom-600 dark:text-nom-400">Engine</span>
            </span>
          </Link>
        )}
      </div>

      <nav className="flex items-center gap-4 text-sm font-medium text-gray-600 dark:text-gray-300">
        <Link
          href="/search?q=python"
          className="hover:text-nom-600 dark:hover:text-nom-400 transition-colors hidden sm:inline-block"
        >
          Explore Docs
        </Link>
        <Link
          href="/admin"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-[#303134] hover:bg-gray-200 dark:hover:bg-[#3c4043] text-gray-700 dark:text-gray-200 transition-colors"
        >
          <Activity className="w-4 h-4 text-nom-600 dark:text-nom-400" />
          <span>Admin & Monitoring</span>
        </Link>
        <ThemeToggle />
      </nav>
    </header>
  );
}
