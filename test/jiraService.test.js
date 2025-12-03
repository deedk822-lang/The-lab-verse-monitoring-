import JiraService from '../src/services/jiraService.js';
import AlertService from '../src/services/alertService.js';
import mailchimpService from '../src/services/mailchimpService.js';

// Mock the services
jest.mock('../src/services/alertService.js');
jest.mock('../src/services/mailchimpService.js');

describe('JiraService', () => {
  let jiraService;

  beforeEach(() => {
    // Clear all instances and calls to constructor and all methods:
    AlertService.mockClear();
    mailchimpService.createAndSendCampaign.mockClear();
    jiraService = new JiraService();
  });

  it('should handle issue_created event', async () => {
    const payload = {
      webhookEvent: 'jira:issue_created',
      issue: {
        key: 'TEST-1',
        fields: {
          summary: 'This is a test issue',
          creator: {
            displayName: 'John Doe',
          },
        },
      },
    };

    await jiraService.handleWebhook(payload);

    expect(AlertService).toHaveBeenCalledTimes(1);
    const alertServiceInstance = AlertService.mock.instances[0];
    expect(alertServiceInstance.sendSlackAlert).toHaveBeenCalledWith(
      'New Jira Issue',
      'New issue created by John Doe: [TEST-1] This is a test issue',
      'info'
    );
    expect(mailchimpService.createAndSendCampaign).not.toHaveBeenCalled();
  });

  it('should handle issue_updated event with status change to Done', async () => {
    const payload = {
      webhookEvent: 'jira:issue_updated',
      user: {
        displayName: 'Jane Doe',
      },
      issue: {
        key: 'TEST-2',
        fields: {
          summary: 'Another test issue',
        },
      },
      changelog: {
        items: [
          {
            field: 'status',
            fromString: 'In Progress',
            toString: 'Done',
          },
        ],
      },
    };

    await jiraService.handleWebhook(payload);

    const alertServiceInstance = AlertService.mock.instances[0];
    expect(alertServiceInstance.sendSlackAlert).toHaveBeenCalledTimes(2);
    expect(alertServiceInstance.sendSlackAlert).toHaveBeenCalledWith(
        'Jira Issue Updated',
        "Issue [TEST-2] Another test issue was updated by Jane Doe. Changes: 'status' from 'In Progress' to 'Done'",
        'info'
    );

    expect(mailchimpService.createAndSendCampaign).toHaveBeenCalledTimes(1);
    expect(mailchimpService.createAndSendCampaign).toHaveBeenCalledWith({
      subject: 'Issue Completed: Another test issue',
      content: '<h1>Issue Completed: Another test issue</h1><p>The issue TEST-2 has been marked as done.</p>',
    });
  });

  it('should not trigger mailchimp for non-done status changes', async () => {
    const payload = {
        webhookEvent: 'jira:issue_updated',
        user: {
          displayName: 'Jane Doe',
        },
        issue: {
          key: 'TEST-3',
          fields: {
            summary: 'A third test issue',
          },
        },
        changelog: {
          items: [
            {
              field: 'status',
              fromString: 'To Do',
              toString: 'In Progress',
            },
          ],
        },
      };

      await jiraService.handleWebhook(payload);

      const alertServiceInstance = AlertService.mock.instances[0];
      expect(alertServiceInstance.sendSlackAlert).toHaveBeenCalledTimes(1);
      expect(mailchimpService.createAndSendCampaign).not.toHaveBeenCalled();
    });
});
