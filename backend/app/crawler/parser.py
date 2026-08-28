"""
HTML Processing and Structured Content Extractor
Extracts primary readable content, metadata, links, images, and news article signals.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Comment
from app.crawler.deduplication import normalize_url
from app.monitoring.logger import logger


class ParsedPage:
    """Data container for extracted web page contents."""

    def __init__(self):
        self.url: str = ""
        self.canonical_url: Optional[str] = None
        self.title: str = ""
        self.description: str = ""
        self.language: str = "en"
        self.author: Optional[str] = None
        self.published_date: Optional[datetime] = None
        self.modified_date: Optional[datetime] = None
        self.main_text: str = ""
        self.word_count: int = 0
        self.noindex: bool = False
        self.nofollow: bool = False
        self.links: List[Tuple[str, str]] = []  # (target_url, anchor_text)
        self.images: List[Dict[str, Any]] = []
        self.is_news: bool = False
        self.news_headline: Optional[str] = None
        self.news_publisher: Optional[str] = None


class HTMLContentExtractor:
    """High-quality HTML parser and readable text extractor."""

    # Unwanted tag names
    STRIP_TAGS = {
        "script", "style", "noscript", "svg", "header", "footer", "nav",
        "aside", "form", "button", "iframe", "menu", "template"
    }

    # Boilerplate / noise CSS classes and IDs
    NOISE_PATTERNS = re.compile(
        r"(cookie|banner|consent|gdpr|newsletter|subscribe|advert|ad-|ad_|sidebar|popup|modal|share|social)",
        re.IGNORECASE,
    )

    def parse(self, html: str, base_url: str) -> ParsedPage:
        """Parses raw HTML and returns a structured ParsedPage object."""
        page = ParsedPage()
        page.url = normalize_url(base_url)

        if not html:
            return page

        try:
            soup = BeautifulSoup(html, "lxml")
        except Exception:
            try:
                soup = BeautifulSoup(html, "html.parser")
            except Exception as e:
                logger.warning(f"Failed to parse HTML for {base_url}: {e}")
                return page

        # 1. Robots Meta Directives
        for meta in soup.find_all("meta", attrs={"name": re.compile(r"robots", re.I)}):
            content = meta.get("content", "").lower()
            if "noindex" in content:
                page.noindex = True
            if "nofollow" in content:
                page.nofollow = True

        # 2. Canonical URL
        canonical_tag = soup.find("link", rel=lambda val: val and "canonical" in val.lower())
        if canonical_tag and canonical_tag.get("href"):
            page.canonical_url = normalize_url(urljoin(base_url, canonical_tag["href"]))

        # 3. Title Extraction
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            page.title = title_tag.string.strip()
        elif soup.find("meta", property="og:title"):
            page.title = soup.find("meta", property="og:title").get("content", "").strip()
        elif soup.find("h1"):
            page.title = soup.find("h1").get_text(strip=True)

        # 4. Meta Description
        desc_meta = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", property="og:description"
        )
        if desc_meta and desc_meta.get("content"):
            page.description = desc_meta["content"].strip()

        # 5. Language Detection
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = html_tag["lang"].split("-")[0].strip().lower()
            if len(lang) <= 8:
                page.language = lang

        # 6. Author and Dates
        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find(
            "meta", property="article:author"
        )
        if author_meta and author_meta.get("content"):
            page.author = author_meta["content"].strip()

        pub_meta = soup.find("meta", property="article:published_time") or soup.find(
            "meta", attrs={"name": "pubdate"}
        )
        if pub_meta and pub_meta.get("content"):
            try:
                page.published_date = datetime.fromisoformat(
                    pub_meta["content"].replace("Z", "+00:00")
                )
            except Exception:
                pass

        # 7. Images Extraction (before destroying DOM)
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if not src:
                continue
            img_url = normalize_url(urljoin(base_url, src))
            if not img_url or img_url.startswith("data:"):
                continue

            alt = img.get("alt", "").strip()
            img_title = img.get("title", "").strip()
            width = self._parse_int(img.get("width"))
            height = self._parse_int(img.get("height"))

            page.images.append({
                "image_url": img_url,
                "alt_text": alt,
                "title": img_title,
                "width": width,
                "height": height,
                "surrounding_text": img.parent.get_text(" ", strip=True)[:250] if img.parent else "",
            })

        # 8. Link Extraction (before destroying DOM)
        if not page.nofollow:
            seen_links: Set[str] = set()
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                    continue

                abs_url = normalize_url(urljoin(base_url, href))
                if not abs_url or abs_url == page.url or abs_url in seen_links:
                    continue

                rel = a.get("rel", [])
                if isinstance(rel, str):
                    rel = [rel]
                if any("nofollow" in r.lower() for r in rel):
                    continue

                anchor = a.get_text(" ", strip=True)[:200]
                seen_links.add(abs_url)
                page.links.append((abs_url, anchor))

        # 9. Clean Readable Main Text Extraction
        # Remove HTML comments
        for comment in soup.find_all(text=lambda t: isinstance(t, Comment)):
            comment.extract()

        # Remove noise tags
        for tag_name in self.STRIP_TAGS:
            for el in soup.find_all(tag_name):
                el.decompose()

        # Remove elements with noise classes/IDs
        for el in soup.find_all(attrs={"class": self.NOISE_PATTERNS}):
            el.decompose()
        for el in soup.find_all(attrs={"id": self.NOISE_PATTERNS}):
            el.decompose()

        # Prefer <article> or <main> or standard body
        content_root = soup.find("article") or soup.find("main") or soup.find("body") or soup

        # Extract text blocks
        text_blocks = []
        for element in content_root.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote"]):
            txt = element.get_text(" ", strip=True)
            if len(txt) > 10:  # Skip tiny fragments
                text_blocks.append(txt)

        if not text_blocks:
            # Fallback to direct clean text
            full_text = content_root.get_text(" ", strip=True)
            page.main_text = re.sub(r"\s+", " ", full_text)
        else:
            page.main_text = re.sub(r"\s+", " ", "\n\n".join(text_blocks))

        words = re.findall(r"\b\w+\b", page.main_text)
        page.word_count = len(words)

        # 10. News Article Detection
        if soup.find("meta", property="og:type", content=re.compile(r"article", re.I)) or page.published_date:
            page.is_news = True
            page.news_headline = page.title
            og_site = soup.find("meta", property="og:site_name")
            page.news_publisher = og_site.get("content") if og_site else parsed_domain(base_url)

        return page

    @staticmethod
    def _parse_int(val: Any) -> Optional[int]:
        if not val:
            return None
        try:
            return int(re.sub(r"[^\d]", "", str(val)))
        except ValueError:
            return None


def parsed_domain(url: str) -> str:
    """Extracts clean domain name from URL."""
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


extractor = HTMLContentExtractor()
