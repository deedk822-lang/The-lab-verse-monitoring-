// File: scripts/automated-authority-engine/vercel-router.js
// Vercel Intelligent Router - Routes content through quality checks and optimization

const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

async function routeContent() {
  const contentPath = process.env.CONTENT_PATH;
  const cdataResults = process.env.CDATA_RESULTS;

  console.log('🎯 Vercel Intelligent Router - Optimizing content...');

  if (!contentPath || !fs.existsSync(contentPath)) {
    throw new Error('Content path not found');
  }

  // Read the content
  let content = fs.readFileSync(contentPath, 'utf8');

  // Parse front matter
  const frontMatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  let frontMatter = {};
  let bodyContent = content;

  if (frontMatterMatch) {
    const fmText = frontMatterMatch[1];
    fmText.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split(':');
      if (key && valueParts.length) {
        const value = valueParts.join(':').trim().replace(/^["']|["']$/g, '');
        frontMatter[key.trim()] = value;
      }
    });
    bodyContent = content.slice(frontMatterMatch[0].length);
  }

  console.log('📋 Content Metadata:');
  console.log(`  Title: ${frontMatter.title || 'Untitled'}`);
  console.log(`  Slug: ${frontMatter.slug || 'untitled'}`);
  console.log(`  Tags: ${frontMatter.tags || 'none'}`);

  // Quality Check 1: Content Length
  console.log('✅ Quality Check 1: Content Length');
  const htmlContent = bodyContent.match(/<!-- HTML START -->([\s\S]*?)<!-- HTML END -->/)?.[1] || '';
  const wordCount = htmlContent.replace(/<[^>]+>/g, '').split(/\s+/).length;
  console.log(`  Word count: ${wordCount} words`);
  
  if (wordCount < 500) {
    console.warn('  ⚠️ Warning: Content is shorter than recommended (500+ words)');
  } else {
    console.log('  ✓ Content length is adequate');
  }

  // Quality Check 2: HTML Structure
  console.log('✅ Quality Check 2: HTML Structure');
  const hasH2 = /<h2[^>]*>/.test(htmlContent);
  const hasH3 = /<h3[^>]*>/.test(htmlContent);
  const hasParagraphs = /<p[^>]*>/.test(htmlContent);
  const hasLists = /<ul[^>]*>|<ol[^>]*>/.test(htmlContent);
  
  console.log(`  H2 headings: ${hasH2 ? '✓' : '✗'}`);
  console.log(`  H3 headings: ${hasH3 ? '✓' : '✗'}`);
  console.log(`  Paragraphs: ${hasParagraphs ? '✓' : '✗'}`);
  console.log(`  Lists: ${hasLists ? '✓' : '✗'}`);

  // Quality Check 3: SEO Optimization
  console.log('✅ Quality Check 3: SEO Optimization');
  const title = frontMatter.title || '';
  const titleLength = title.length;
  console.log(`  Title length: ${titleLength} characters`);
  
  if (titleLength < 30 || titleLength > 70) {
    console.warn('  ⚠️ Warning: Title should be 30-70 characters for optimal SEO');
  } else {
    console.log('  ✓ Title length is optimal');
  }

  // Optimization 1: Add meta description if missing
  if (!frontMatter.description) {
    const excerpt = htmlContent
      .replace(/<[^>]+>/g, '')
      .trim()
      .slice(0, 160);
    frontMatter.description = excerpt;
    console.log('  ✓ Generated meta description');
  }

  // Optimization 2: Ensure proper tags
  if (!frontMatter.tags || frontMatter.tags === 'none') {
    const keywords = (frontMatter.title || '').split(' ').slice(0, 3);
    frontMatter.tags = keywords.join(', ');
    console.log('  ✓ Generated tags from title');
  }

  // Optimization 3: Add schema.org markup
  console.log('✅ Optimization: Adding Schema.org markup');
  const schemaMarkup = `
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "${frontMatter.title}",
  "datePublished": "${frontMatter.date}",
  "dateModified": "${new Date().toISOString().split('T')[0]}",
  "author": {
    "@type": "Organization",
    "name": "Automated Authority Engine"
  },
  "publisher": {
    "@type": "Organization",
    "name": "The Lab Verse"
  },
  "description": "${frontMatter.description || ''}",
  "keywords": "${frontMatter.tags}"
}
</script>
`;

  const enhancedHtmlContent = htmlContent + '\n' + schemaMarkup;
  const enhancedBodyContent = bodyContent.replace(
    htmlContent,
    enhancedHtmlContent
  );

  // Rebuild the content with updated front matter
  const updatedFrontMatter = Object.entries(frontMatter)
    .map(([key, value]) => `${key}: "${value}"`)
    .join('\n');

  const finalContent = `---
${updatedFrontMatter}
---
${enhancedBodyContent}`;

  // Write the optimized content
  fs.writeFileSync(contentPath, finalContent, 'utf8');
  console.log('✅ Content optimized and saved');

  // Routing Decision: Determine publication strategy
  console.log('🎯 Routing Decision: Publication Strategy');
  let publishStatus = 'draft';
  let priority = 'normal';

  if (wordCount >= 1500 && hasH2 && hasH3 && hasParagraphs) {
    priority = 'high';
    console.log('  ✓ High-quality content detected - Priority: HIGH');
  } else if (wordCount >= 800) {
    priority = 'medium';
    console.log('  ✓ Good content detected - Priority: MEDIUM');
  } else {
    priority = 'low';
    console.log('  ⚠️ Content needs improvement - Priority: LOW');
  }

  // Set outputs for WordPress publishing
  const outputs = {
    final_content_path: contentPath,
    post_title: frontMatter.title,
    post_slug: frontMatter.slug,
    post_tags: frontMatter.tags,
    publish_status: publishStatus,
    priority: priority,
    word_count: wordCount
  };

  // Write outputs
  Object.entries(outputs).forEach(([key, value]) => {
    fs.appendFileSync(process.env.GITHUB_OUTPUT, `${key}=${value}\n`);
  });

  console.log('✨ Vercel routing complete!');
  console.log('📊 Final Metrics:');
  console.log(`  Priority: ${priority}`);
  console.log(`  Status: ${publishStatus}`);
  console.log(`  Word Count: ${wordCount}`);
}

routeContent().catch(error => {
  console.error('❌ Routing error:', error.message);
  process.exit(1);
});
