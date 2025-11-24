const fs = require('fs');
const path = require('path');
const https = require('https');

async function publishToWordPress(inputFile, wordpressUrl, username, password) {
  try {
    const content = fs.readFileSync(inputFile, 'utf8');
    const title = 'The Future of AI';
    const postData = JSON.stringify({
      title: title,
      content: content,
      status: 'publish'
    });

    const auth = 'Basic ' + Buffer.from(username + ':' + password).toString('base64');
    const options = {
      hostname: new URL(wordpressUrl).hostname,
      path: '/wp-json/wp/v2/posts',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': postData.length,
        'Authorization': auth
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const response = JSON.parse(data);
          const permalink = response.link;
          const updatedContent = `${content}\n<!-- Published at ${permalink} -->`;
          fs.writeFileSync(inputFile, updatedContent, 'utf8');
          console.log(`Successfully published to WordPress. Permalink: ${permalink}`);
        } else {
          console.error(`Failed to publish to WordPress. Status: ${res.statusCode}`, data);
        }
      });
    });

    req.on('error', (error) => {
      console.error('Error publishing to WordPress:', error);
    });

    req.write(postData);
    req.end();
  } catch (error) {
    console.error('Error in publishToWordPress:', error);
    throw error;
  }
}

const inputFile = path.join(__dirname, 'content.html');
const wordpressUrl = 'https://deedk822.wordpress.com';
const username = process.env.WORDPRESS_USER;
const password = process.env.WORDPRESS_APP_PASSWORD;

if (username && password) {
  publishToWordPress(inputFile, wordpressUrl, username, password);
} else {
  console.error('WordPress username or password not set in environment variables.');
}
