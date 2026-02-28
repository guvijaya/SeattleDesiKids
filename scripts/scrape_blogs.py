#!/usr/bin/env python3
"""
scrape_blogs.py — Fetch essays from Blogger JSON feeds and save as Markdown.

Usage:
    pip install requests html2text python-slugify
    python scripts/scrape_blogs.py
"""

import json
import os
import re
import sys
import io
import time
import requests
import html2text
from slugify import slugify

# Fix Windows terminal Unicode output
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── Configuration ─────────────────────────────────────────────────────────────

BLOG_SOURCES = {
    "english": {
        "url": "https://seattledesikids.blogspot.com",
        "translator": "Jayanthi Gowrishankaran",
    },
    "marathi": {
        "url": "https://seattlemarathi.blogspot.com",
        "translator": "Mahesh Deshpande",
    },
    "telugu": {
        "url": "https://seattletelugukids.blogspot.com",
        "translator": "Pavan Kumar Yerravelly",
    },
    "kannada": {
        "url": "https://muddadakannada.blogspot.com",
        "translator": "Naraya",
    },
    "hindi": {
        "url": "https://nanhihindi.blogspot.com",
        "translator": "Rahul Upadhyaya",
    },
}

FEED_ENDPOINT = "/feeds/posts/default?alt=json&max-results=150"

# Skip these non-essay posts
SKIP_TITLES = {
    "get started", "about us", "about", "welcome", "introduction",
    "start here", "begin here",
}

# Output directory (relative to script location, going up one level)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ESSAYS_DIR = os.path.join(PROJECT_DIR, "src", "content", "essays")

# ─── HTML → Markdown converter setup ───────────────────────────────────────────

def make_converter():
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True      # we use our own illustrations
    h.body_width = 0            # no hard line wraps
    h.ignore_emphasis = False
    h.protect_links = True
    h.unicode_snob = True       # preserve Unicode (Indic scripts)
    return h

converter = make_converter()

# ─── Helpers ───────────────────────────────────────────────────────────────────

def extract_english_slug(raw_title: str) -> str:
    """
    Extract English portion from bilingual titles.
    e.g. "రైలు ప్రయాణం - Train Journey" → "train-journey"
         "Train Journey" → "train-journey"
    """
    # Try splitting on " - " (space-dash-space), take last segment
    parts = re.split(r"\s+[-–]\s+", raw_title)
    english_part = parts[-1].strip()

    # If the result contains only non-ASCII (e.g. pure native script), use the full title
    if not re.search(r"[a-zA-Z]", english_part):
        english_part = raw_title

    return slugify(english_part, separator="-", lowercase=True)


def clean_markdown(md: str) -> str:
    """Clean up converted markdown — collapse blank lines, strip style artifacts."""
    # Collapse 3+ consecutive blank lines to 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    # Remove leftover CSS inline style artifacts
    md = re.sub(r"\{[^}]*font-family[^}]*\}", "", md)
    return md.strip()


def fetch_feed(blog_url: str) -> list[dict]:
    """Fetch and parse a Blogger JSON feed, handling pagination."""
    entries = []
    start_index = 1
    max_results = 50

    while True:
        url = f"{blog_url}/feeds/posts/default?alt=json&max-results={max_results}&start-index={start_index}"
        print(f"  Fetching {url} ...", end=" ", flush=True)

        try:
            resp = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (compatible; KidsBookScraper/1.0)"
            })
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"ERROR: {e}")
            break

        data = resp.json()
        feed = data.get("feed", {})
        batch_entries = feed.get("entry", [])
        total_results = int(feed.get("openSearch$totalResults", {}).get("$t", 0))

        print(f"got {len(batch_entries)} entries (total: {total_results})")
        entries.extend(batch_entries)

        if start_index + max_results > total_results:
            break

        start_index += max_results
        time.sleep(0.5)  # be polite to Blogger

    return entries


def parse_entry(entry: dict) -> dict | None:
    """Extract structured data from a Blogger feed entry."""
    title = entry.get("title", {}).get("$t", "").strip()
    if not title:
        return None

    # Check if this is a skip entry
    if title.lower().strip() in SKIP_TITLES:
        return None

    content_html = entry.get("content", {}).get("$t", "") or \
                   entry.get("summary", {}).get("$t", "")

    author = entry.get("author", [{}])[0].get("name", {}).get("$t", "")
    published = entry.get("published", {}).get("$t", "")[:10]

    # Find the alternate (HTML) link = source URL
    source_url = ""
    for link in entry.get("link", []):
        if link.get("rel") == "alternate":
            source_url = link.get("href", "")
            break

    return {
        "raw_title": title,
        "slug": extract_english_slug(title),
        "content_html": content_html,
        "author": author,
        "published": published,
        "source_url": source_url,
    }


def write_markdown(slug: str, language: str, entry: dict, translator: str):
    """Write a single essay language file."""
    essay_dir = os.path.join(ESSAYS_DIR, slug)
    os.makedirs(essay_dir, exist_ok=True)

    md_path = os.path.join(essay_dir, f"{language}.md")

    # Convert HTML → Markdown
    md_body = converter.handle(entry["content_html"])
    md_body = clean_markdown(md_body)

    # Skip near-empty entries (< 50 chars of content)
    if len(md_body.strip()) < 50:
        print(f"    SKIP (too short): {entry['raw_title']}")
        return False

    # Check for existing file — keep longer version (prefer complete content)
    if os.path.exists(md_path):
        existing = open(md_path, "r", encoding="utf-8").read()
        if len(existing) >= len(md_body) + 200:
            print(f"    KEEP existing (longer): {slug}/{language}.md")
            return True

    frontmatter = f"""---
language: {language}
title: "{entry['raw_title'].replace('"', "'")}"
translator: "{translator}"
sourceUrl: "{entry['source_url']}"
fetchedAt: "{time.strftime('%Y-%m-%d')}"
---

"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + md_body + "\n")

    print(f"    WROTE {slug}/{language}.md ({len(md_body)} chars)")
    return True


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(ESSAYS_DIR, exist_ok=True)
    written = 0
    skipped = 0
    errors = 0

    for language, config in BLOG_SOURCES.items():
        print(f"\n{'='*60}")
        print(f"Scraping {language.upper()} — {config['url']}")
        print(f"{'='*60}")

        entries = fetch_feed(config["url"])
        if not entries:
            print("  No entries found.")
            continue

        for entry_data in entries:
            parsed = parse_entry(entry_data)
            if not parsed:
                skipped += 1
                continue

            print(f"  >> [{parsed['slug']}] {parsed['raw_title'][:60]}")

            success = write_markdown(
                slug=parsed["slug"],
                language=language,
                entry=parsed,
                translator=config["translator"],
            )

            if success:
                written += 1
            else:
                skipped += 1

    print(f"\n{'='*60}")
    print(f"Done! Written: {written}, Skipped: {skipped}, Errors: {errors}")
    print(f"Essays directory: {ESSAYS_DIR}")
    print(f"\nNext step: python scripts/build_manifest.py")


if __name__ == "__main__":
    main()
