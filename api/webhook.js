// api/webhook.js - Vercel Serverless Function
// RankYak → GitHub → Unito (→ Asana) Bridge

import { Octokit } from '@octokit/rest';
import crypto from 'crypto';
import fetch from 'node-fetch'; // Added fetch for Slack notification

// Initialize GitHub client
const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// Configuration
const config = {
  owner: process.env.GITHUB_OWNER,
  repo: process.env.GITHUB_REPO,
  branch: process.env.GITHUB_BRANCH || 'main',
  webhookSecret: process.env.WEBHOOK_SECRET,
  createPR: process.env.CREATE_PR === 'true',
  slackWebhook: process.env.SLACK_WEBHOOK_URL,
  contentDir: process.env.CONTENT_DIR || '_posts'
};

/**
 * Verify webhook signature from RankYak
 */
function verifySignature(payload, signature, secret) {
  if (!signature || !secret) return false;
  
  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(payload).digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}

/**
 * Convert RankYak HTML to Markdown
 */
function htmlToMarkdown(html) {
  if (!html) return '';
  
  return html
    // Headers
    .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
    .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
    .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
    // Paragraphs
    .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
    // Links
    .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
    // Bold/Italic
    .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
    .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
    // Lists
    .replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n')
    .replace(/<ul[^>]*>/gi, '\n')
    .replace(/<\/ul>/gi, '\n')
    // Images
    .replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/gi, '![$2]($1)')
    // Code
    .replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`')
    .replace(/<pre[^>]*>(.*?)<\/pre>/gi, '```\n$1\n```\n')
    // Clean up HTML tags
    .replace(/<[^>]*>/g, '')
    // Clean up extra whitespace
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

/**
 * Generate slug from title
 */
function generateSlug(title) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .substring(0, 60);
}

/**
 * Create markdown file content
 */
function createMarkdownContent(article) {
  const frontmatter = {
    title: article.title,
    slug: article.slug || generateSlug(article.title),
    date: article.published_at || new Date().toISOString().split('T')[0],
    author: article.author?.name || 'Unknown',
    tags: article.tags || [],
    categories: article.categories || [],
    rankyak_id: article.id,
    status: 'published',
    seo_title: article.seo?.title || article.title,
    seo_description: article.seo?.meta_description || article.excerpt || '',
    featured_image: article.featured_image_url || ''
  };

  const yaml = Object.entries(frontmatter)
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `${key}: [${value.join(', ')}]`;
      }
      return `${key}: "${value}"`;
    })
    .join('\n');

  const body = htmlToMarkdown(article.content || '');

  return `---
${yaml}
---

${body}
`;
}

/**
 * Get file path for article
 */
function getFilePath(article) {
  const date = (article.published_at || new Date().toISOString()).split('T')[0];
  const slug = article.slug || generateSlug(article.title);
  return `${config.contentDir}/${date}-${slug}.md`;
}

/**
 * Commit file to GitHub
 */
async function commitToGitHub(filePath, content, commitMessage, article) {
  try {
    // Get current file (if exists)
    let sha;
    try {
      const { data } = await octokit.repos.getContent({
        owner: config.owner,
        repo: config.repo,
        path: filePath,
        ref: config.branch
      });
      sha = data.sha;
    } catch (error) {
      // File doesn't exist, that's okay
      sha = null;
    }

    // Create or update file
    const { data } = await octokit.repos.createOrUpdateFileContents({
      owner: config.owner,
      repo: config.repo,
      path: filePath,
      message: commitMessage,
      content: Buffer.from(content).toString('base64'),
      sha: sha,
      branch: config.branch
    });

    return {
      success: true,
      commit: data.commit,
      url: data.content.html_url
    };
  } catch (error) {
    console.error('GitHub commit error:', error);
    throw error;
  }
}

/**
 * Create pull request
 */
async function createPullRequest(article, filePath, content) {
  const branchName = `rankyak/${article.id}-${Date.now()}`;
  const prTitle = `📝 ${article.title}`;
  const prBody = `
## RankYak Article Sync

