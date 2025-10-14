import { logger } from '../logger';

export class RetryPolicy {
  constructor(
    private readonly maxRetries: number,
    private readonly delayMs: number
  ) {}

  public async execute<T>(fn: () => Promise<T>): Promise<T> {
    for (let i = 0; i < this.maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === this.maxRetries - 1) {
          throw error;
        }
        logger.warn(`Attempt ${i + 1} failed. Retrying in ${this.delayMs}ms...`);
        await new Promise((resolve) => setTimeout(resolve, this.delayMs));
      }
    }
    throw new Error('Max retries reached');
  }
}