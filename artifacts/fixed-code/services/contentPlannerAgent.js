// src/services/contentPlannerAgent.js
import { mcpRequest } from './mcpService.js';
import { githubService } from './githubService.js';
import { wpService } from './wpService.js';
import { logger } from '../utils/logger.js';

/**
 * Content Planner Agent - orchestrates the content creation workflow
 * This agent handles the planning phase and coordinates handoffs to other agents
 */
export class ContentPlannerAgent {
  /**
   * Main handler for content planning requests
   * @param {Object} payload - RankYak webhook payload
   * @param {Object} context - Execution context including handoffs
   * @returns {Object} Planning result with handoff instructions
   */
  static async handle(payload, context = {}) {
    try {
      logger.info('🧠 Content Planner Agent started', { topic: payload.topic, intent: payload.intent });
      
      // Step 1: Analyze the request and create comprehensive plan
      const contentPlan = await this.createContentPlan(payload);
      logger.info('📋 Content plan created', { planId: contentPlan.id });
      
      // Step 2: Estimate costs and check budget
      const costEstimate = await this.estimateCosts(contentPlan);
      logger.info('💰 Cost estimate', { total: costEstimate.total, currency: 'USD' });
      
      // Step 3: Initiate parallel handoffs for content generation
      const handoffs = await this.initiateHandoffs(contentPlan, context);
      
      // Step 4: Prepare response with handoff instructions
      const result = {
        status: 'initiated',
        contentPlan,
        costEstimate,
        handoffs,
        nextSteps: [
          'Wait for writer-agent and bria-agent to complete',
          'Then proceed to github-commit-agent',
          'Finally publish to WordPress and social media'
        ],
        meta: {
          requestId: context.requestId || `plan_${Date.now()}`,
          timestamp: new Date().toISOString(),
          source: 'rankyak-webhook'
        }
      };
      
      logger.info('✅ Content planning completed successfully', { 
        planId: contentPlan.id,
        handoffs: handoffs.length 
      });
      
      return result;
      
    } catch (error) {
      logger.error('❌ Content planning failed', { 
        error: error.message, 
        stack: error.stack,
        payload 
      });
      
      // Fallback to emergency notification
      await this.handleFailure(payload, error);
      
      throw error;
    }
  }

  /**
   * Create comprehensive content plan from RankYak payload
   * @param {Object} payload - RankYak webhook payload
   * @returns {Object} Content plan with all necessary details
   */
  static async createContentPlan(payload) {
    const { topic, keywords = [], audience = 'tech professionals', tone = 'professional', intent } = payload;
    
    // Generate slug from topic
    const slug = this.generateSlug(topic);
    
    // Create structured outline using MCP
    const outline = await mcpRequest({
      agent: 'writer',
      input: {
        task: 'create_outline',
        topic,
        audience,
        keywords,
        tone,
        context: `Lab Verse Monitoring Stack - AI-powered infrastructure monitoring`
      },
      provider: payload.provider || 'zai'
    });
    
    // Generate image requirements
    const imageRequirements = await mcpRequest({
      agent: 'creative',
      input: {
        task: 'generate_image_requirements',
        topic,
        audience,
        style: 'tech professional, clean, modern',
        context: 'Hero image for AI monitoring blog post'
      },
      provider: payload.provider || 'gemini'
    });
    
    return {
      id: `plan_${Date.now()}`,
      topic,
      slug,
      keywords,
      audience,
      tone,
      intent,
      outline: outline.output,
      imageRequirements: imageRequirements.output,
      channels: payload.platforms?.split(',') || ['blog', 'linkedin', 'twitter'],
      metadata: {
        source: 'rankyak',
        createdAt: new Date().toISOString(),
        version: '1.0'
      }
    };
  }

  /**
   * Estimate costs for the content plan
   * @param {Object} contentPlan - Content plan object
   * @returns {Object} Cost breakdown
   */
  static async estimateCosts(contentPlan) {
    const costs = {
      aiGeneration: 0,
      imageGeneration: 0,
      socialPosting: 0,
      emailCampaign: 0,
      total: 0
    };
    
    // AI text generation costs (based on tokens)
    costs.aiGeneration = 0.02 * contentPlan.outline.sections.length;
    
    // Image generation costs (Bria API)
    costs.imageGeneration = 0.15 * contentPlan.imageRequirements.prompts.length;
    
    // Social media posting costs (Ayrshare)
    costs.socialPosting = 0.01 * contentPlan.channels.filter(c => ['twitter', 'linkedin', 'facebook', 'instagram'].includes(c)).length;
    
    // Email campaign costs (Mailchimp)
    if (contentPlan.channels.includes('email')) {
      costs.emailCampaign = 0.05;
    }
    
    costs.total = Object.values(costs).reduce((sum, val) => sum + val, 0);
    
    return costs;
  }

