export enum TaskType {
  REASONING = "REASONING",
  RESEARCH = "RESEARCH",
  ANALYSIS = "ANALYSIS",
  GENERAL = "GENERAL",
}

export enum Priority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  URGENT = "URGENT",
}

export interface TaskRequirements {
  maxTokens?: number;
  temperature?: number;
}

export interface Task {
  id: string;
  type: TaskType;
  priority: Priority;
  content: string;
  requirements?: TaskRequirements;
  meta?: Record<string, unknown>;
}
