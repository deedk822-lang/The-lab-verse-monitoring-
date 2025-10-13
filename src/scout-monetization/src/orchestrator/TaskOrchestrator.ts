import { Task } from "../types";

export interface ProcessResult {
  extractedOpps?: any[];
  rankedOpps?: any[];
  result?: any;
}

export class EnhancedTaskOrchestrator {
  private running = false;

  async start(): Promise<void> {
    this.running = true;
  }

  async healthCheck(): Promise<number> {
    return this.running ? 1 : 0;
  }

  async processBatch(tasks: Task[]): Promise<ProcessResult[]> {
    return tasks.map(() => ({ extractedOpps: [] }));
  }

  async processTask(task: Task): Promise<ProcessResult> {
    if (task.id.startsWith("rank-opps-")) {
      const opps = (task.meta as any)?.opps ?? [];
      return { rankedOpps: opps };
    }
    return { result: {} };
  }
}
