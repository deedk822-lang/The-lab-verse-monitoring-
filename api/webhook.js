import { Octokit } from '@octokit/rest';
import TurndownService from 'turndown';
import fetch from 'node-fetch';
import FormData from 'form-data';
import crypto from 'crypto';

const turndown = new TurndownService({ headingStyle: 'atx', codeBlockStyle: 'fenced' });

/* ----------  ENV VARS  ---------- */
const GITHUB_TOKEN        = process.env.GITHUB_TOKEN;
const GITHUB_OWNER        = process.env.GITHUB_OWNER || new URL(process.env.GITHUB_REPO).pathname.split('/')[1];
const GITHUB_REPO         = process.env.GITHUB_REPO.split('/')[1];
const GITHUB_BRANCH       = process.env.GITHUB_BRANCH || 'main';

const WP_SITE             = process.env.WP_SITE_ID;
const WP_USER             = process.env.WP_USERNAME;
const WP_PASS             = process.env.WP_APP_PASSWORD;
const WP_STAT             = process.env.WP_PUBLISH_STATUS || 'draft';

const BRIA_KEY            = process.env.BRIA_API_KEY;
const BRIA_ENGINE         = process.env.BRIA_BRAND_ENGINE;

const AYR_KEY             = process.env.AYRSHARE_API_KEY;
const SP_KEY              = process.env.SOCIALPILOT_API_KEY;
const MC_KEY              = process.env.MAILCHIMP_API_KEY;
const MC_SERVER           = process.env.MAILCHIMP_SERVER_PREFIX || 'us1';
const MC_LIST             = process.env.MAILCHIMP_LIST_ID;

const SLACK_WEBHOOK       = process.env.SLACK_WEBHOOK_URL;
const TEAMS_WEBHOOK       = process.env.TEAMS_WEBHOOK_URL;
const DISCORD_WEBHOOK     = process.env.DISCORD_WEBHOOK_URL;

const BRAVE_WALLET_ID     = process.env.BRAVE_WALLET_ID;
const BRAVE_TOKEN         = process.env.BRAVE_ADS_TOKEN;

const PLAID_CLIENT_ID     = process.env.PLAID_CLIENT_ID;
const PLAID_SECRET        = process.env.PLAID_SECRET;
const PLAID_BUDGET_ID     = process.env.PLAID_BUDGET_CATEGORY || 'marketing';

const WEBHOOK_SECRET      = process.env.RANKYAK_WEBHOOK_SECRET;

const WP_AUTH = 'Basic ' + Buffer.from(`${WP_USER}:${WP_PASS}`).toString('base64');

/* ----------  HELPERS  ---------- */
async function briaImage(prompt, width = 1024, height = 1024, format = 'jpg') {
  const body = { prompt, width, height, output_format: format, num_results: 1 };
  if (BRIA_ENGINE) body.engine_id = BRIA_ENGINE;
  const r = await fetch('https://platform.bria.ai/v1/images/generate', {
    method: 'POST',
    headers: { api_token: BRIA_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  }).then(r => r.json());
  if (r.error) throw new Error(`Bria: ${r.error.message}`);
  const buf = await fetch(r.result[0].url).then(r => r.buffer());
  return { buffer: buf, generationId: r.result[0].generation_id, attribution: r.result[0].attribution_token, url: r.result[0].url };
}

async function uploadMedia(buffer, filename, mime = 'image/jpeg') {
  const fd = new FormData();
  fd.append('media[]', buffer, { filename, contentType: mime });
  const r = await fetch(`https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/media/new`, {
    method: 'POST', headers: { Authorization: WP_AUTH, ...fd.getHeaders() }, body: fd
  }).then(r => r.json());
  if (r.error) throw new Error(`WP media: ${r.message}`);
  return { id: r.media[0].ID, url: r.media[0].URL };
}

async function upsertPost({ title, slug, html, excerpt, tags, heroId, categories = [] }) {
  const existing = await fetch(`https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/posts/slug:${slug}`, {
    headers: { Authorization: WP_AUTH }
  }).then(r => r.ok ? r.json() : null);
  
  const payload = {
    title, slug,
    content: `<!-- wp:image {"id":${heroId}} --><figure class="wp-block-image"><img class="wp-image-${heroId}"/></figure><!-- /wp:image --><!-- wp:html -->${html}<!-- /wp:html -->`,
    excerpt: excerpt || html.replace(/<[^>]*>/g, '').substring(0, 160),
    tags: tags.join(','),
    categories: categories.join(','),
    status: WP_STAT
  };
  
  const url = existing 
    ? `https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/posts/${existing.ID}`
    : `https://public-api.wordpress.com/rest/v1.1/sites/${WP_SITE}/posts/new`;
  const method = existing ? 'POST' : 'POST';
  
  const r = await fetch(url, {
    method,
    headers: { Authorization: WP_AUTH, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(r => r.json());
  
  if (r.error) throw new Error(`WP post: ${r.message}`);
  return { id: r.ID, url: r.URL, status: r.status };
}

async function notifySlack(message) {
  if (!SLACK_WEBHOOK) return;
  await fetch(SLACK_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: message })
  });
}

async function notifyTeams(message) {
  if (!TEAMS_WEBHOOK) return;
  await fetch(TEAMS_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: message })
  });
}