  /**
   * Initiate parallel handoffs to writer and bria agents
   * @param {Object} contentPlan - Content plan
   * @param {Object} context - Execution context
   * @returns {Array} Handoff instructions
   */
  static async initiateHandoffs(contentPlan, context) {
    const handoffs = [];
    const requestId = context.requestId || `req_${Date.now()}`;
    
    // Handoff 1: Writer agent for text generation
    handoffs.push({
      agent: 'writer-agent',
      context: {
        requestId,
        contentPlan,
        task: 'generate_full_article',
        outputFormat: 'html',
        includeSocialVariants: true,
        includeEmailCopy: contentPlan.channels.includes('email')
      },
      handoffType: 'parallel'
    });
    
    // Handoff 2: Bria agent for image generation
    handoffs.push({
      agent: 'bria-agent',
      context: {
        requestId,
        contentPlan,
        task: 'generate_hero_image',
        requirements: contentPlan.imageRequirements
      },
      handoffType: 'parallel'
    });
    
    logger.info('🔄 Initiating parallel handoffs', { 
      count: handoffs.length,
      requestId 
    });
    
    return handoffs;
  }

  /**
   * Handle completion of parallel handoffs and proceed to GitHub/WordPress
   * @param {Object} context - Execution context
   * @param {Array} results - Results from parallel handoffs
   * @returns {Object} Final handoff instructions
   */
  static async handleHandoffCompletion(context, results) {
    try {
      logger.info('✅ Parallel handoffs completed', { 
        requestId: context.requestId,
        resultCount: results.length 
      });
      
      // Extract results from writer and bria agents
      const writerResult = results.find(r => r.agent === 'writer-agent');
      const briaResult = results.find(r => r.agent === 'bria-agent');
      
      if (!writerResult || !briaResult) {
        throw new Error('Missing required handoff results');
      }
      
      // Prepare GitHub commit
      const githubHandoff = await this.prepareGitHubCommit(
        context.contentPlan,
        writerResult.output,
        briaResult.output
      );
      
      // Prepare WordPress publish
      const wpHandoff = await this.prepareWordPressPublish(
        context.contentPlan,
        writerResult.output,
        briaResult.output
      );
      
      return {
        status: 'ready_for_publishing',
        githubHandoff,
        wpHandoff,
        nextHandoffs: [
          {
            agent: 'github-commit-agent',
            context: githubHandoff
          },
          {
            agent: 'wp-publisher-agent', 
            context: wpHandoff
          }
        ]
      };
      
    } catch (error) {
      logger.error('❌ Handoff completion failed', { 
        error: error.message,
        stack: error.stack 
      });
      throw error;
    }
  }

  /**
   * Prepare GitHub commit data
   * @param {Object} contentPlan - Content plan
   * @param {Object} writerOutput - Writer agent output
   * @param {Object} briaOutput - Bria agent output
   * @returns {Object} GitHub commit data
   */
  static async prepareGitHubCommit(contentPlan, writerOutput, briaOutput) {
    const frontMatter = {
      title: contentPlan.topic,
      date: new Date().toISOString().split('T')[0],
      draft: false,
      hero_image_url: briaOutput.imageUrl,
      bria_attribution: briaOutput.attributionToken,
      source: 'rankyak-webhook',
      keywords: contentPlan.keywords.join(', '),
      audience: contentPlan.audience,
      tone: contentPlan.tone,
      cost_tracking: {
        total_cost: 0, // Will be updated later
        ai_cost: writerOutput.cost,
        image_cost: briaOutput.cost
      }
    };
    
    const content = `# ${contentPlan.topic}\n\n${writerOutput.article}\n\n`;
    
    return {
      path: `content/posts/${contentPlan.slug}.md`,
      content,
      frontMatter,
      message: `🤖 Auto-generated post: ${contentPlan.topic}`
    };
  }

  /**
   * Prepare WordPress publish data
   * @param {Object} contentPlan - Content plan
   * @param {Object} writerOutput - Writer agent output
   * @param {Object} briaOutput - Bria agent output
   * @returns {Object} WordPress publish data
   */
  static async prepareWordPressPublish(contentPlan, writerOutput, briaOutput) {
    return {
      title: contentPlan.topic,
      slug: contentPlan.slug,
      content: writerOutput.htmlContent,
      excerpt: writerOutput.excerpt,
      status: 'draft', // Will be published later
      featured_media: briaOutput.wpMediaId,
      categories: ['AI', 'Monitoring', 'Automation'],
      tags: contentPlan.keywords,
      meta: {
        github_url: '', // Will be filled after GitHub commit
        bria_attribution: briaOutput.attributionToken,
        source: 'rankyak-webhook'
      }
    };
  }

  /**
   * Handle failure scenario
   * @param {Object} payload - Original payload
   * @param {Error} error - Error object
   */
  static async handleFailure(payload, error) {
    try {
      await mcpRequest({
        agent: 'emergency',
        input: {
          message: `Content planning failed for topic: ${payload.topic}`,
          error: error.message,
          severity: 'high',
          context: 'Lab Verse Monitoring Stack content automation'
        },
        provider: 'gemini'
      });
    } catch (notificationError) {
      logger.error('❌ Failed to send failure notification', notificationError);
    }
  }

  /**
   * Generate URL-friendly slug from topic
   * @param {string} topic - Article topic
   * @returns {string} URL slug
   */
  static generateSlug(topic) {
    return topic
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 50);
  }
}

// Handoff completion handler - called when parallel handoffs finish
export async function handleContentPlannerHandoffCompletion(context, results) {
  return ContentPlannerAgent.handleHandoffCompletion(context, results);
}

export default ContentPlannerAgent;
