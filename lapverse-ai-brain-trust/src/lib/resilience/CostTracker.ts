import { logger } from '../logger';

export class CostTracker {
  private totalCost = 0;

  constructor(private readonly budget: number) {}

  public recordCost(cost: number) {
    this.totalCost += cost;
    logger.info(`Cost recorded: ${cost}. Total cost: ${this.totalCost}`);
    if (this.totalCost > this.budget) {
      logger.warn(`Budget exceeded. Budget: ${this.budget}, Total cost: ${this.totalCost}`);
    }
  }

  public hasExceededBudget(): boolean {
    return this.totalCost > this.budget;
  }
}