async function notifyDiscord(message) {
  if (!DISCORD_WEBHOOK) return;
  await fetch(DISCORD_WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: message })
  });
}

async function postToSocialMedia(postUrl, title) {
  if (!AYR_KEY) return;
  await fetch('https://app.ayrshare.com/api/post', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${AYR_KEY}` },
    body: JSON.stringify({
      post: `${title}\n\nRead more: ${postUrl}`,
      platforms: ['twitter', 'facebook', 'linkedin']
    })
  });
}

async function addToMailchimp(email, firstName, lastName) {
  if (!MC_KEY || !MC_LIST) return;
  await fetch(`https://${MC_SERVER}.api.mailchimp.com/3.0/lists/${MC_LIST}/members`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `apikey ${MC_KEY}` },
    body: JSON.stringify({
      email_address: email,
      status: 'subscribed',
      merge_fields: { FNAME: firstName, LNAME: lastName }
    })
  });
}

async function trackBraveMetrics(conversionValue) {
  if (!BRAVE_WALLET_ID || !BRAVE_TOKEN) return;
  await fetch(`https://api.brave.com/v1/wallets/${BRAVE_WALLET_ID}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${BRAVE_TOKEN}` },
    body: JSON.stringify({
      event_type: 'conversion',
      conversion_value: conversionValue,
      timestamp: new Date().toISOString()
    })
  });
}

async function updatePlaidBudget(amount) {
  if (!PLAID_CLIENT_ID || !PLAID_SECRET) return;
  // This is a placeholder for Plaid budget tracking
  // Implementation would depend on your specific Plaid setup
  console.log(`Plaid budget update: ${amount} for category ${PLAID_BUDGET_ID}`);
}

