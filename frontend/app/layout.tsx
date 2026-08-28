import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NomEngine - Modern Web Search Engine From Scratch",
  description:
    "A scalable, production-grade web search engine built from scratch with custom crawler, positional inverted index, and BM25 ranking.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
