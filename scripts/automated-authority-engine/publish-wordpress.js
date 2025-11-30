// File: scripts/automated-authority-engine/publish-wordpress.js
// Publishes the generated content to WordPress

const fs = require('fs');
const axios = require('axios');

async function publishToWordPress() {
  const contentPath = process.env.CONTENT_PATH;
  const postTitle = process.env.POST_TITLE;
  const postSlug = process.env.POST_SLUG;
  const postTags = process.env.POST_TAGS;
  const wpSiteId = process.env.WP_SITE_ID;
  const wpUsername = process.env.WP_USERNAME;
  const wpAppPassword = process.env.WP_APP_PASSWORD;
  const wpPublishStatus = process.env.WP_PUBLISH_STATUS || 'draft';

  console.log('📤 Publishing to WordPress...');

  // Validate required environment variables
  if (!wpSiteId || !wpUsername || !wpAppPassword) {
    console.error('❌ Missing WordPress credentials');
    console.log('Required: WP_SITE_ID, WP_USERNAME, WP_APP_PASSWORD');
    console.log('⚠️ Skipping WordPress publication');
    return;
  }

  if (!contentPath || !fs.existsSync(contentPath)) {
    throw new Error('Content path not found');
  }

  // Read the content
  const content = fs.readFileSync(contentPath, 'utf8');

  // Extract HTML content
  const htmlMatch = content.match(/<!-- HTML START -->([\s\S]*?)<!-- HTML END -->/);
  if (!htmlMatch) {
    throw new Error('No HTML content found in file');
  }

  const htmlContent = htmlMatch[1].trim();

  // Extract front matter for metadata
  const frontMatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  let description = '';
  
  if (frontMatterMatch) {
    const descMatch = frontMatterMatch[1].match(/description:\s*"([^"]*)"/);
    if (descMatch) {
      description = descMatch[1];
    }
  }

  // Prepare WordPress post data
  const postData = {
    title: postTitle,
    content: htmlContent,
    excerpt: description || htmlContent.replace(/<[^>]+>/g, '').slice(0, 160),
    status: wpPublishStatus,
    slug: postSlug,
    format: 'standard',
    categories: [],
    tags: postTags ? postTags.split(',').map(t => t.trim()) : []
  };

  console.log('📝 Post Details:');
  console.log(`  Title: ${postTitle}`);
  console.log(`  Slug: ${postSlug}`);
  console.log(`  Status: ${wpPublishStatus}`);
  console.log(`  Tags: ${postTags || 'none'}`);

  try {
    // WordPress.com REST API endpoint
    const apiUrl = `https://public-api.wordpress.com/wp/v2/sites/${wpSiteId}/posts`;
    
    // Create authentication header
    const auth = Buffer.from(`${wpUsername}:${wpAppPassword}`).toString('base64');
    
    console.log('🔐 Authenticating with WordPress...');
    
    // Make the API request
    const response = await axios.post(apiUrl, postData, {
      headers: {
        'Authorization': `Basic ${auth}`,
        'Content-Type': 'application/json'
      }
    });

    const wpPost = response.data;
    const wpUrl = wpPost.link || wpPost.guid?.rendered || '#';

    console.log('✅ Successfully published to WordPress!');
    console.log(`📍 WordPress URL: ${wpUrl}`);
    console.log(`🆔 Post ID: ${wpPost.id}`);

    // Update the markdown file with WordPress permalink
    const updatedContent = content.replace(
      /^---\n/,
      `---\nwordpress_url: "${wpUrl}"\nwordpress_id: ${wpPost.id}\n`
    );

    fs.writeFileSync(contentPath, updatedContent, 'utf8');
    console.log('✅ Updated content file with WordPress URL');

    // Set output for workflow summary
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `wordpress_url=${wpUrl}\n`);
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `wordpress_id=${wpPost.id}\n`);

    console.log('🎉 Publication complete!');

  } catch (error) {
    console.error('❌ WordPress publication failed');
    
    if (error.response) {
      console.error(`Status: ${error.response.status}`);
      console.error(`Message: ${JSON.stringify(error.response.data, null, 2)}`);
      
      // Provide helpful error messages
      if (error.response.status === 401) {
        console.error('Authentication failed. Please check WP_USERNAME and WP_APP_PASSWORD');
      } else if (error.response.status === 403) {
        console.error('Permission denied. Ensure the app password has sufficient permissions');
      } else if (error.response.status === 404) {
        console.error('Site not found. Please check WP_SITE_ID');
      }
    } else {
      console.error(`Error: ${error.message}`);
    }

    // Don't fail the workflow, just log the error
    console.log('⚠️ Content was generated but not published to WordPress');
    console.log('📁 Content saved locally at:', contentPath);
    
    // Set a placeholder URL
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `wordpress_url=pending\n`);
  }
}

publishToWordPress().catch(error => {
  console.error('❌ Fatal error:', error.message);
  process.exit(1);
});
