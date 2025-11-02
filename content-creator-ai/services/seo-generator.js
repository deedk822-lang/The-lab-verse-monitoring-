const logger = require('../utils/logger');

class SEOGenerator {
  async generateSEOMetadata(content, keywords, topic) {
    try {
      logger.info('Generating SEO metadata...');

      const title = this.generateTitle(topic, content);
      const metaDescription = this.generateMetaDescription(content, topic);
      const keywordTags = this.generateKeywords(keywords, content);
      const ogTags = this.generateOGTags(title, metaDescription, topic);
      const structuredData = this.generateStructuredData(title, content, topic);

      return {
        title,
        metaDescription,
        keywords: keywordTags,
        ogTags,
        structuredData,
        readabilityScore: this.calculateReadabilityScore(content)
      };
    } catch (error) {
      logger.error('SEO generation error:', error);
      throw error;
    }
  }

  generateTitle(topic, content) {
    // Extract first heading or create from topic
    const headingMatch = content.match(/^#\s+(.+)$/m) || content.match(/^(.+)\n/);
    
    if (headingMatch) {
      return headingMatch[1].trim().substring(0, 60);
    }

    // Create title from topic
    const words = topic.split(' ');
    const title = words.map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    return title.substring(0, 60);
  }

  generateMetaDescription(content, topic) {
    // Extract first paragraph or sentence
    const text = content.replace(/[#*_`]/g, '').trim();
    const firstParagraph = text.split('\n\n')[0];
    const description = firstParagraph.substring(0, 155);

    // Ensure it ends properly
    const lastPeriod = description.lastIndexOf('.');
    if (lastPeriod > 100) {
      return description.substring(0, lastPeriod + 1);
    }

    return description + '...';
  }

  generateKeywords(providedKeywords, content) {
    const keywords = [...providedKeywords];

    // Extract additional keywords from content
    const words = content.toLowerCase()
      .replace(/[^a-z0-9\s]/g, '')
      .split(/\s+/)
      .filter(w => w.length > 4);

    // Count word frequency
    const wordFreq = {};
    words.forEach(word => {
      wordFreq[word] = (wordFreq[word] || 0) + 1;
    });

    // Get top words
    const topWords = Object.entries(wordFreq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);

    // Combine and deduplicate
    const allKeywords = [...new Set([...keywords, ...topWords])];
    return allKeywords.slice(0, 15);
  }

  generateOGTags(title, description, topic) {
    return {
      'og:title': title,
      'og:description': description,
      'og:type': 'article',
      'og:site_name': 'Content Creator AI',
      'twitter:card': 'summary_large_image',
      'twitter:title': title,
      'twitter:description': description
    };
  }

  generateStructuredData(title, content, topic) {
    const wordCount = content.split(/\s+/).length;
    const readingTime = Math.ceil(wordCount / 200); // Average reading speed

    return {
      '@context': 'https://schema.org',
      '@type': 'Article',
      'headline': title,
      'description': this.generateMetaDescription(content, topic),
      'wordCount': wordCount,
      'timeRequired': `PT${readingTime}M`,
      'author': {
        '@type': 'Organization',
        'name': 'Content Creator AI'
      },
      'publisher': {
        '@type': 'Organization',
        'name': 'Content Creator AI'
      },
      'datePublished': new Date().toISOString(),
      'dateModified': new Date().toISOString()
    };
  }

  calculateReadabilityScore(content) {
    // Simple Flesch Reading Ease approximation
    const text = content.replace(/[^a-zA-Z0-9\s.]/g, '');
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
    const words = text.split(/\s+/).filter(w => w.length > 0);
    const syllables = words.reduce((sum, word) => sum + this.countSyllables(word), 0);

    if (sentences.length === 0 || words.length === 0) {
      return { score: 0, level: 'unknown' };
    }

    const avgSentenceLength = words.length / sentences.length;
    const avgSyllablesPerWord = syllables / words.length;

    const score = 206.835 - (1.015 * avgSentenceLength) - (84.6 * avgSyllablesPerWord);
    const clampedScore = Math.max(0, Math.min(100, score));

    let level;
    if (clampedScore >= 90) level = 'Very Easy';
    else if (clampedScore >= 80) level = 'Easy';
    else if (clampedScore >= 70) level = 'Fairly Easy';
    else if (clampedScore >= 60) level = 'Standard';
    else if (clampedScore >= 50) level = 'Fairly Difficult';
    else if (clampedScore >= 30) level = 'Difficult';
    else level = 'Very Difficult';

    return {
      score: Math.round(clampedScore),
      level
    };
  }

  countSyllables(word) {
    word = word.toLowerCase();
    if (word.length <= 3) return 1;
    
    word = word.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '');
    word = word.replace(/^y/, '');
    const matches = word.match(/[aeiouy]{1,2}/g);
    
    return matches ? matches.length : 1;
  }
}

module.exports = new SEOGenerator();
