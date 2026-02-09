import fetch from 'node-fetch';
import fs from 'fs/promises';

export async function publishWordPress() {
  try {
    const content = JSON.parse(await fs.readFile('./tmp/content-bundle.json', 'utf8'));

    console.log('📝 Publishing to WordPress...');

    // Use WordPress REST API (you need Application Password)
    const response = await fetch('https://public-api.wordpress.com/rest/v1.1/sites/deedk822.wordpress.com/posts/new', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.WP_API_TOKEN}`,  // Add this secret
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: `🔴 CRISIS ALERT: ${content.crisis_id}`,
        content: content.blog.replace(
          '[AFFILIATE-LINK]',
          `<a href="https://www.amazon.com/s?k=humanitarian+aid&ref=nb_sb_noss">Emergency Aid Supplies</a>`
        ),
        tags: ['South Africa', 'Crisis', 'Humanitarian'],
        categories: ['News'],
        status: 'publish'  // or 'draft' for review
      })
    });

    if (!response.ok) {
      throw new Error(`WordPress API error: ${response.statusText}`);
    }

    const post = await response.json();
    console.log('✅ WordPress published:', post.URL);

    // Output for GitHub Actions
    if (process.env.GITHUB_OUTPUT) {
      await fs.appendFile(process.env.GITHUB_OUTPUT, `blog_url=${post.URL}\n`);
    }

  } catch (error) {
    console.error('❌ Error publishing to WordPress:', error);
    process.exit(1);
  }
}

publishWordPress();
