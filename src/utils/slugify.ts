/**
 * Convert a string to a URL-safe slug.
 * Handles bilingual titles like "రైలు ప్రయాణం - Train Journey" → "train-journey"
 */
export function slugify(text: string): string {
  // If title contains " - ", take the last segment (English part)
  const parts = text.split(' - ');
  const englishPart = parts[parts.length - 1];

  return englishPart
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')   // remove non-word chars (keeps hyphens)
    .replace(/\s+/g, '-')       // spaces to hyphens
    .replace(/-+/g, '-')        // collapse multiple hyphens
    .replace(/^-+|-+$/g, '');   // trim leading/trailing hyphens
}
