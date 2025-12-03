import AlertService from './alertService.js';
import mailchimpService from './mailchimpService.js';
import { logger } from '../utils/logger.js';

class JiraService {
  constructor() {
    this.alertService = new AlertService();
  }

  /**
   * Processes an incoming Jira webhook.
   * @param {object} payload - The Jira webhook payload.
   */
  async handleWebhook(payload) {
    const eventType = payload.webhookEvent;
    logger.info(`Processing Jira event: ${eventType}`);

    switch (eventType) {
      case 'jira:issue_created':
        await this.handleIssueCreated(payload);
        break;
      case 'jira:issue_updated':
        await this.handleIssueUpdated(payload);
        break;
      // Add other event types as needed
      default:
        logger.info(`Unhandled Jira event type: ${eventType}`);
    }
  }

  /**
   * Handles the 'issue_created' event.
   * @param {object} payload - The Jira webhook payload.
   */
  async handleIssueCreated(payload) {
    const { issue } = payload;
    const issueKey = issue.key;
    const summary = issue.fields.summary;
    const creator = issue.fields.creator.displayName;

    const message = `New issue created by ${creator}: [${issueKey}] ${summary}`;
    await this.alertService.sendSlackAlert('New Jira Issue', message, 'info');
  }

  /**
   * Handles the 'issue_updated' event.
   * @param {object} payload - The Jira webhook payload.
   */
  async handleIssueUpdated(payload) {
    const { issue, changelog } = payload;
    const issueKey = issue.key;
    const summary = issue.fields.summary;
    const updater = payload.user.displayName;

    // Check if there is a changelog and items
    if (changelog && changelog.items && changelog.items.length > 0) {
        const changes = changelog.items.map(item =>
            `'${item.field}' from '${item.fromString}' to '${item.toString}'`
        ).join(', ');

        const message = `Issue [${issueKey}] ${summary} was updated by ${updater}. Changes: ${changes}`;
        await this.alertService.sendSlackAlert('Jira Issue Updated', message, 'info');

        // Example of a more critical alert and Mailchimp campaign
        const statusChange = changelog.items.find(item => item.field === 'status');
        if (statusChange && statusChange.toString.toLowerCase() === 'done') {
            const criticalMessage = `Issue [${issueKey}] ${summary} has been completed!`;
            await this.alertService.sendSlackAlert('Jira Issue Completed', criticalMessage, 'critical');

            await mailchimpService.createAndSendCampaign({
                subject: `Issue Completed: ${summary}`,
                content: `<h1>Issue Completed: ${summary}</h1><p>The issue ${issueKey} has been marked as done.</p>`,
            });
        }
    } else {
        logger.info(`Issue [${issueKey}] updated by ${updater}, but no changes were found in the changelog.`);
    }
  }
}

export default new JiraService();
