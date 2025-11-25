// src/services/mcpHandoffRouter.js
import { mcpRequest } from './mcpService.js';
import { redis } from '../utils/redis.js';
import { logger } from '../utils/logger.js';
import { AyrshareService } from './ayrshareService.js';
import { MailchimpService } from './mailchimpService.js';
import { SlackService, DiscordService, TeamsService } from './a2aService.js';
import { GithubService } from './githubService.js';
import { WpService } from './wpService.js';
import { BriaService } from './briaService.js';

/**
 * MCP Handoff Router - Fallback version for air-gapped or cost-sensitive environments
 * Uses local MCP layer to emulate Mistral handoffs with Redis coordination
 */
export class MCPHandoffRouter {
  /**
   * Main routing function - delegates to appropriate agent
   * @param {Object} payload - RankYak webhook payload
   * @param {Object} options - Additional options
   * @returns {Object} Routing result
   */
  static async route(payload, options = {}) {
    const requestId = options.requestId || `req_${Date.now()}`;
    const { topic, urgency = 'normal', budgetEstimate = 0, intent = 'content' } = payload;
    
    logger.info('🔄 MCP Handoff Router started', { 
      requestId, 
      topic, 
      urgency, 
      budgetEstimate,
      intent 
    });
    
    try {
      // Step 1: Route based on priority
      let nextAgent = this.determineAgent(payload);
      
      // Step 2: Check budget if needed
      if (['content-planner-agent', 'budget-agent'].includes(nextAgent)) {
        const budgetCheck = await this.checkBudget(payload, budgetEstimate);
        if (!budgetCheck.approved) {
          logger.warn('💰 Budget check failed', { 
            requestId, 
            estimated: budgetEstimate,
            remaining: budgetCheck.remaining 
          });
          
          // Send notification and stop processing
          await this.notifyBudgetExceeded(payload, budgetCheck);
          return {
            status: 'rejected',
            reason: 'budget_exceeded',
            requestId,
            budgetCheck
          };
        }
      }
      
      // Step 3: Execute the agent
      logger.info(`🎯 Routing to agent: ${nextAgent}`, { requestId });
      
      const result = await this.executeAgent(nextAgent, payload, { requestId, ...options });
      
      // Step 4: Handle result and potential next handoffs
      return await this.handleResult(result, payload, { requestId, ...options });
      
    } catch (error) {
      logger.error('❌ MCP routing failed', { 
        requestId,
        error: error.message,
        stack: error.stack,
        payload 
      });
      
      // Fallback to emergency notification
      await this.handleRoutingFailure(payload, error, requestId);
      
      throw error;
    }
  }

  /**
   * Determine which agent should handle the request
   * @param {Object} payload - RankYak payload
   * @returns {string} Agent name
   */
  static determineAgent(payload) {
    const { urgency, severity, intent, budgetEstimate } = payload;
    
    // Emergency/critical path
    if (urgency === 'critical' || severity >= 8) {
      return 'emergency-agent';
    }
    
    // Budget check first if over threshold
    if (budgetEstimate > 500) {
      return 'budget-agent';
    }
    
    // Content creation path
    if (intent.includes('content') || intent.includes('create') || intent.includes('publish')) {
      return 'content-planner-agent';
    }
    
    // Monitoring/alert path
    if (intent.includes('monitor') || intent.includes('alert') || intent.includes('status')) {
      return 'monitoring-agent';
    }
    
    // Default to content planner
    return 'content-planner-agent';
  }

  /**
   * Check budget allowance
   * @param {Object} payload - Original payload
   * @param {number} estimatedCost - Estimated cost
   * @returns {Object} Budget check result
   */
  static async checkBudget(payload, estimatedCost) {
    try {
      // Get remaining budget from Redis or config
      const remainingBudget = await redis.get('budget:remaining') || process.env.MONTHLY_BUDGET || 1000;
      
      const approved = parseFloat(remainingBudget) >= estimatedCost;
      
      return {
        approved,
        remaining: parseFloat(remainingBudget),
        estimated: estimatedCost,
        project: 'lab-verse-monitoring'
      };
      
    } catch (error) {
      logger.error('❌ Budget check failed', error);
      // Default to approved if check fails (fail-safe)
      return { approved: true, remaining: Infinity, estimated: estimatedCost };
    }
  }

