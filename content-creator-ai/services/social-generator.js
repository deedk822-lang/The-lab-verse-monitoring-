const logger = require('../utils/logger');

class SocialGenerator {
  async generateSocialPosts(content, topic, keywords, cta) {
    try {
      logger.info('Generating social media posts...');

      return {
        twitter: this.generateTwitterPost(topic, keywords, cta),
        linkedin: this.generateLinkedInPost(content, topic, keywords, cta),
        facebook: this.generateFacebookPost(content, topic, cta),
        instagram: this.generateInstagramPost(topic, keywords, cta),
        threads: this.generateThreadsPost(topic, keywords, cta)
      };
    } catch (error) {
      logger.error('Social post generation error:', error);
      throw error;
    }
  }

  generateTwitterPost(topic, keywords, cta) {
    const hashtags = keywords.slice(0, 3).map(k => `#${k.replace(/\s+/g, '')}`).join(' ');
    const maxLength = 280 - hashtags.length - cta.length - 10;
    
    const topicText = this.truncateText(topic, maxLength);
    
    return {
      text: `${topicText}\n\n${cta}\n\n${hashtags}`,
      length: topicText.length + cta.length + hashtags.length + 4
    };
  }

  generateLinkedInPost(content, topic, keywords, cta) {
    // Extract first paragraph or create summary
    const summary = this.extractSummary(content, 200);
    const hashtags = keywords.slice(0, 5).map(k => `#${k.replace(/\s+/g, '')}`).join(' ');
    
    const post = `🚀 ${topic}\n\n${summary}\n\n${cta}\n\n${hashtags}\n\n#ContentCreation #AI #DigitalMarketing`;
    
    return {
      text: post,
      length: post.length
    };
  }

  generateFacebookPost(content, topic, cta) {
    const summary = this.extractSummary(content, 300);
    
    const post = `${topic}\n\n${summary}\n\n${cta}\n\n👉 Learn more in the full article!`;
    
    return {
      text: post,
      length: post.length
    };
  }

  generateInstagramPost(topic, keywords, cta) {
    const hashtags = keywords.slice(0, 10).map(k => `#${k.replace(/\s+/g, '')}`).join(' ');
    const maxCaptionLength = 200;
    
    const caption = this.truncateText(topic, maxCaptionLength);
    
    const post = `${caption}\n\n${cta}\n\n${hashtags}\n\n#ContentCreator #AITools #DigitalContent`;
    
    return {
      text: post,
      length: post.length,
      note: 'Pair with relevant image or video'
    };
  }

  generateThreadsPost(topic, keywords, cta) {
    // Similar to Instagram but optimized for Threads
    const hashtags = keywords.slice(0, 3).map(k => `#${k.replace(/\s+/g, '')}`).join(' ');
    const maxLength = 500 - hashtags.length - cta.length - 10;
    
    const text = this.truncateText(topic, maxLength);
    
    return {
      text: `${text}\n\n${cta}\n\n${hashtags}`,
      length: text.length + cta.length + hashtags.length + 4
    };
  }

  extractSummary(content, maxLength) {
    // Remove markdown formatting
    const cleanText = content
      .replace(/[#*_`]/g, '')
      .replace(/\n+/g, ' ')
      .trim();

    // Get first sentence or paragraph
    const firstSentence = cleanText.split(/[.!?]+/)[0];
    
    if (firstSentence.length <= maxLength) {
      return firstSentence + '.';
    }

    return this.truncateText(cleanText, maxLength);
  }

  truncateText(text, maxLength) {
    if (text.length <= maxLength) {
      return text;
    }

    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace) + '...';
    }

    return truncated + '...';
  }

  generateEmailNewsletter(content, topic, cta) {
    const summary = this.extractSummary(content, 500);
    
    return {
      subject: `📧 ${topic}`,
      preheader: summary.substring(0, 100) + '...',
      body: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h1 style="color: #333;">${topic}</h1>
          <p style="color: #666; line-height: 1.6;">${summary}</p>
          <div style="margin: 30px 0;">
            <a href="#" style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
              ${cta}
            </a>
          </div>
          <p style="color: #999; font-size: 12px;">
            You're receiving this because you subscribed to our content updates.
          </p>
        </div>
      `
    };
  }

  generateYouTubeScript(topic, content) {
    const intro = `Hey everyone! Today we're talking about ${topic}.`;
    const summary = this.extractSummary(content, 300);
    const outro = `If you found this helpful, don't forget to like, subscribe, and hit that notification bell for more content like this!`;
    
    return {
      hook: intro,
      body: summary,
      cta: outro,
      estimatedDuration: '2-3 minutes',
      notes: 'Add B-roll footage and graphics to enhance engagement'
    };
  }
}

module.exports = new SocialGenerator();
