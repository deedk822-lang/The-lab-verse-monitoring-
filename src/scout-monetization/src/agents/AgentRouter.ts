import { Task } from "../types";

class MockAgent {
  constructor(private id: string) {}
  async processTask(task: Task): Promise<{ result: any }> {
    return { result: { subject: `Opportunity ${task.id}`, body: "Draft email body" } };
  }
}

export class AgentRouter {
  async selectBestAgent(preferredId: string): Promise<MockAgent> {
    return new MockAgent(preferredId);
  }
}
