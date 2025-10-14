import { logger } from '../lib/logger';
import { argillaClient } from '../integrations/ArgillaClient';
import { argillaMonetization } from '../monetization/ArgillaMonetization';

// Placeholder for BattleResult interface
interface BattleResult {
    battleId: string;
    challengeId: string;
    winner: string | null;
    competitors: string[];
    results: any;
    prompt: string;
    id: string;
    severity: string;
    category: string;
}

export class ColiseumManager {
  private battleHistory: Map<string, BattleResult[]> = new Map();
  private activeChallenges: Map<string, any> = new Map();

  constructor() {
    logger.info('Coliseum Manager initialized');
  }

  // Placeholder for creating a sponsored battle
  public async createSponsoredBattle(title: string, prize: number, sponsor: string) {
    logger.info('Creating sponsored battle', { title, prize, sponsor });
    // In a real implementation, this would interact with a battle management system.
    return { id: `battle-${Date.now()}` };
  }

  async handleBattleCompleted(battleResult: BattleResult): Promise<void> {
    // Store the battle result
    const challengeId = battleResult.challengeId;
    const history = this.battleHistory.get(challengeId) || [];
    history.push(battleResult);
    this.battleHistory.set(challengeId, history);

    // NEW: Log battle to Argilla for human annotation
    await argillaClient.logBattleResult(battleResult);

    logger.info('Battle completed', {
      battleId: battleResult.battleId,
      challengeId,
      winner: battleResult.winner,
    });
  }

  async createGoldLabelPack(battleIds: string[]): Promise<string> {
    // Create a gold label pack from selected battles
    const packName = `AI vs AI Battles - ${new Date().toISOString().split('T')[0]}`;
    const description = `High-quality AI battle results from ${battleIds.length} competitions`;

    const packId = await argillaMonetization.createGoldLabelPack(packName, description);

    logger.info('Gold label pack created', {
      packId,
      battleCount: battleIds.length
    });

    return packId;
  }

  async processFailedTask(task: any): Promise<void> {
    // NEW: Log failed tasks to Argilla for improvement
    await argillaClient.logFailedTask(task);

    logger.info('Failed task processed for improvement', {
      taskId: task.id,
      category: task.category
    });
  }
}

export const coliseumManager = new ColiseumManager();