/* ----------  MAIN HANDLER  ---------- */
export default async function handler(req, res) {
  try {
    // Verify webhook signature
    const signature = req.headers['x-hub-signature-256'];
    if (!signature) {
      return res.status(401).json({ error: 'No signature provided' });
    }
    
    const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET);
    const digest = 'sha256=' + hmac.update(JSON.stringify(req.body)).digest('hex');
    
    if (signature !== digest) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // Process the webhook payload
    const { action, repository, issue, pull_request, release } = req.body;
    
    if (!repository || repository.full_name !== `${GITHUB_OWNER}/${GITHUB_REPO}`) {
      return res.status(200).json({ message: 'Ignoring event for different repository' });
    }
    
    // Initialize Octokit
    const octokit = new Octokit({ auth: GITHUB_TOKEN });
    
    // Handle different event types
    if (action === 'published' && release) {
      // Handle new release
      const releaseData = await octokit.repos.getRelease({
        owner: GITHUB_OWNER,
        repo: GITHUB_REPO,
        release_id: release.id
      });
      
      const releaseBody = releaseData.data.body || '';
      const releaseTitle = releaseData.data.name || `Release ${releaseData.data.tag_name}`;
      const releaseTag = releaseData.data.tag_name;
      
      // Generate image for the release
      const imagePrompt = `Software release announcement for ${releaseTitle} with version ${releaseTag}`;
      const image = await briaImage(imagePrompt);
      const uploadedImage = await uploadMedia(image.buffer, `release-${releaseTag}.jpg`, 'image/jpeg`);
      
      // Convert release notes to HTML
      const htmlContent = turndown.turndown(releaseBody);
      
      // Create or update WordPress post
      const post = await upsertPost({
        title: releaseTitle,
        slug: `release-${releaseTag}`,
        html: htmlContent,
        tags: ['release', 'update'],
        heroId: uploadedImage.id,
        categories: ['Releases']
      });
      
      // Send notifications
      const message = `New release published: ${releaseTitle}\n\n${post.url}`;
      await Promise.all([
        notifySlack(message),
        notifyTeams(message),
        notifyDiscord(message),
        postToSocialMedia(post.url, releaseTitle)
      ]);
      
      return res.status(200).json({ success: true, post: post.url });
    }
    
    if (issue && (action === 'opened' || action === 'closed')) {
      // Handle issue events
      const issueData = await octokit.issues.get({
        owner: GITHUB_OWNER,
        repo: GITHUB_REPO,
        issue_number: issue.number
      });
      
      const issueTitle = issueData.data.title;
      const issueBody = issueData.data.body || '';
      const issueState = issueData.data.state;
      const issueNumber = issueData.data.number;
      
      // Generate image for the issue
      const imagePrompt = `GitHub issue ${issueState}: ${issueTitle}`;
      const image = await briaImage(imagePrompt);
      const uploadedImage = await uploadMedia(image.buffer, `issue-${issueNumber}.jpg`, 'image/jpeg`);
      
      // Convert issue to HTML
      const htmlContent = turndown.turndown(issueBody);
      
      // Create or update WordPress post
      const post = await upsertPost({
        title: `${issueState === 'closed' ? 'Resolved' : 'New'} Issue: ${issueTitle}`,
        slug: `issue-${issueNumber}`,
        html: htmlContent,
        tags: ['issue', issueState],
        heroId: uploadedImage.id,
        categories: ['Issues']
      });
      
      // Send notifications
      const message = `Issue ${issueState}: ${issueTitle}\n\n${post.url}`;
      await Promise.all([
        notifySlack(message),
        notifyTeams(message),
        notifyDiscord(message)
      ]);
      
      return res.status(200).json({ success: true, post: post.url });
    }
    
    if (pull_request && (action === 'opened' || action === 'closed')) {
      // Handle pull request events
      const prData = await octokit.pulls.get({
        owner: GITHUB_OWNER,
        repo: GITHUB_REPO,
        pull_number: pull_request.number
      });
      
      const prTitle = prData.data.title;
      const prBody = prData.data.body || '';
      const prState = prData.data.state;
      const prNumber = prData.data.number;
      const prMerged = prData.data.merged;
      
      // Generate image for the pull request
      const imagePrompt = `GitHub pull request ${prState}: ${prTitle}`;
      const image = await briaImage(imagePrompt);
      const uploadedImage = await uploadMedia(image.buffer, `pr-${prNumber}.jpg`, 'image/jpeg`);
      
      // Convert PR body to HTML
      const htmlContent = turndown.turndown(prBody);
      
      // Create or update WordPress post
      const post = await upsertPost({
        title: `${prMerged ? 'Merged' : prState === 'closed' ? 'Closed' : 'New'} Pull Request: ${prTitle}`,
        slug: `pull-request-${prNumber}`,
        html: htmlContent,
        tags: ['pull-request', prState, prMerged ? 'merged' : ''],
        heroId: uploadedImage.id,
        categories: ['Pull Requests']
      });
      
      // Send notifications
      const message = `Pull Request ${prMerged ? 'merged' : prState}: ${prTitle}\n\n${post.url}`;
      await Promise.all([
        notifySlack(message),
        notifyTeams(message),
        notifyDiscord(message)
      ]);
      
      return res.status(200).json({ success: true, post: post.url });
    }
    
    // Default response for unhandled events
    return res.status(200).json({ message: 'Event received but not processed' });
    
  } catch (error) {
    console.error('Webhook error:', error);
    return res.status(500).json({ error: error.message });
  }
}
