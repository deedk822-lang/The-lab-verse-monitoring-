const { Perplexity } = require('@perplexity/sdk');
const fs = require('fs');
const path = require('path');

async function generateContent(prompt, outputFile) {
  try {
    const perplexity = new Perplexity({ apiKey: process.env.PERPLEXITY_API_KEY });

    const stream = await perplexity.chat.completions.create({
      model: 'sonar-medium-32k-online',
      stream: true,
      messages: [{ role: 'user', content: prompt }],
    });

    let fullContent = '';
    for await (const chunk of stream) {
      const content = chunk.choices[0].delta.content;
      if (content) {
        fullContent += content;
      }
    }

    fs.writeFileSync(outputFile, fullContent, 'utf8');
    console.log(`Content successfully generated and saved to ${outputFile}`);
    return fullContent;
  } catch (error) {
    console.error('Error generating content:', error);
    throw error;
  }
}

const prompt = process.argv[2] || 'Write a blog post about the future of AI.';
const outputFile = path.join(__dirname, 'content.html');

generateContent(prompt, outputFile);
