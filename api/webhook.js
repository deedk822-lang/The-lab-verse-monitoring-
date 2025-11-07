// api/webhook.js - Vercel Serverless Function
// RankYak → GitHub → Unito (→ Asana) Bridge

import { Octokit } from '@octokit/rest';
import utils from './util.js';

// Initialize GitHub client
let octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN
});

// For testing purposes only, allow replacing the octokit instance.
export function _setOctokitForTest(mockOctokit) {
  if (process.env.NODE_ENV !== 'test') {
    throw new Error('This function is only available in test environment');
  }
  octokit = mockOctokit;
}

// Configuration object with getters to ensure process.env is read at runtime.
const appConfig = {
  get owner() { return process.env.GITHUB_OWNER },
  get repo() { return process.env.GITHUB_REPO },
  get branch() { return process.env.GITHUB_BRANCH || 'main' },
  get webhookSecret() { return process.env.WEBHOOK_SECRET },
  get createPR() { return process.env.CREATE_PR === 'true' },
  get slackWebhook() { return process.env.SLACK_WEBHOOK_URL },
  get contentDir() { return process.env.CONTENT_DIR || '_posts' }
};

/**
 * Convert RankYak HTML to Markdown
 */
function htmlToMarkdown(html) {
  if (!html) return '';
  
  return html
    .replace(/<h1[^>]*>(.*?)<\/h1>/gi, '# $1\n\n')
    .replace(/<h2[^>]*>(.*?)<\/h2>/gi, '## $1\n\n')
    .replace(/<h3[^>]*>(.*?)<\/h3>/gi, '### $1\n\n')
    .replace(/<p[^>]*>(.*?)<\/p>/gi, '$1\n\n')
    .replace(/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/gi, '[$2]($1)')
    .replace(/<strong[^>]*>(.*?)<\/strong>/gi, '**$1**')
    .replace(/<em[^>]*>(.*?)<\/em>/gi, '*$1*')
    .replace(/<li[^>]*>(.*?)<\/li>/gi, '- $1\n')
    .replace(/<ul[^>]*>/gi, '\n')
    .replace(/<\/ul>/gi, '\n')
    .replace(/<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>/gi, '![$2]($1)')
    .replace(/<code[^>]*>(.*?)<\/code>/gi, '`$1`')
    .replace(/<pre[^>]*>(.*?)<\/pre>/gi, '```\n$1\n```\n')
    .replace(/<[^>]*>/g, '')
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
  return `${appConfig.contentDir}/${date}-${slug}.md`;
}

/**
 * Commit file to GitHub
 */
async function commitToGitHub(filePath, content, commitMessage, article) {
  try {
    let sha;
    try {
      const { data } = await octokit.repos.getContent({
        owner: appConfig.owner,
        repo: appConfig.repo,
        path: filePath,
        ref: appConfig.branch
      });
      sha = data.sha;
    } catch (error) {
      sha = null;
    }

    const { data } = await octokit.repos.createOrUpdateFileContents({
      owner: appConfig.owner,
      repo: appConfig.repo,
      path: filePath,
      message: commitMessage,
      content: Buffer.from(content).toString('base64'),
      sha: sha,
      branch: appConfig.branch
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
    const { data: baseRef } = await octokit.git.getRef({
      owner: appConfig.owner,
      repo: appConfig.repo,
      ref: `heads/${appConfig.branch}`
    });

    await octokit.git.createRef({
      owner: appConfig.owner,
      repo: appConfig.repo,
      ref: `refs/heads/${branchName}`,
      sha: baseRef.object.sha
    });

    await commitToGitHub(
      filePath,
      content,
      `Add: ${article.title}`,
      article
    );

    const { data: pr } = await octokit.pulls.create({
      owner: appConfig.owner,
      repo: appConfig.repo,
      title: prTitle,
      body: prBody,
      head: branchName,
      base: appConfig.branch
    });

    await octokit.issues.addLabels({
      owner: appConfig.owner,
      repo: appConfig.repo,
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
  if (!appConfig.slackWebhook) return;

  const message = {
    text: `📝 New content synced from RankYak`,
    blocks: [
      {
        type: 'header',
        text: { type: 'plain_text', text: article.title }
      },
      {
        type: 'section',
        fields: [
          { type: 'mrkdwn', text: `*Author:*\n${article.author?.name || 'Unknown'}` },
          { type: 'mrkdwn', text: `*Status:*\n${result.pr ? 'PR Created' : 'Committed'}` }
        ]
      },
      {
        type: 'section',
        text: { type: 'mrkdwn', text: `*Tags:* ${(article.tags || []).join(', ') || 'None'}` }
      },
      {
        type: 'actions',
        elements: [
          {
            type: 'button',
            text: { type: 'plain_text', text: result.pr ? 'View PR' : 'View Commit' },
            url: result.url
          }
        ]
      }
    ]
  };

  try {
    await fetch(appConfig.slackWebhook, {
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
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const signature = req.headers['x-webhook-signature'];
    const rawBody = JSON.stringify(req.body);
    
    if (!utils.verifySignature(rawBody, signature, appConfig.webhookSecret)) {
      console.error('Invalid webhook signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const { event, article } = req.body;

    if (!event || !event.includes('published')) {
      return res.status(200).json({ 
        message: 'Event ignored',
        event 
      });
    }

    if (!article || !article.title) {
      return res.status(400).json({ error: 'Invalid article data' });
    }

    console.log(`Processing article: ${article.title}`);

    const content = createMarkdownContent(article);
    const filePath = getFilePath(article);

    let result;
    if (appConfig.createPR) {
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

    await notifySlack(article, result);

    return res.status(200).json({
      success: true,
      message: appConfig.createPR ? 'Pull request created' : 'Content committed',
      file: filePath,
      url: result.url,
      unito_sync: 'Unito will sync this to Asana automatically'
    });

  } catch (error) {
    console.error('Webhook processing error:', error);
    
    return res.status(500).json({
      error: 'Processing failed',
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}

// Export config for Vercel
export const config = {
  api: {
    bodyParser: true
  }
};
