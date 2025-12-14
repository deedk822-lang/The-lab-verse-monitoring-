// File: .github/workflows/rankyak-sync-script.js
const { Octokit } = require('@octokit/rest');
const fs = require('fs');
const path = require('path');
const syncWordPress = require('../../scripts/sync-wordpress.js'); // Assumes the script is in the root scripts/ folder

async function run() {
  const isPush = process.env.GITHUB_EVENT_NAME === 'push';
  const githubToken = process.env.GITHUB_TOKEN;
  const [owner, repo] = process.env.GITHUB_REPOSITORY.split('/');

  if (!githubToken) {
    throw new Error('GITHUB_TOKEN is not set.');
  }

  const octokit = new Octokit({ auth: githubToken });

  let postPath, slug, title, tags;

  if (isPush) {
    console.log('Running from a push event...');
    const eventPayload = JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
    const commit = eventPayload.commits.find(c => (c.added || c.modified).some(p => p.startsWith('_posts/')));
    postPath = (commit.added || commit.modified).find(p => p.startsWith('_posts/'));

    if (!postPath) {
      console.log('No post file found in push commits. Exiting.');
      return;
    }

    // Derive slug and title from filename: YYYY-MM-DD-this-is-the-slug.md
    const filename = path.basename(postPath, '.md');
    const slugParts = filename.split('-').slice(3);
    slug = slugParts.join('-');
    title = slugParts.join(' ').replace(/\b\w/g, c => c.toUpperCase());
    tags = []; // Tags are not available from push events in this setup

  } else {
    console.log('Running from a workflow_dispatch event...');
    postPath = process.env.INPUT_POST_PATH;
    slug = process.env.INPUT_SLUG;
    title = process.env.INPUT_TITLE;
    tags = (process.env.INPUT_TAGS || '').split(',').map(s => s.trim()).filter(Boolean);
  }

  if (!postPath || !slug) {
    throw new Error('Could not determine post_path or slug.');
  }

  console.log(`Processing post: ${postPath}`);
  console.log(`Slug: ${slug}`);
  console.log(`Title: ${title}`);

  // Get file content from GitHub
  const { data: file } = await octokit.repos.getContent({
    owner,
    repo,
    path: postPath,
    ref: process.env.GITHUB_REF_NAME,
  });

  const markdownContent = Buffer.from(file.content, 'base64').toString('utf8');

  // Extract HTML block if present, otherwise use the full markdown
  const htmlMatch = markdownContent.match(/<!-- HTML START -->([\s\S]*?)<!-- HTML END -->/);
  const html = htmlMatch ? htmlMatch[1].trim() : markdownContent;

  const briaAssets = {}; // Placeholder for future use

  console.log('Syncing to WordPress...');
  await syncWordPress({ octokit, owner, repo, postPath, slug, title, html, tags, briaAssets });
  console.log('Sync complete!');
}

run().catch(error => {
  console.error(error);
  process.exit(1);
});
