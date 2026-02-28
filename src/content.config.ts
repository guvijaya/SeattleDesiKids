import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const essays = defineCollection({
  loader: glob({ pattern: '**/[a-z]*.md', base: './src/content/essays' }),
  schema: z.object({
    language: z.enum(['english', 'hindi', 'telugu', 'marathi', 'kannada', 'tamil']),
    title: z.string(),
    translator: z.string().optional(),
    sourceUrl: z.string().url().optional(),
    fetchedAt: z.string().optional(),
  }),
});

export const collections = { essays };
