import { MistralService } from './mistralService.js';
import { logger } from '../utils/logger.js';

/**
 * The Auditor Agent
 * Uses Pixtral-12B for visual verification of Tax Collector triggers.
 */
export class AuditorAgent {
  static async handle(payload, context) {
    const mistral = new MistralService();
    const { topic, evidenceUrl, budget } = payload;

    logger.info('🧐 The Auditor is verifying evidence...', { evidenceUrl });

    // 1. If we have visual evidence (news screenshot, invoice, brochure)
    if (evidenceUrl) {
      const verificationPrompt = `
        Analyze this image for the 'Tax Collector' protocol.
        1. Is this a legitimate humanitarian need or educational opportunity?
        2. Extract the specific dollar amount needed if visible.
        3. Verify the organization name.
        Return JSON.
      `;

      try {
        const analysis = await mistral.analyzeImageOrDocument(verificationPrompt, evidenceUrl);
        logger.info('✅ Pixtral Analysis Complete', { analysis });

        // Logic to approve/deny based on Pixtral's output would go here
        // For now, we pass it through
        return {
          status: 'verified',
          analysis: analysis,
          action: 'payment_processing_initiated'
        };

      } catch (error) {
        logger.error('❌ Auditor visual verification failed', error);
        return { status: 'failed_verification', reason: 'unreadable_evidence' };
      }
    }

    // 2. Text-only fallback
    return {
      status: 'pending',
      message: 'No visual evidence provided for Pixtral analysis.'
    };
  }
}
