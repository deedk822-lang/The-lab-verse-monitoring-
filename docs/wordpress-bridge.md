# RankYak → WordPress.com Bridge (k822.wordpress.com)

This adds an automated path from RankYak → GitHub → WordPress.com while preserving your Unito → Asana flow.

## What it does
- On push to `_posts/*.md` or manual dispatch, publishes the post to WordPress.com using Application Passwords.
- Uploads Bria-generated hero/OG images to the WP Media Library (when provided by the bridge).
- Writes the WordPress permalink back into the Markdown front-matter as `wordpress_permalink:` so Unito propagates it to Asana.

## Setup (one time)
1) Generate a WordPress.com Application Password
- Go to https://wordpress.com/me/security → Application Passwords
- Name: `rankyak-bridge` → Generate → copy the 24‑char password
- Note your site id: `k822` (same as k822.wordpress.com)

2) Add secrets to this GitHub repo (Settings → Secrets and variables → Actions)
- `WP_SITE_ID` = `k822`
- `WP_USERNAME` = your WordPress.com username (e.g., `deedk22`)
- `WP_APP_PASSWORD` = the application password from step 1

3) Optional variables (Repository → Settings → Variables)
- `WP_PUBLISH_STATUS` = `draft` (default) or `publish`
- `WP_FEATURED_IMAGE` = `true` (default) or `false`

## Files added
- `api/wp.js` – WordPress.com REST client (media upload + create/update post)
- `scripts/sync-wordpress.js` – Helper that uploads media, posts to WP, and writes permalink to front-matter
- `.github/workflows/rankyak-wordpress-sync.yml` – CI that runs on push to `_posts/**.md` or manual dispatch

## How to use
- Commit a Markdown post under `_posts/` (e.g., `_posts/2025-11-06-best-winter-hikes.md`).
- The workflow runs, publishes the post to WordPress (draft by default), and writes back:

```yaml
---
wordpress_permalink: "https://k822.wordpress.com/2025/11/06/best-winter-hikes/"
---
```

## Hero & OG images (from Bria)
- The helper accepts binary buffers; when wired from your Vercel bridge, pass:
```js
await syncWordPress({
  ...,
  briaAssets: {
    hero: { buffer, mime: 'image/jpeg' },
    og:   { buffer, mime: 'image/png' }
  }
});
```
- Images are uploaded to WP Media Library and `hero` can be set as `featured_image`.

## Local test (optional)
- You can run the helper locally with a personal token and Octokit to simulate the write-back; prefer CI usage for secrets safety.

## Notes
- Media upload uses `multipart/form-data` per WordPress.com REST docs.
- If an existing post with the same slug exists, it is updated; otherwise a new draft/published post is created.
- If your Markdown includes an `<!-- HTML START --> … <!-- HTML END -->` block, that HTML is used as the content. Otherwise the Markdown is embedded as a Gutenberg HTML block.

## Troubleshooting
- 401/403: Verify `WP_USERNAME` and `WP_APP_PASSWORD`, and that you’re targeting the correct `WP_SITE_ID`.
- Media upload errors: ensure correct MIME (`image/jpeg` or `image/png`) and that buffers are valid.
- Permalink not written: check the Action logs and confirm the `_posts/` path and branch name.
