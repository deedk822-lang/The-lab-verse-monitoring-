import axios from 'axios';
import { logger } from '../../lib/logger';
import { Config } from '../../lib/config/Config';

const TONGYI_API_URL = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation';

class TongyiDeepResearch {
  private readonly apiKey: string;

  constructor() {
    if (!Config.TONGYI_API_KEY) {
      throw new Error('TONGYI_API_KEY is not set');
    }
    this.apiKey = Config.TONGYI_API_KEY;
  }

  async analyzeAnomaly(
    { query, researchType }: { query: string; researchType: string },
    opts: any
  ): Promise<any> {
    logger.info({ query, researchType, opts }, 'Performing deep research with Tongyi');

    const response = await axios.post(
      TONGYI_API_URL,
      {
        model: 'qwen-long',
        input: {
          prompt: `Analyze the following anomaly with a ${researchType} approach: ${query}`,
        },
        parameters: {
          result_format: 'text',
        },
      },
      {
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
          ...opts.headers,
        },
      }
    );

    if (response.data.output && response.data.output.text) {
      return response.data.output.text;
    } else {
      logger.error({ response: response.data }, 'Tongyi API error');
      throw new Error('Failed to get response from Tongyi');
    }
  }
}

export const tongyiDeepResearch = new TongyiDeepResearch();