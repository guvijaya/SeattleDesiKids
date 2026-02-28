#!/usr/bin/env python3
"""
extract_tamil.py — Extract Tamil essays from "Konju Tamil V3.docx"
and save them as Markdown files.

Usage:
    pip install python-docx python-slugify
    python scripts/extract_tamil.py
"""

import os
import re
import sys
import io
import time

# Fix Windows terminal Unicode output
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    from docx import Document
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx python-slugify")
    sys.exit(1)

# ─── Configuration ─────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DOCX_PATH = os.path.join(PROJECT_DIR, "Konju Tamil V3.docx")
ESSAYS_DIR = os.path.join(PROJECT_DIR, "src", "content", "essays")

# Skip these non-essay chapters
SKIP_TITLES_CONTAINING = ["முன்னுரை", "அணிந்துரை", "சில மாதிரி"]

# Map Tamil chapter titles to English slugs
TAMIL_TO_SLUG = {
    "பள்ளிப் பேருந்து":            "school-bus",
    "ஹாலோவின்":                   "halloween",
    "தப்பிக்கும் அறை":             "escape-room",
    "பனிவிழும் நாள்":              "snow-day",
    "படகுச் சவாரி":                "boat-ride",
    "உழவர் சந்தை":                 "farmers-market",
    "கூட்டாஞ்சோறு":               "potluck",
    "பிறந்தநாள் கொண்டாட்டங்கள்":   "birthday-party",
    "தோட்டம்":                     "gardening",
    "இரயில் பயணம்":               "train-journey",
    "சமாமிஷ் ஏரி மிதிவண்டியில் வலம்": "sammamish-lake-trail",
    "ஐட்லிவுட் பூங்கா":            "idylwood-beach-park",
    "ஃபிராங்க்ளின் அருவி":         "franklin-falls",
    "புறப்பாடு":                   "an-outing",
    "சமாமிஷ் நடைபாதை":            "sammamish-river-trail",
    "மெரிமோர் பூங்கா":             "marymoor-park",
    "ரெயினியர் பூபாளம்":           "sunrise-mt-rainier",
    "உயர்நிலைப்பள்ளி":             "higher-secondary-schools-world-language-credits",
}


# ─── Helpers ───────────────────────────────────────────────────────────────────

def get_slug_for_title(title_text: str) -> str:
    """
    Extract slug from a Chapter Title.
    Title may contain:
    - Only Tamil: "ஹாலோவின்"
    - Tamil + English in parens: "சமாமிஷ் ஏரி மிதிவண்டியில் வலம்\n(Sammamish lake trail)"
    - Tamil + English inline: "ரெயினியர் பூபாளம் (Mt.Rainier sunrise)"

    Priority: TAMIL_TO_SLUG mapping > parenthetical English > fallback
    """
    # Try known Tamil title mappings first (highest priority)
    for tamil_key, slug in TAMIL_TO_SLUG.items():
        if tamil_key in title_text:
            return slug

    # Extract English from parentheses as fallback
    paren_match = re.search(r'\(([^)]+)\)', title_text)
    if paren_match:
        english = paren_match.group(1).strip()
        slug = english.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug).strip('-')
        return slug

    # Fallback: hash-based slug
    return f"essay-{abs(hash(title_text)) % 10000:04d}"


def clean_title(raw_title: str) -> str:
    """Get the display Tamil title (first line only, without English portion)."""
    lines = [line.strip() for line in raw_title.split('\n') if line.strip()]
    # Remove lines that are purely English/ASCII (the parenthetical translations)
    tamil_lines = [l for l in lines if re.search(r'[\u0B80-\u0BFF]', l)]
    return tamil_lines[0] if tamil_lines else lines[0]


def should_skip(title_text: str) -> bool:
    """Skip non-essay chapters like prefaces."""
    for skip in SKIP_TITLES_CONTAINING:
        if skip in title_text:
            return True
    return False


def paragraph_to_markdown(para) -> str:
    """Convert a docx paragraph to a Markdown line."""
    text = para.text.strip()
    # Normalize non-breaking spaces
    text = text.replace('\xa0', ' ')
    if not text:
        return ""

    style = para.style.name
    if style == "Heading 1":
        return f"# {text}"
    elif style == "Heading 2":
        return f"## {text}"
    elif style == "Content Para":
        # Check if it's a bold sub-heading
        runs = [r for r in para.runs if r.text.strip()]
        if runs and all(r.bold for r in runs) and len(text) < 80:
            return f"**{text}**"
        return text
    elif style in ("List Paragraph", "List Bullet"):
        return f"- {text}"
    else:
        return text


# ─── Main extraction ────────────────────────────────────────────────────────────

def extract_essays(docx_path: str) -> list[dict]:
    doc = Document(docx_path)
    essays = []

    current_slug = None
    current_title = None
    current_lines = []

    for para in doc.paragraphs:
        text = para.text.strip()

        if para.style.name == "Chapter Title" and text:
            # Save previous essay
            if current_slug and current_lines:
                content = "\n\n".join(current_lines).strip()
                if len(content) > 80:
                    essays.append({
                        "slug": current_slug,
                        "title": current_title,
                        "content": content,
                    })

            if should_skip(text):
                current_slug = None
                current_title = None
                current_lines = []
            else:
                current_slug = get_slug_for_title(text)
                current_title = clean_title(text)
                current_lines = []

        elif current_slug and para.style.name in ("Content Para", "Normal"):
            md = paragraph_to_markdown(para)
            if md:
                current_lines.append(md)

    # Flush last essay
    if current_slug and current_lines:
        content = "\n\n".join(current_lines).strip()
        if len(content) > 80:
            essays.append({
                "slug": current_slug,
                "title": current_title,
                "content": content,
            })

    return essays


def write_essay(essay: dict):
    essay_dir = os.path.join(ESSAYS_DIR, essay["slug"])
    os.makedirs(essay_dir, exist_ok=True)

    md_path = os.path.join(essay_dir, "tamil.md")

    frontmatter = (
        f'---\n'
        f'language: tamil\n'
        f'title: "{essay["title"].replace(chr(34), chr(39))}"\n'
        f'translator: "Guruprasad Vijayarao"\n'
        f'fetchedAt: "{time.strftime("%Y-%m-%d")}"\n'
        f'---\n\n'
    )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + essay["content"] + "\n")

    title_preview = essay["title"][:40]
    print(f"  WROTE {essay['slug']}/tamil.md ({len(essay['content'])} chars) — {title_preview}")


# ─── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(DOCX_PATH):
        print(f"ERROR: File not found: {DOCX_PATH}")
        sys.exit(1)

    print(f"Extracting Tamil essays from: {DOCX_PATH}")
    print(f"Output: {ESSAYS_DIR}\n")

    os.makedirs(ESSAYS_DIR, exist_ok=True)

    essays = extract_essays(DOCX_PATH)
    print(f"Found {len(essays)} essays\n")

    for essay in essays:
        write_essay(essay)

    print(f"\nDone! {len(essays)} Tamil essays written.")
    print("Next: python scripts/scrape_blogs.py")


if __name__ == "__main__":
    main()