  /**
   * Execute the specified agent
   * @param {string} agentName - Name of agent to execute
   * @param {Object} payload - Payload to process
   * @param {Object} context - Execution context
   * @returns {Object} Agent result
   */
  static async executeAgent(agentName, payload, context) {
    const agentHandlers = {
      'rankyak-router': async () => this.route(payload, context),
      'content-planner-agent': async () => {
        const ContentPlanner = (await import('./contentPlannerAgent.js')).default;
        return ContentPlanner.handle(payload, context);
      },
      'writer-agent': async () => {
        const WriterAgent = (await import('./writerAgent.js')).default;
        return WriterAgent.handle(payload, context);
      },
      'bria-agent': async () => {
        const BriaAgent = (await import('./briaAgent.js')).default;
        return BriaAgent.handle(payload, context);
      },
      'github-commit-agent': async () => {
        const githubService = new GithubService();
        return githubService.commitContent(payload, context);
      },
      'wp-publisher-agent': async () => {
        const wpService = new WpService();
        return wpService.publishPost(payload, context);
      },
      'ayrshare-agent': async () => {
        const ayrshareService = new AyrshareService();
        return ayrshareService.postContent(payload, context);
      },
      'mailchimp-agent': async () => {
        const mailchimpService = new MailchimpService();
        return mailchimpService.createCampaign(payload, context);
      },
      'budget-agent': async () => {
        // Simple budget logging
        logger.info('💰 Budget agent handling', { estimatedCost: payload.budgetEstimate });
        return { approved: true, logged: true };
      },
      'emergency-agent': async () => {
        await this.sendEmergencyAlert(payload, context);
        return { notified: true, severity: payload.urgency || 'critical' };
      },
      'monitoring-agent': async () => {
        const MonitoringAgent = (await import('./monitoringAgent.js')).default;
        return MonitoringAgent.handle(payload, context);
      }
    };
    
    const handler = agentHandlers[agentName];
    if (!handler) {
      throw new Error(`Agent not found: ${agentName}`);
    }
    
    logger.debug(`🏃‍♂️ Executing agent: ${agentName}`, { context });
    return handler();
  }

  /**
   * Handle agent result and determine next steps
   * @param {Object} result - Agent execution result
   * @param {Object} payload - Original payload
   * @param {Object} context - Execution context
   * @returns {Object} Final result
   */
  static async handleResult(result, payload, context) {
    // Handle handoffs
    if (result.handoffs && result.handoffs.length > 0) {
      logger.info('🔀 Handling handoffs', { 
        count: result.handoffs.length,
        requestId: context.requestId 
      });
      
      // Execute parallel handoffs
      const handoffResults = await Promise.allSettled(
        result.handoffs.map(handoff => 
          this.executeAgent(handoff.agent, { ...payload, ...handoff.context }, context)
        )
      );
      
      // Filter successful results
      const successfulResults = handoffResults
        .filter(r => r.status === 'fulfilled')
        .map(r => r.value);
      
      // Handle completion
      if (result.handoffType === 'parallel' && successfulResults.length === result.handoffs.length) {
        logger.info('✅ All parallel handoffs completed', { requestId: context.requestId });
        return this.handleParallelCompletion(successfulResults, payload, context);
      }
      
      result.handoffResults = successfulResults;
    }
    
    // Handle completion notifications
    if (result.status === 'completed' || result.status === 'published') {
      await this.sendCompletionNotification(payload, result, context);
    }
    
    return result;
  }

  /**
   * Handle completion of parallel handoffs
   * @param {Array} results - Results from parallel handoffs
   * @param {Object} payload - Original payload
   * @param {Object} context - Execution context
   * @returns {Object} Combined result
   */
  static async handleParallelCompletion(results, payload, context) {
    logger.info('🏁 Parallel handoffs completed successfully', { 
      requestId: context.requestId,
      resultCount: results.length 
    });
    
    // Combine results
    const combinedResult = {
      status: 'parallel_completed',
      requestId: context.requestId,
      timestamp: new Date().toISOString(),
      results: results.map((r, i) => ({
        agent: payload.handoffs?.[i]?.agent || `agent_${i}`,
        result: r
      }))
    };
    
    // Determine next steps based on results
    if (results.some(r => r.agent === 'writer-agent' && r.agent === 'bria-agent')) {
      // Both writer and bria completed - proceed to GitHub and WordPress
      combinedResult.nextSteps = [
        'github-commit-agent',
        'wp-publisher-agent'
      ];
    }
    
    return combinedResult;
  }

