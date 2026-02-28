#!/usr/bin/env python3
"""
build_manifest.py — Generate metadata.json for each essay folder.

Reads all *.md files in each essay directory, extracts frontmatter,
and produces a consolidated metadata.json per essay.

Usage:
    python scripts/build_manifest.py
"""

import json
import os
import re
import sys
import io
from datetime import date

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ESSAYS_DIR = os.path.join(PROJECT_DIR, "src", "content", "essays")

LANGUAGE_ORDER = ["tamil", "english", "hindi", "telugu", "marathi", "kannada"]

TRANSLATORS = {
    "tamil":   {"name": "Guruprasad Vijayarao", "blog": ""},
    "english": {"name": "Jayanthi Gowrishankaran", "blog": "https://seattledesikids.blogspot.com"},
    "marathi": {"name": "Mahesh Deshpande", "blog": "https://seattlemarathi.blogspot.com"},
    "telugu":  {"name": "Pavan Kumar Yerravelly", "blog": "https://seattletelugukids.blogspot.com"},
    "kannada": {"name": "Naraya", "blog": "https://muddadakannada.blogspot.com"},
    "hindi":   {"name": "Rahul Upadhyaya", "blog": "https://nanhihindi.blogspot.com"},
}

# ─── Helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(md_content: str) -> dict:
    """Extract YAML-ish frontmatter from a markdown file."""
    result = {}
    match = re.match(r"^---\n([\s\S]*?)\n---", md_content)
    if not match:
        return result

    for line in match.group(1).splitlines():
        kv = line.split(":", 1)
        if len(kv) == 2:
            key = kv[0].strip()
            val = kv[1].strip().strip('"').strip("'")
            result[key] = val

    return result


def build_display_titles(essay_dir: str, slug: str) -> tuple[str, dict]:
    """Build the englishTitle and displayTitles dict from available language files."""
    display_titles = {}
    english_title = slug.replace("-", " ").title()

    for lang in LANGUAGE_ORDER:
        md_path = os.path.join(essay_dir, f"{lang}.md")
        if not os.path.exists(md_path):
            continue
        content = open(md_path, encoding="utf-8").read()
        fm = parse_frontmatter(content)
        title = fm.get("title", "")
        if title:
            display_titles[lang] = title
            if lang == "english":
                english_title = title

    return english_title, display_titles


def build_source_urls(essay_dir: str) -> dict:
    """Collect source URLs from frontmatter of all available language files."""
    urls = {}
    for lang in LANGUAGE_ORDER:
        md_path = os.path.join(essay_dir, f"{lang}.md")
        if not os.path.exists(md_path):
            continue
        content = open(md_path, encoding="utf-8").read()
        fm = parse_frontmatter(content)
        url = fm.get("sourceUrl", "")
        if url and url != "None" and url.startswith("http"):
            urls[lang] = url
    return urls


def get_earliest_date(essay_dir: str) -> str:
    """Get the earliest published date across all language files."""
    dates = []
    for lang in LANGUAGE_ORDER:
        md_path = os.path.join(essay_dir, f"{lang}.md")
        if not os.path.exists(md_path):
            continue
        content = open(md_path, encoding="utf-8").read()
        fm = parse_frontmatter(content)
        d = fm.get("fetchedAt", "")
        if re.match(r"\d{4}-\d{2}-\d{2}", d):
            dates.append(d)
    return min(dates) if dates else str(date.today())


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(ESSAYS_DIR):
        print(f"ERROR: Essays directory not found: {ESSAYS_DIR}")
        print("Run scrape_blogs.py and extract_tamil.py first.")
        exit(1)

    essay_dirs = [
        d for d in os.listdir(ESSAYS_DIR)
        if os.path.isdir(os.path.join(ESSAYS_DIR, d))
    ]
    essay_dirs.sort()

    print(f"Building manifests for {len(essay_dirs)} essay folders...\n")

    for slug in essay_dirs:
        essay_dir = os.path.join(ESSAYS_DIR, slug)
        meta_path = os.path.join(essay_dir, "metadata.json")

        # Determine available languages
        available = [
            lang for lang in LANGUAGE_ORDER
            if os.path.exists(os.path.join(essay_dir, f"{lang}.md"))
        ]

        if not available:
            print(f"  SKIP {slug} (no language files)")
            continue

        english_title, display_titles = build_display_titles(essay_dir, slug)
        source_urls = build_source_urls(essay_dir)
        published_date = get_earliest_date(essay_dir)

        # Build translators dict for available languages
        translators = {
            lang: TRANSLATORS[lang]
            for lang in available
            if lang in TRANSLATORS
        }

        # Determine illustrations (SVG files in public/images/essays/{slug}/)
        img_dir = os.path.join(PROJECT_DIR, "public", "images", "essays")
        illustrations = [
            f"{slug}-1.svg" if os.path.exists(os.path.join(img_dir, f"{slug}-1.svg")) else None,
            f"{slug}-2.svg" if os.path.exists(os.path.join(img_dir, f"{slug}-2.svg")) else None,
        ]
        illustrations = [i for i in illustrations if i]

        metadata = {
            "slug": slug,
            "englishTitle": english_title,
            "displayTitles": display_titles,
            "availableLanguages": available,
            "originalAuthor": "Guruprasad Vijayarao",
            "translators": translators,
            "illustrations": illustrations,
            "tags": [],
            "sourceUrls": source_urls,
            "publishedDate": published_date,
            "lastUpdated": str(date.today()),
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        lang_codes = ", ".join(available)
        print(f"  OK {slug} [{lang_codes}] -- {english_title}")

    print(f"\nDone! {len(essay_dirs)} metadata.json files written.")
    print("Run `npm run build` in the project directory to build the site.")


if __name__ == "__main__":
    main()
