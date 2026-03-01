import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://guvijaya.github.io',
  base: '/SeattleDesiKids',
  integrations: [sitemap()],
  output: 'static',
});
