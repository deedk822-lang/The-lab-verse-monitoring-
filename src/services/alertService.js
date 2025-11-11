import { Queue, Worker } from 'bullmq';
import axios from 'axios';
import Redis from 'ioredis';
import pino from 'pino';

const logger = pino({ level: 'info' });
const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379', {
  maxRetriesPerRequest: null
});
const slackQueue = new Queue('slack-alerts', { connection: redis });

new Worker('slack-alerts', async job => {
  const { title, message, severity } = job.data;
  const payload = {
    username: 'Lab-Verse',
    icon_emoji: ':robot_face:',
    attachments: [{ color: severity === 'critical' ? 'danger' : 'warning', title, text: message }]
  };
  await axios.post(process.env.SLACK_WEBHOOK_URL, payload);
}, { connection: redis });

class AlertService {
  async sendSlackAlert(title, message, severity = 'info') {
    await slackQueue.add('slack-alert', { title, message, severity });
    return { queued: true };
  }
}
export default AlertService;