  /**
   * Send emergency alert
   * @param {Object} payload - Alert payload
   * @param {Object} context - Execution context
   */
  static async sendEmergencyAlert(payload, context) {
    const message = payload.message || `Emergency alert: ${payload.topic || 'Unknown issue'}`;
    const severity = payload.urgency || 'critical';
    
    const notificationPromises = [];
    
    // Slack notification
    if (process.env.A2A_SLACK_WEBHOOK) {
      notificationPromises.push(
        SlackService.sendAlert(message, severity, context)
      );
    }
    
    // Discord notification  
    if (process.env.A2A_DISCORD_WEBHOOK) {
      notificationPromises.push(
        DiscordService.sendAlert(message, severity, context)
      );
    }
    
    // Teams notification
    if (process.env.A2A_TEAMS_WEBHOOK) {
      notificationPromises.push(
        TeamsService.sendAlert(message, severity, context)
      );
    }
    
    await Promise.allSettled(notificationPromises);
    logger.info('🚨 Emergency alerts sent', { severity, platforms: notificationPromises.length });
  }

  /**
   * Send completion notification
   * @param {Object} payload - Original payload
   * @param {Object} result - Processing result
   * @param {Object} context - Execution context
   */
  static async sendCompletionNotification(payload, result, context) {
    const message = `✅ Content automation completed for: ${payload.topic}\n\n` +
                    `**Status:** ${result.status}\n` +
                    `**Platforms:** ${payload.platforms || 'WordPress'}\n` +
                    `**Links:** ${result.permalink ? `[View post](${result.permalink})` : 'Processing...'}`;
    
    const notifications = [];
    
    // Slack if configured
    if (process.env.A2A_SLACK_WEBHOOK) {
      notifications.push(SlackService.sendNotification(message, 'success', context));
    }
    
    // Discord if configured  
    if (process.env.A2A_DISCORD_WEBHOOK) {
      notifications.push(DiscordService.sendNotification(message, 'success', context));
    }
    
    await Promise.allSettled(notifications);
    logger.info('✅ Completion notifications sent', { requestId: context.requestId });
  }

  /**
   * Handle routing failure
   * @param {Object} payload - Original payload
   * @param {Error} error - Error object
   * @param {string} requestId - Request ID
   */
  static async handleRoutingFailure(payload, error, requestId) {
    try {
      const message = `❌ Content automation failed for: ${payload.topic}\n\n` +
                     `**Error:** ${error.message}\n` +
                     `**Request ID:** ${requestId}\n` +
                     `**Payload:** ${JSON.stringify(payload, null, 2).substring(0, 500)}...`;
      
      // Send to all available notification channels
      const notifications = [];
      
      if (process.env.A2A_SLACK_WEBHOOK) {
        notifications.push(SlackService.sendAlert(message, 'high', { requestId }));
      }
      
      if (process.env.A2A_DISCORD_WEBHOOK) {
        notifications.push(DiscordService.sendAlert(message, 'high', { requestId }));
      }
      
      await Promise.allSettled(notifications);
      
    } catch (notificationError) {
      logger.error('❌ Failed to send failure notification', notificationError);
    }
  }

  /**
   * Notify when budget is exceeded
   * @param {Object} payload - Original payload
   * @param {Object} budgetCheck - Budget check result
   */
  static async notifyBudgetExceeded(payload, budgetCheck) {
    const message = `💰 **Budget Exceeded**\n\n` +
                   `**Topic:** ${payload.topic}\n` +
                   `**Estimated Cost:** $${budgetCheck.estimated.toFixed(2)}\n` +
                   `**Remaining Budget:** $${budgetCheck.remaining.toFixed(2)}\n` +
                   `**Action:** Request rejected - please reduce scope or increase budget.`;
    
    if (process.env.A2A_SLACK_WEBHOOK) {
      await SlackService.sendAlert(message, 'medium', { budget: true });
    }
    
    if (process.env.A2A_DISCORD_WEBHOOK) {
      await DiscordService.sendAlert(message, 'medium', { budget: true });
    }
  }
}

// Fallback router for Vercel webhook
export async function fallbackRouter(req, res) {
  try {
    const payload = req.body;
    const requestId = `webhook_${Date.now()}`;
    
    logger.info('🌐 MCP Fallback Router invoked', { requestId });
    
    const result = await MCPHandoffRouter.route(payload, { requestId });
    
    // Return immediate response - processing continues async
    res.status(202).json({
      success: true,
      requestId,
      message: 'Content automation workflow initiated',
      status: result.status || 'processing'
    });
    
  } catch (error) {
    logger.error('❌ Fallback router failed', error);
    
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

export default MCPHandoffRouter;
