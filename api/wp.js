/* =====  WORDPRESS.COM MODULE  ===== */
// Inserted by integration assistant on 2025-11-06
import fetch from 'node-fetch';

const WP_SITE = process.env.WP_SITE_ID; // e.g., k822 (site id or domain)
const WP_USER = process.env.WP_USERNAME; // e.g., deedk22
const WP_PASS = process.env.WP_APP_PASSWORD; // 24-char app password with spaces
const WP_STATUS = process.env.WP_PUBLISH_STATUS || 'draft'; // 'draft' | 'publish'
const WP_FEATURED = (process.env.WP_FEATURED_IMAGE || 'true').toLowerCase() === 'true';

const WP_AUTH = 'Basic ' + Buffer.from(`${WP_USER}:${WP_PASS}`).toString('base64');

export async function uploadMediaToWordPress({ buffer, filename, mime = 'image/jpeg', title = '' }) {
  // Use proper multipart/form-data with boundary
  const boundary = '----wp-media-' + Math.random().toString(36).slice(2);
  const preamble = Buffer.from(
    `--${boundary}\r\n` +
      `Content-Disposition: form-data; name="media[]"; filename="${filename}"\r\n` +
      `Content-Type: ${mime}\r\n\r\n`
  );
  const epilogue = Buffer.from(`\r\n--${boundary}--\r\n`);
  const body = Buffer.concat([preamble, buffer, epilogue]);

  const res = await fetch(`https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/media/new`, {
    method: 'POST',
    headers: {
      Authorization: WP_AUTH,
      'Content-Type': `multipart/form-data; boundary=${boundary}`,
      'Accept': 'application/json',
    },
    body,
  });
  const data = await res.json();
  if (!res.ok || data.error) {
    throw new Error(`Media upload failed: ${data?.message || res.statusText}`);
  }
  const media = Array.isArray(data.media) ? data.media[0] : data.media;
  return { id: media?.ID, url: media?.URL || media?.URL, meta: media };
}

export function buildWordPressContent({ html, heroId }) {
  const heroBlock = heroId
    ? `<!-- wp:image {"id":${heroId},"sizeSlug":"large"} -->\n<figure class="wp-block-image size-large"><img src="" alt="" class="wp-image-${heroId}"/></figure>\n<!-- /wp:image -->\n`
    : '';
  return `${heroBlock}<!-- wp:html -->\n${html}\n<!-- /wp:html -->`;
}

export async function createOrUpdateWordPressPost({ title, slug, html, excerpt, tags = [], heroId }) {
  // 1) Check if post exists via slug
  const existingRes = await fetch(
    `https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/posts/slug:${encodeURIComponent(slug)}`,
    { headers: { Authorization: WP_AUTH, 'Accept': 'application/json' } }
  );
  const existing = existingRes.ok ? await existingRes.json() : null;

  // 2) Prepare payload
  const payload = {
    title,
    content: buildWordPressContent({ html, heroId }),
    excerpt,
    tags: (tags || []).join(','),
    slug,
    status: WP_STATUS,
    ...(WP_FEATURED && heroId ? { featured_image: heroId } : {}),
  };

  // 3) Create or update
  const endpoint = existing?.ID
    ? `https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/posts/${existing.ID}`
    : `https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/posts/new`;

  const wpRes = await fetch(endpoint, {
    method: 'POST',
    headers: { Authorization: WP_AUTH, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const wpData = await wpRes.json();
  if (!wpRes.ok || wpData.error) {
    throw new Error(`WP post error: ${wpData?.message || wpRes.statusText}`);
  }
  return { id: wpData.ID, url: wpData.URL, slug: wpData.slug };
}
