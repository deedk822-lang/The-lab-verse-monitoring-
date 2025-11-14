// RankYak → Vercel Bridge → GitHub → WordPress.com sync
// Inserts WP permalink into front-matter and uploads Bria images

import { createOrUpdateWordPressPost, uploadMediaToWordPress } from '../api/wp.js';
import fs from 'fs';
import path from 'path';

export default async function syncWordPress({
  octokit,
  owner,
  repo,
  branch = process.env.GITHUB_BRANCH || 'main',
  postPath, // path in repo, e.g., _posts/2025-11-06-slug.md
  slug,
  title,
  html,
  tags = [],
  briaAssets = {}, // { hero: { buffer, mime }, og: { buffer, mime } }
}) {
  // 1) Upload media if present
  let heroId = null;
  let ogId = null;
  if (briaAssets?.hero?.buffer) {
    heroId = (
      await uploadMediaToWordPress({
        buffer: briaAssets.hero.buffer,
        filename: `${slug}-hero.${(briaAssets.hero.mime || 'image/jpeg').split('/')[1]}`,
        mime: briaAssets.hero.mime || 'image/jpeg',
        title: `${title} – Hero`,
      })
    ).id;
  }
  if (briaAssets?.og?.buffer) {
    ogId = (
      await uploadMediaToWordPress({
        buffer: briaAssets.og.buffer,
        filename: `${slug}-og.${(briaAssets.og.mime || 'image/png').split('/')[1]}`,
        mime: briaAssets.og.mime || 'image/png',
        title: `${title} – OG`,
      })
    ).id;
  }

  // 2) Create/update WordPress post
  const excerpt = html?.replace(/<[^>]+>/g, '').slice(0, 160) || '';
  const wp = await createOrUpdateWordPressPost({ title, slug, html, excerpt, tags, heroId, ogId });

  // 3) Read existing file to get sha
  const { data: file } = await octokit.rest.repos.getContent({ owner, repo, path: postPath, ref: branch });
  const contentB64 = file.content.replace(/\n/g, '');
  const md = Buffer.from(contentB64, 'base64').toString('utf8');

  // 4) Inject permalink into front-matter
  const fmMatch = md.match(/^---[\s\S]*?---/);
  let updatedMd;
  if (fmMatch) {
    const fm = fmMatch[0];
    const without = md.slice(fm.length);
    const injected = fm.includes('wordpress_permalink:')
      ? fm.replace(/wordpress_permalink:.*/,
                   `wordpress_permalink: "${wp.url}"`)
      : fm.replace(/---\s*$/, `wordpress_permalink: "${wp.url}"\n---`);
    updatedMd = injected + without;
  } else {
    updatedMd = `---\nwordpress_permalink: "${wp.url}"\n---\n` + md;
  }

  // 5) Write back to GitHub
  await octokit.rest.repos.createOrUpdateFileContents({
    owner,
    repo,
    path: postPath,
    message: `🔗 WordPress permalink added: ${wp.url}`,
    content: Buffer.from(updatedMd, 'utf8').toString('base64'),
    sha: file.sha,
    branch,
  });

  return wp;
}
