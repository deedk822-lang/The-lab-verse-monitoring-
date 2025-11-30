// File: scripts/automated-authority-engine/generate-content.js
// Generates high-quality content using AI (Perplexity Sonar or OpenAI)

const fs = require('fs');
const path = require('path');
const axios = require('axios');

async function generateContent() {
  const keyword = process.env.KEYWORD;
  const contentType = process.env.CONTENT_TYPE || 'article';
  const sonarApiKey = process.env.SONAR_API_KEY;
  const openaiApiKey = process.env.OPENAI_API_KEY;

  if (!keyword) {
    throw new Error('KEYWORD environment variable is required');
  }

  console.log(`🚀 Generating ${contentType} about: "${keyword}"`);

  // Prepare the prompt based on content type
  let prompt = '';
  switch (contentType) {
    case 'guide':
      prompt = `Write a comprehensive, authoritative guide about "${keyword}". Include:
- An engaging introduction
- Key concepts and definitions
- Step-by-step explanations
- Best practices and tips
- Common pitfalls to avoid
- Actionable takeaways
- Conclusion with future outlook

Format the content in HTML with proper headings (h2, h3), paragraphs, and lists. Make it SEO-optimized and reader-friendly. Aim for 1500-2000 words.`;
      break;
    
    case 'analysis':
      prompt = `Write an in-depth analysis of "${keyword}". Include:
- Executive summary
- Current state and trends
- Key players and stakeholders
- Opportunities and challenges
- Data-driven insights
- Expert perspectives
- Future predictions
- Conclusion with recommendations

Format the content in HTML with proper headings (h2, h3), paragraphs, and lists. Make it authoritative and well-researched. Aim for 1500-2000 words.`;
      break;
    
    default: // article
      prompt = `Write a comprehensive, engaging article about "${keyword}". Include:
- A compelling introduction that hooks the reader
- Well-structured body sections with clear headings
- Evidence-based insights and examples
- Practical applications or implications
- Expert perspectives or quotes
- A strong conclusion with key takeaways

Format the content in HTML with proper headings (h2, h3), paragraphs, and lists. Make it informative, authoritative, and SEO-optimized. Aim for 1500-2000 words.`;
  }

  let content = '';
  let title = '';

  // Try Perplexity Sonar first (better for research-based content)
  if (sonarApiKey) {
    try {
      console.log('📡 Using Perplexity Sonar API...');
      const response = await axios.post(
        'https://api.perplexity.ai/chat/completions',
        {
          model: 'sonar-pro',
          messages: [
            {
              role: 'system',
              content: 'You are an expert content writer who creates authoritative, well-researched articles with proper HTML formatting.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          temperature: 0.7,
          max_tokens: 4000
        },
        {
          headers: {
            'Authorization': `Bearer ${sonarApiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      content = response.data.choices[0].message.content;
      
      // Generate a title
      const titleResponse = await axios.post(
        'https://api.perplexity.ai/chat/completions',
        {
          model: 'sonar-pro',
          messages: [
            {
              role: 'user',
              content: `Create a compelling, SEO-optimized title (60-70 characters) for an article about: "${keyword}". Return only the title, nothing else.`
            }
          ],
          temperature: 0.8,
          max_tokens: 100
        },
        {
          headers: {
            'Authorization': `Bearer ${sonarApiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      title = titleResponse.data.choices[0].message.content.trim().replace(/^["']|["']$/g, '');
      
      console.log('✅ Content generated successfully with Perplexity Sonar');
    } catch (error) {
      console.error('⚠️ Perplexity Sonar failed:', error.message);
      console.log('🔄 Falling back to OpenAI...');
    }
  }

  // Fallback to OpenAI if Sonar failed or wasn't available
  if (!content && openaiApiKey) {
    try {
      console.log('📡 Using OpenAI API...');
      const response = await axios.post(
        'https://api.openai.com/v1/chat/completions',
        {
          model: 'gpt-4',
          messages: [
            {
              role: 'system',
              content: 'You are an expert content writer who creates authoritative, well-researched articles with proper HTML formatting.'
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          temperature: 0.7,
          max_tokens: 4000
        },
        {
          headers: {
            'Authorization': `Bearer ${openaiApiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      content = response.data.choices[0].message.content;
      
      // Generate a title
      const titleResponse = await axios.post(
        'https://api.openai.com/v1/chat/completions',
        {
          model: 'gpt-4',
          messages: [
            {
              role: 'user',
              content: `Create a compelling, SEO-optimized title (60-70 characters) for an article about: "${keyword}". Return only the title, nothing else.`
            }
          ],
          temperature: 0.8,
          max_tokens: 100
        },
        {
          headers: {
            'Authorization': `Bearer ${openaiApiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      title = titleResponse.data.choices[0].message.content.trim().replace(/^["']|["']$/g, '');
      
      console.log('✅ Content generated successfully with OpenAI');
    } catch (error) {
      console.error('❌ OpenAI also failed:', error.message);
      throw new Error('All AI providers failed to generate content');
    }
  }

  if (!content) {
    throw new Error('No AI API keys available. Please set SONAR_API_KEY or OPENAI_API_KEY');
  }

  // Create output directory
  const outputDir = path.join(process.cwd(), '_posts');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // Generate filename with date
  const date = new Date().toISOString().split('T')[0];
  const slug = keyword.toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  const filename = `${date}-${slug}.md`;
  const filepath = path.join(outputDir, filename);

  // Create markdown with front matter
  const markdown = `---
title: "${title}"
date: ${date}
slug: ${slug}
tags: ${keyword.split(' ').slice(0, 3).join(', ')}
status: draft
generated_by: automated-authority-engine
---

<!-- HTML START -->
${content}
<!-- HTML END -->
`;

  fs.writeFileSync(filepath, markdown, 'utf8');
  console.log(`📝 Content saved to: ${filepath}`);

  // Set output for next step
  const output = `content_path=${filepath}`;
  fs.appendFileSync(process.env.GITHUB_OUTPUT, output + '\n');

  console.log('✨ Content generation complete!');
  console.log(`Title: ${title}`);
  console.log(`Slug: ${slug}`);
}

generateContent().catch(error => {
  console.error('❌ Error:', error.message);
  process.exit(1);
});
