import { EventEmitter } from 'events';
import { logger } from '../lib/logger/Logger';
import { metrics } from '../lib/metrics/Metrics';
import { localAIOSSProvider } from './LocalAIOSSProvider';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'busy' | 'offline';
  capabilities: string[];
  performance: {
    tasksCompleted: number;
    successRate: number;
    averageResponseTime: number;
  };
}

export interface Task {
  id: string;
  type: string;
  prompt: string;
  assignedAgent?: string;
  status: 'pending' | 'assigned' | 'completed' | 'failed';
  result?: any;
  error?: string;
  createdAt: Date;
  completedAt?: Date;
}

export class AgentOrchestrator extends EventEmitter {
  private agents: Map<string, Agent> = new Map();
  private tasks: Map<string, Task> = new Map();
  private taskQueue: Task[] = [];

  constructor() {
    super();
    this.initializeAgents();
  }

  private initializeAgents(): void {
    // Initialize default agents
    const defaultAgents: Agent[] = [
      {
        id: 'gpt-oss-20b',
        name: 'GPT-OSS-20B',
        type: 'research',
        status: 'idle',
        capabilities: ['research', 'analysis', 'writing'],
        performance: {
          tasksCompleted: 0,
          successRate: 0,
          averageResponseTime: 0,
        }
      }
    ];

    defaultAgents.forEach(agent => {
      this.agents.set(agent.id, agent);
    });

    logger.info('Agent orchestrator initialized', { agentCount: this.agents.size });
  }

  async createTask(type: string, prompt: string): Promise<string> {
    const task: Task = {
      id: `task-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      type,
      prompt,
      status: 'pending',
      createdAt: new Date(),
    };

    this.tasks.set(task.id, task);
    this.taskQueue.push(task);

    // Process queue
    this.processQueue();

    metrics.a2aTasksCreated.inc({ category: type });

    logger.info('Task created', { taskId: task.id, type });
    return task.id;
  }

  private async processQueue(): Promise<void> {
    if (this.taskQueue.length === 0) return;

    const task = this.taskQueue.shift()!;
    const agent = this.findAvailableAgent(task);

    if (agent) {
      await this.assignTask(task, agent);
    } else {
      // No available agents, put back in queue
      this.taskQueue.push(task);
    }
  }

  private findAvailableAgent(task: Task): Agent | null {
    for (const agent of this.agents.values()) {
      if (agent.status === 'idle' && agent.capabilities.includes(task.type)) {
        return agent;
      }
    }
    return null;
  }

  private async assignTask(task: Task, agent: Agent): Promise<void> {
    task.assignedAgent = agent.id;
    task.status = 'assigned';
    agent.status = 'busy';

    logger.info('Task assigned', { taskId: task.id, agentId: agent.id });

    try {
      const result = await this.executeTask(task, agent);
      task.result = result;
      task.status = 'completed';
      task.completedAt = new Date();

      // Update agent performance
      agent.performance.tasksCompleted++;
      agent.status = 'idle';

      this.emit('taskCompleted', { task, agent, result });

    } catch (error) {
      task.error = error instanceof Error ? error.message : 'Unknown error';
      task.status = 'failed';
      agent.status = 'idle';

      logger.error('Task failed', { taskId: task.id, error: task.error });
    }
  }

  private async executeTask(task: Task, agent: Agent): Promise<any> {
    const startTime = Date.now();

    try {
      const result = await localAIOSSProvider.callModel(task.prompt);

      const duration = Date.now() - startTime;

      // Update agent performance metrics
      agent.performance.averageResponseTime =
        (agent.performance.averageResponseTime + duration) / 2;
      agent.performance.successRate =
        (agent.performance.successRate * agent.performance.tasksCompleted + 1) /
        (agent.performance.tasksCompleted + 1);

      return result;
    } catch (error) {
      throw error;
    }
  }

  getTask(taskId: string): Task | undefined {
    return this.tasks.get(taskId);
  }

  getAgent(agentId: string): Agent | undefined {
    return this.agents.get(agentId);
  }

  getAllAgents(): Agent[] {
    return Array.from(this.agents.values());
  }

  getAllTasks(): Task[] {
    return Array.from(this.tasks.values());
  }
}

export const agentOrchestrator = new AgentOrchestrator();