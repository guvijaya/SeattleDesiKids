#!/usr/bin/env python3
"""
consolidate_essays.py — Merge variant-slug essay folders into canonical slugs.

Each essay may have been scraped into different slug folders across languages.
This script moves all language files into a single canonical folder per essay.

Usage:
    python scripts/consolidate_essays.py
"""

import os
import sys
import io
import shutil

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
ESSAYS_DIR = os.path.join(PROJECT_DIR, "src", "content", "essays")

# Canonical slug → list of variant slugs to absorb
# The canonical slug is what the Tamil extractor uses (most reliable)
CONSOLIDATION_MAP = {
    "sunrise-mt-rainier": [
        "sunrise-at-mt-rainier",       # english, telugu
        "sunrise-on-mount-rainier",    # hindi
        "sunrise-at-rainier",          # kannada
        "maauuntt-reniar-vrcaa-suuryody",  # marathi
    ],
    "sammamish-lake-trail": [
        "samammish-lake-trail",                               # english (typo)
        "smaamiish-ndii-kaatth-cii-paayvaatt-smaamish-lek-ttrel",  # marathi
        "smmaamiss-tlaavaacii-paayvaatt-ttrel",               # marathi variant
        "smmmiss-sreuu-vrd-rste-samammish-lake-trail",        # kannada
    ],
    "marymoor-park": [
        "marymoore-park",    # english (extra 'e')
        "meeriimuur-paark",  # telugu
        "meriimuur-paark",   # marathi
    ],
    "train-journey": [
        "aaggaaddiicaa-prvaas-ttren-caa-prvaas",  # marathi
    ],
    "birthday-party": [
        "jnmdin-kii-paarttii-birthday-party",    # hindi
        "jnmdind-aacrnne-birthday-celebrations", # kannada (first duplicate)
        "birthday-parties",                      # kannada (second duplicate)
        "maajhaa-vaaddhdivs",                    # marathi
    ],
    "idylwood-beach-park": [
        "iiddlvuudd-biic-paark",                # marathi
        "idyllwood-park",                        # hindi
        "aiddilvudd-udyaanvn-idylwood-park",    # kannada
    ],
    "boat-ride": [
        "bott-raaidd",                   # marathi
        "deuu-nni-vihaar-boat-ride",     # kannada
    ],
    "halloween": [
        "henlovin",                   # marathi
        "hyaaleuu-vi-n-halloween",    # kannada
    ],
    "escape-room": [
        "eskep-kholii-escape-room",              # marathi
        "tppisikeuulllluv-keuutthddi-escape-room",  # kannada
    ],
    "farmers-market": [
        "shetkrii-baajaar",          # marathi
        "re-t-snte-farmer-s-market", # kannada
    ],
    "higher-secondary-schools-world-language-credits": [
        "world-language-credits",                              # english, telugu, kannada
        "world-language-credit",                               # hindi
        "ucc-maadhymik-shaalaa-jaagtik-bhaassaa-kredditts",   # marathi
    ],
    "snow-day": [
        "himvrssaav",   # marathi
    ],
    "potluck": [
        "sne-hkuutt-potluck",  # kannada
    ],
    "gardening": [
        "baagkaam",  # marathi
    ],
    "train": [
        "train-travel",  # kannada (ರೈಲು ಪ್ರಯಾಣ - same essay as "Train")
    ],
    # Intro/about posts — consolidate but mark as non-essay
    "get-started": [
        "getting-started",  # kannada
        "aarnbh-kraa",      # marathi
    ],
}

# These slugs are unique Kannada stories not translated from Tamil — keep as-is
UNIQUE_CONTENT = {"allilin-alllu", "puppet-story", "story", "ranganna"}


def consolidate():
    moves = 0
    removals = 0

    for canonical, variants in CONSOLIDATION_MAP.items():
        canonical_dir = os.path.join(ESSAYS_DIR, canonical)
        os.makedirs(canonical_dir, exist_ok=True)

        for variant in variants:
            variant_dir = os.path.join(ESSAYS_DIR, variant)
            if not os.path.exists(variant_dir):
                continue

            # Move all *.md files from variant to canonical
            files = [f for f in os.listdir(variant_dir) if f.endswith(".md")]
            for fname in files:
                src = os.path.join(variant_dir, fname)
                dst = os.path.join(canonical_dir, fname)

                if os.path.exists(dst):
                    # Keep the longer (more complete) version
                    src_size = os.path.getsize(src)
                    dst_size = os.path.getsize(dst)
                    if src_size <= dst_size:
                        print(f"  KEEP existing {canonical}/{fname} (larger)")
                        continue
                    else:
                        print(f"  REPLACE {canonical}/{fname} with larger version from {variant}/")

                shutil.move(src, dst)
                print(f"  MOVED {variant}/{fname} -> {canonical}/{fname}")
                moves += 1

            # Remove empty variant dir (and its metadata.json)
            meta = os.path.join(variant_dir, "metadata.json")
            if os.path.exists(meta):
                os.remove(meta)

            remaining = [f for f in os.listdir(variant_dir) if not f.startswith('.')]
            if not remaining:
                os.rmdir(variant_dir)
                print(f"  REMOVED empty dir: {variant}/")
                removals += 1
            else:
                print(f"  NOTE: {variant}/ still has files: {remaining}")

    print(f"\nConsolidation complete: {moves} files moved, {removals} dirs removed.")


def report_final_state():
    """Print the final essay inventory."""
    essay_dirs = sorted([
        d for d in os.listdir(ESSAYS_DIR)
        if os.path.isdir(os.path.join(ESSAYS_DIR, d))
    ])

    print(f"\nFinal state: {len(essay_dirs)} essay folders:")
    for slug in essay_dirs:
        d = os.path.join(ESSAYS_DIR, slug)
        langs = [f[:-3] for f in os.listdir(d) if f.endswith(".md")]
        langs_str = ", ".join(sorted(langs)) or "(empty)"
        is_unique = " [unique Kannada]" if slug in UNIQUE_CONTENT else ""
        print(f"  {slug:<55} [{langs_str}]{is_unique}")


if __name__ == "__main__":
    print(f"Consolidating essays in: {ESSAYS_DIR}\n")
    consolidate()
    report_final_state()
    print("\nNext: python scripts/build_manifest.py")
