/**
 * Ayrshare Social Media Posting Script
 * 
 * This script allows you to post content to multiple social media platforms
 * using the Ayrshare API.
 * 
 * Usage:
 *   node ayrshare/post-to-social.js "Your post content here"
 */

const https = require('https');

// Configuration
const AYRSHARE_API_KEY = process.env.ARYSHARE_API_KEY;
const API_URL = 'api.ayrshare.com';
const API_PATH = '/api/post';

/**
 * Post content to social media platforms
 * @param {string} postContent - The text content to post
 * @param {string[]} platforms - Array of platform names
 * @param {string[]} mediaUrls - Optional array of media URLs
 */
function postToSocial(postContent, platforms = ['twitter', 'facebook', 'linkedin'], mediaUrls = []) {
  if (!AYRSHARE_API_KEY) {
    console.error('❌ Error: ARYSHARE_API_KEY environment variable is not set!');
    console.log('\nTo use this script:');
    console.log('1. In GitHub Actions, the secret is automatically available');
    console.log('2. For local usage: export ARYSHARE_API_KEY=your_api_key_here');
    process.exit(1);
  }

  const postData = JSON.stringify({
    post: postContent,
    platforms: platforms,
    ...(mediaUrls.length > 0 && { mediaUrls: mediaUrls })
  });

  const options = {
    hostname: API_URL,
    path: API_PATH,
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${AYRSHARE_API_KEY}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(postData)
    }
  };

  console.log('📤 Posting to social media...');
  console.log(`📝 Content: ${postContent}`);
  console.log(`🎯 Platforms: ${platforms.join(', ')}`);
  
  if (mediaUrls.length > 0) {
    console.log(`🖼️  Media: ${mediaUrls.join(', ')}`);
  }

  const req = https.request(options, (res) => {
    let data = '';

    res.on('data', (chunk) => {
      data += chunk;
    });

    res.on('end', () => {
      try {
        const response = JSON.parse(data);
        
        if (res.statusCode === 200 && response.status === 'success') {
          console.log('\n✅ Successfully posted to social media!');
          console.log('\n📊 Results:');
          
          response.postIds.forEach((result) => {
            if (result.status === 'success') {
              console.log(`\n✓ ${result.platform.toUpperCase()}:`);
              console.log(`  Post ID: ${result.id}`);
              if (result.postUrl) {
                console.log(`  URL: ${result.postUrl}`);
              }
            } else {
              console.log(`\n✗ ${result.platform.toUpperCase()}: ${result.status}`);
            }
          });
          
          // Save results to file for GitHub Actions artifact
          const fs = require('fs');
          fs.writeFileSync('ayrshare-post-results.json', JSON.stringify(response, null, 2));
          console.log('\n💾 Results saved to ayrshare-post-results.json');
          
        } else {
          console.error('\n❌ Posting failed:');
          console.error(JSON.stringify(response, null, 2));
          process.exit(1);
        }
      } catch (error) {
        console.error('\n❌ Error parsing response:', error.message);
        console.error('Raw response:', data);
        process.exit(1);
      }
    });
  });

  req.on('error', (error) => {
    console.error('\n❌ Request error:', error.message);
    process.exit(1);
  });

  req.write(postData);
  req.end();
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('Usage: node ayrshare/post-to-social.js "Your post content" [platforms] [mediaUrls]');
    console.log('\nExamples:');
    console.log('  node ayrshare/post-to-social.js "Hello World!"');
    console.log('  node ayrshare/post-to-social.js "Check this out!" "twitter,linkedin"');
    console.log('  node ayrshare/post-to-social.js "Great news!" "twitter,facebook" "https://example.com/image.jpg"');
    process.exit(1);
  }

  const postContent = args[0];
  const platforms = args[1] ? args[1].split(',') : ['twitter', 'facebook', 'linkedin'];
  const mediaUrls = args[2] ? args[2].split(',') : [];

  postToSocial(postContent, platforms, mediaUrls);
}

module.exports = { postToSocial };
