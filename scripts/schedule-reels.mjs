import fs from 'fs/promises';
import fetch from 'node-fetch';

export async function scheduleReels() {
  try {
    const content = JSON.parse(await fs.readFile('./tmp/content-bundle.json', 'utf8'));

    console.log('📱 Scheduling Reels via SocialPilot...');

    // SocialPilot API - schedule 3 Reels
    for (let i = 1; i <= 3; i++) {
      const videoScript = content.reels[`video${i}`];

      const response = await fetch('https://api.socialpilot.co/v1/posts', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${process.env.SOCIALPILOT_API_KEY}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: videoScript.text,
          // TODO: Replace with a dynamic image, e.g., a crisis map image
          image_url: 'https://your-logo.png',
          link: process.env.BLOG_POST_URL,
          type: 'shortVideo',
          schedule_time: new Date(Date.now() + (i * 3600000)).toISOString(),  // Stagger posts
          accounts: [process.env.INSTAGRAM_ACCOUNT_ID]
        })
      });

      if (!response.ok) {
        throw new Error(`SocialPilot API error: ${response.statusText}`);
      }

      await response.json();
      console.log(`✅ Reel ${i} scheduled`);
    }
  } catch (error) {
    console.error('❌ Error scheduling Reels:', error);
    process.exit(1);
  }
}

scheduleReels();
