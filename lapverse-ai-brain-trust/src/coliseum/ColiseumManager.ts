import { logger } from '../lib/logger';

// A simple placeholder for a competitor
interface Competitor {
  type: string;
  name: string;
}

// A simple placeholder for a battle result
interface BattleResult {
  winner: string;
  results: Record<string, any>;
}

export class ColiseumManager {
  private static instance: ColiseumManager;
  private challenges: Map<string, any> = new Map();
  private competitors: Map<string, Competitor> = new Map();

  constructor() {
    if (ColiseumManager.instance) {
      return ColiseumManager.instance;
    }
    ColiseumManager.instance = this;
    // Add some default competitors
    this.competitors.set('gemini', { type: 'gemini', name: 'Gemini' });
    this.competitors.set('tongyi', { type: 'tongyi', name: 'Tongyi' });
  }

  async createChallenge(
    name: string,
    prompt: string,
    metadata: any,
    priority: 'low' | 'medium' | 'high',
    type: string
  ) {
    const id = Math.random().toString(36).substring(7);
    const challenge = { id, name, prompt, metadata, priority, type, status: 'CREATED', history: [] };
    this.challenges.set(id, challenge);
    logger.info({ challenge }, 'Challenge created');
    return id;
  }

  async startBattle(challengeId: string) {
    const challenge = this.challenges.get(challengeId);
    if (!challenge) {
      throw new Error(`Challenge ${challengeId} not found`);
    }
    challenge.status = 'IN_PROGRESS';
    logger.info({ challengeId }, 'Battle started');

    // Simulate the battle
    const results: Record<string, any> = {};
    for (const [id, competitor] of this.competitors.entries()) {
      results[id] = `Result from ${competitor.name} for prompt: ${challenge.prompt}`;
    }

    // Simulate a winner
    const winner = Array.from(this.competitors.keys())[Math.floor(Math.random() * this.competitors.size)];

    const battleResult: BattleResult = { winner, results };
    challenge.history.push(battleResult);
    challenge.status = 'COMPLETED';
    logger.info({ challengeId, result: battleResult }, 'Battle completed');
  }

  getBattleHistory(challengeId: string) {
    const challenge = this.challenges.get(challengeId);
    if (!challenge) {
      throw new Error(`Challenge ${challengeId} not found`);
    }
    return challenge.history;
  }

  getCompetitor(competitorId: string) {
    const competitor = this.competitors.get(competitorId);
    if (!competitor) {
      throw new Error(`Competitor ${competitorId} not found`);
    }
    return competitor;
  }
}

export const coliseumManager = new ColiseumManager();