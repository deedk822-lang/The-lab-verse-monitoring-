import axios from 'axios';
import { logger } from '../lib/logger';
import { metrics } from '../lib/metrics';
import { config } from '../lib/config/Config';

export interface FeedbackRecord {
  prompt: string;
  response_a: string;
  response_b: string;
  winner: string;
  metadata: {
    battleId: string;
    severity: string;
    category: string;
    timestamp: number;
  };
}

export interface AnnotationResult {
  overall: number; // 1-5 rating
  issue: string; // hallucination, toxicity, bias, none
  reviewer_id: string;
  confidence: number;
}

export class ArgillaClient {
  private baseURL: string;
  private apiKey: string;
  private workspace: string;
  private quotaUsed: number = 0;
  private quotaLimit: number;

  constructor() {
    this.baseURL = config.get().ARGILLA_BASE_URL;
    this.apiKey = config.get().ARGILLA_API_KEY;
    this.workspace = config.get().ARGILLA_WORKSPACE;
    this.quotaLimit = config.get().ARGILLA_QUOTA_ROWS;
  }

  async createFeedbackDataset(): Promise<string> {
    try {
      const response = await axios.post(
        `${this.baseURL}/api/datasets`,
        {
          name: 'lapverse-ai-battles',
          workspace: this.workspace,
          settings: {
            fields: [
              { name: 'prompt', title: 'Prompt', type: 'text' },
              { name: 'response_a', title: 'Response A', type: 'text' },
              { name: 'response_b', title: 'Response B', type: 'text' },
              { name: 'winner', title: 'Winner', type: 'text' }
            ],
            questions: [
              {
                name: 'overall',
                title: 'Overall Quality',
                description: 'Rate the overall quality of the responses',
                type: 'rating',
                values: [1, 2, 3, 4, 5]
              },
              {
                name: 'issue',
                title: 'Identified Issues',
                description: 'Select any issues found in the responses',
                type: 'label_selection',
                options: ['hallucination', 'toxicity', 'bias', 'none']
              }
            ],
            guidelines: 'Rate the AI responses based on accuracy, helpfulness, and safety.'
          }
        },
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const datasetId = response.data.id;

      logger.info('Feedback dataset created', { datasetId });
      return datasetId;
    } catch (error) {
      logger.error('Failed to create feedback dataset', { error });
      throw error;
    }
  }

  async logBattleResult(battle: any): Promise<void> {
    if (this.quotaUsed >= this.quotaLimit) {
      logger.warn('Argilla quota exceeded', { used: this.quotaUsed, limit: this.quotaLimit });
      return;
    }

    try {
      const record: FeedbackRecord = {
        prompt: battle.prompt,
        response_a: battle.results[battle.competitors[0]].content,
        response_b: battle.results[battle.competitors[1]].content,
        winner: battle.winner,
        metadata: {
          battleId: battle.id,
          severity: battle.severity,
          category: battle.category,
          timestamp: Date.now()
        }
      };

      // Anonymize sensitive data
      const anonymizedRecord = this.anonymizeRecord(record);

      const response = await axios.post(
        `${this.baseURL}/api/datasets/lapverse-ai-battles/records`,
        anonymizedRecord,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      this.quotaUsed++;

      // Track metrics
      metrics.counter('argilla_records_logged', 'Number of records logged to Argilla', ['category', 'severity']).inc({
        category: battle.category,
        severity: battle.severity
      });

      logger.info('Battle result logged to Argilla', {
        battleId: battle.id,
        recordId: response.data.id
      });
    } catch (error) {
      logger.error('Failed to log battle result', { error });
      throw error;
    }
  }

  async logFailedTask(task: any): Promise<void> {
    if (this.quotaUsed >= this.quotaLimit) {
      logger.warn('Argilla quota exceeded', { used: this.quotaUsed, limit: this.quotaLimit });
      return;
    }

    try {
      const record = {
        prompt: task.prompt,
        response_a: task.result || 'No response',
        response_b: 'Expected response not provided',
        winner: 'none',
        metadata: {
          taskId: task.id,
          category: task.category,
          error: task.error,
          timestamp: Date.now()
        }
      };

      const anonymizedRecord = this.anonymizeRecord(record);

      const response = await axios.post(
        `${this.baseURL}/api/datasets/lapverse-failed-tasks/records`,
        anonymizedRecord,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      this.quotaUsed++;

      logger.info('Failed task logged to Argilla', {
        taskId: task.id,
        recordId: response.data.id
      });
    } catch (error) {
      logger.error('Failed to log failed task', { error });
      throw error;
    }
  }

  private anonymizeRecord(record: any): any {
    // Remove PII and sensitive information
    const anonymized = { ...record };

    // Remove emails, IPs, and other PII
    anonymized.prompt = record.prompt.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]');
    anonymized.prompt = anonymized.prompt.replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[IP]');

    return anonymized;
  }

  async getAnnotations(datasetId: string): Promise<AnnotationResult[]> {
    try {
      const response = await axios.get(
        `${this.baseURL}/api/datasets/${datasetId}/records`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        }
      );

      return response.data.map((record: any) => ({
        overall: record.responses.overall?.value || 0,
        issue: record.responses.issue?.value || 'none',
        reviewer_id: record.responses.overall?.user_id || 'anonymous',
        confidence: record.responses.overall?.confidence || 0
      }));
    } catch (error) {
      logger.error('Failed to get annotations', { error });
      throw error;
    }
  }

  async exportDataset(datasetId: string, format: 'csv' | 'json' = 'csv'): Promise<string> {
    try {
      const response = await axios.get(
        `${this.baseURL}/api/datasets/${datasetId}/export?format=${format}`,
        {
          headers: {
            'Authorization': `Bearer ${this.apiKey}`
          }
        }
      );

      return response.data.url;
    } catch (error) {
      logger.error('Failed to export dataset', { error });
      throw error;
    }
  }

  getQuotaStatus(): { used: number; limit: number; remaining: number } {
    return {
      used: this.quotaUsed,
      limit: this.quotaLimit,
      remaining: this.quotaLimit - this.quotaUsed
    };
  }
}

export const argillaClient = new ArgillaClient();