**Title:** ${article.title}
**Author:** ${article.author?.name || 'Unknown'}
**Published:** ${article.published_at || 'Just now'}

### Changes
- Added/Updated: \`${filePath}\`

### Metadata
- **RankYak ID:** ${article.id}
- **Tags:** ${(article.tags || []).join(', ')}
- **Categories:** ${(article.categories || []).join(', ')}

### Preview
${article.excerpt || 'No excerpt available'}

---
*Automatically synced from RankYak. Review and merge to publish.*
`;

  try {
    // Get base branch reference
    const { data: baseRef } = await octokit.git.getRef({
      owner: config.owner,
      repo: config.repo,
      ref: `heads/${config.branch}`
    });

    // Create new branch
    await octokit.git.createRef({
      owner: config.owner,
      repo: config.repo,
      ref: `refs/heads/${branchName}`,
      sha: baseRef.object.sha
    });

    // Commit to new branch
    await commitToGitHub(
      filePath,
      content,
      `Add: ${article.title}`,
      article
    );

    // Create pull request
    const { data: pr } = await octokit.pulls.create({
      owner: config.owner,
      repo: config.repo,
      title: prTitle,
      body: prBody,
      head: branchName,
      base: config.branch
    });

    // Add labels
    await octokit.issues.addLabels({
      owner: config.owner,
      repo: config.repo,
      issue_number: pr.number,
      labels: ['rankyak', 'content', 'needs-review']
    });

    return {
      success: true,
      pr: pr,
      url: pr.html_url
    };
  } catch (error) {
    console.error('PR creation error:', error);
    throw error;
  }
}

/**
 * Send Slack notification
 */
async function notifySlack(article, result) {
  if (!config.slackWebhook) return;

  const message = {
    text: `📝 New content synced from RankYak`,
    blocks: [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: article.title
        }
      },
      {
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*Author:*\n${article.author?.name || 'Unknown'}`
          },
          {
            type: 'mrkdwn',
            text: `*Status:*\n${result.pr ? 'PR Created' : 'Committed'}`
          }
        ]
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Tags:* ${(article.tags || []).join(', ') || 'None'}`
        }
      },
      {
        type: 'actions',
        elements: [
          {
            type: 'button',
            text: {
              type: 'plain_text',
              text: result.pr ? 'View PR' : 'View Commit'
            },
            url: result.url
          }
        ]
      }
    ]
  };

  try {
    await fetch(config.slackWebhook, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message)
    });
  } catch (error) {
    console.error('Slack notification error:', error);
  }
}

/**
 * Main webhook handler
 */
export default async function handler(req, res) {
  // Only accept POST
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Verify webhook signature
    const signature = req.headers['x-webhook-signature'];
    const rawBody = JSON.stringify(req.body);
    
    if (!verifySignature(rawBody, signature, config.webhookSecret)) {
      console.error('Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Parse RankYak payload
    const { event, article } = req.body;

    // Only handle publish events
    if (!event || !event.includes('published')) {
      return res.status(200).json({ 
        message: 'Event ignored',
        event 
      });
    }

    // Validate article data
    if (!article || !article.title) {
      return res.status(400).json({ error: 'Invalid article data' });
    }

    console.log(`Processing article: ${article.title}`);

    // Generate markdown content
    const content = createMarkdownContent(article);
    const filePath = getFilePath(article);

    // Commit or create PR
    let result;
    if (config.createPR) {
      result = await createPullRequest(article, filePath, content);
      console.log(`PR created: ${result.url}`);
    } else {
      result = await commitToGitHub(
        filePath,
        content,
        `Published: ${article.title}`,
        article
      );
      console.log(`Committed: ${result.url}`);
    }

    // Send notification
    await notifySlack(article, result);

    // Return success
    return res.status(200).json({
      success: true,
      message: config.createPR ? 'Pull request created' : 'Content committed',
      file: filePath,
      url: result.url,
      unito_sync: 'Unito will sync this to Asana automatically'
    });

  } catch (error) {
    console.error('Webhook processing error:', error);
    
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}
