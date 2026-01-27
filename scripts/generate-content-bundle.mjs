import fs from 'fs/promises';
import { OpenAI } from 'openai';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function generateContent() {
  try {
    const crisis = JSON.parse(await fs.readFile('./tmp/crisis.json', 'utf8'));

    console.log('🎨 Generating monetization content...');

    // WordPress Blog Post (SEO optimized)
    const blogResponse = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{
        role: 'system',
        content: 'Write an 800-word SEO blog post. Include keywords: "South Africa crisis", "humanitarian aid", "news". Add affiliate placeholders: [AFFILIATE-LINK].'
      }, {
        role: 'user',
        content: `Crisis: ${crisis.title}\nSources: ${crisis.sources.map(s => s.title).join('\n')}`
      }]
    });

    // MailChimp Newsletter
    const newsletterResponse = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{
        role: 'system',
        content: 'Write a MailChimp newsletter. Include: crisis summary, impact stats, sponsor mention placeholder [SPONSOR], CTA to premium Grafana dashboard.'
      }, {
        role: 'user',
        content: `Crisis: ${crisis.description}`
      }]
    });

    // SocialPilot Reels Scripts (3 videos)
    const reelsResponse = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      messages: [{
        role: 'system',
        content: 'Create 3 Reels scripts (15s each). Format: {"video1": {"text": "...", "hashtags": "#SouthAfrica #Crisis"}, ...}'
      }, {
        role: 'user',
        content: `Crisis: ${crisis.title}`
      }]
    });

    const bundle = {
      blog: blogResponse.choices[0].message.content,
      newsletter: newsletterResponse.choices[0].message.content,
      reels: JSON.parse(reelsResponse.choices[0].message.content),
      crisis_id: crisis.crisis_id,
      timestamp: new Date().toISOString()
    };

    await fs.writeFile('./tmp/content-bundle.json', JSON.stringify(bundle, null, 2));
    console.log('✅ Content bundle ready');
  } catch (error) {
    console.error('❌ Error generating content bundle:', error);
    process.exit(1);
  }
}

generateContent();
