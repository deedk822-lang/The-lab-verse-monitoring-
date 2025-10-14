import { logger } from '../logger';

type State = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export class CircuitBreaker {
  private state: State = 'CLOSED';
  private failures = 0;
  private lastFailureTime: number | null = null;
  private openTime: number | null = null;

  constructor(
    private readonly failureThreshold: number,
    private readonly resetTimeout: number
  ) {}

  public async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (this.openTime && Date.now() - this.openTime > this.resetTimeout) {
        this.state = 'HALF_OPEN';
        logger.info('Circuit breaker is now HALF_OPEN');
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.reset();
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }

  private recordFailure() {
    this.failures++;
    this.lastFailureTime = Date.now();
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      this.openTime = Date.now();
      logger.warn('Circuit breaker is now OPEN');
    }
  }

  private reset() {
    if (this.state !== 'CLOSED') {
      logger.info('Circuit breaker is now CLOSED');
    }
    this.failures = 0;
    this.lastFailureTime = null;
    this.state = 'CLOSED';
  }
}