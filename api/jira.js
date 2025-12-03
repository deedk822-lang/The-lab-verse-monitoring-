// api/jira.js - Vercel Serverless Function for Jira Webhooks

import jiraService from '../src/services/jiraService.js';
import { logger } from '../src/utils/logger.js';

export default async function handler(req, res) {
  // Only accept POST requests
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    const payload = req.body;
    logger.info('Received Jira webhook payload.');

    // Asynchronously process the webhook to avoid timeouts
    jiraService.handleWebhook(payload).catch(error => {
      logger.error('Error processing Jira webhook in the background:', error);
    });

    // Respond immediately to Jira to acknowledge receipt
    return res.status(202).json({ message: 'Webhook received and is being processed.' });

  } catch (error) {
    logger.error('Error in Jira webhook handler:', error);
    return res.status(500).json({ success: false, error: 'Internal Server Error' });
  }
}
