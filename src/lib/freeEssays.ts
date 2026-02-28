/**
 * Computed at build time — top 3 essays by available language count.
 * These essays are readable without signing in.
 */
import fs from 'node:fs';
import path from 'node:path';

const essaysDir = path.join(process.cwd(), 'src', 'content', 'essays');

function computeFreeEssays(): string[] {
  if (!fs.existsSync(essaysDir)) return [];

  const slugs = fs.readdirSync(essaysDir).filter(name =>
    fs.statSync(path.join(essaysDir, name)).isDirectory()
  );

  const metas: Array<{ slug: string; count: number }> = [];

  for (const slug of slugs) {
    const metaPath = path.join(essaysDir, slug, 'metadata.json');
    if (!fs.existsSync(metaPath)) continue;
    const meta = JSON.parse(fs.readFileSync(metaPath, 'utf-8'));
    metas.push({
      slug: meta.slug || slug,
      count: (meta.availableLanguages || []).length,
    });
  }

  // Sort by language count desc, then alphabetically for stable ordering
  metas.sort((a, b) => b.count - a.count || a.slug.localeCompare(b.slug));

  return metas.slice(0, 3).map(m => m.slug);
}

export const FREE_ESSAY_SLUGS: readonly string[] = computeFreeEssays();
