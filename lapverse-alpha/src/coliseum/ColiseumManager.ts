import { EventEmitter } from 'events';
import { logger } from '../lib/logger/Logger';
import { metrics } from '../lib/metrics/Metrics';
import { argillaClient } from '../integrations/ArgillaClient';

export interface Battle {
  id: string;
  competitors: string[];
  prompt: string;
  results: Map<string, any>;
  winner?: string;
  status: 'pending' | 'running' | 'completed';
  createdAt: Date;
  completedAt?: Date;
  severity: string;
  category: string;
}

export class ColiseumManager extends EventEmitter {
  private battles: Map<string, Battle> = new Map();
  private activeBattles: Set<string> = new Set();

  constructor() {
    super();
  }

  async createBattle(competitors: string[], prompt: string, category: string, severity: string): Promise<string> {
    const battleId = `battle-${Date.now()}-${Math.random().toString(36).slice(2, 11)}`;

    const battle: Battle = {
      id: battleId,
      competitors,
      prompt,
      results: new Map(),
      status: 'pending',
      createdAt: new Date(),
      category,
      severity,
    };

    this.battles.set(battleId, battle);
    this.activeBattles.add(battleId);

    logger.info('Battle created', { battleId, competitors: competitors.length });
    return battleId;
  }

  async startBattle(battleId: string): Promise<void> {
    const battle = this.battles.get(battleId);
    if (!battle) {
      throw new Error(`Battle ${battleId} not found`);
    }

    battle.status = 'running';

    // Simulate battle execution
    for (const competitor of battle.competitors) {
      // In a real implementation, this would call the actual AI models
      const result = await this.simulateCompetitorResult(competitor, battle.prompt);
      battle.results.set(competitor, result);
    }

    // Determine winner
    battle.winner = this.determineWinner(battle);
    battle.status = 'completed';
    battle.completedAt = new Date();

    // Log to Argilla
    await argillaClient.logBattleResult(battle);

    // Update metrics
    metrics.coliseumBattlesTotal.inc();
    if (battle.completedAt && battle.createdAt) {
      const duration = (battle.completedAt.getTime() - battle.createdAt.getTime()) / 1000;
      metrics.coliseumBattleDuration.observe(duration);
    }

    this.activeBattles.delete(battleId);
    this.emit('battleCompleted', battle);

    logger.info('Battle completed', { battleId, winner: battle.winner });
  }

  private async simulateCompetitorResult(competitor: string, prompt: string): Promise<any> {
    // Simulate AI model response
    return {
      competitor,
      prompt,
      content: `Response from ${competitor} to: ${prompt}`,
      confidence: Math.random() * 0.5 + 0.5,
      timestamp: new Date(),
    };
  }

  private determineWinner(battle: Battle): string {
    let bestCompetitor = '';
    let bestScore = 0;

    for (const [competitor, result] of battle.results.entries()) {
      if (result.confidence > bestScore) {
        bestScore = result.confidence;
        bestCompetitor = competitor;
      }
    }

    return bestCompetitor;
  }

  getBattle(battleId: string): Battle | undefined {
    return this.battles.get(battleId);
  }

  getAllBattles(): Battle[] {
    return Array.from(this.battles.values());
  }

  getActiveBattles(): Battle[] {
    return Array.from(this.activeBattles).map(id => this.battles.get(id)!);
  }
}

export const coliseumManager = new ColiseumManager();