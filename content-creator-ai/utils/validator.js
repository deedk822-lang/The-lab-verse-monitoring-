const Joi = require('joi');

const contentRequestSchema = Joi.object({
  topic: Joi.string().min(3).max(500).required(),
  audience: Joi.string().min(2).max(200).default('general audience'),
  tone: Joi.string().valid('professional', 'casual', 'friendly', 'formal', 'humorous', 'technical').default('professional'),
  language: Joi.string().min(2).max(10).default('en'),
  media_type: Joi.string().valid('text', 'image', 'video', 'audio', 'multimodal').required(),
  provider: Joi.string().valid('openai', 'google', 'localai', 'zai', 'anthropic', 'perplexity', 'auto').default('auto'),
  
  // Text-specific options
  length: Joi.when('media_type', {
    is: 'text',
    then: Joi.string().valid('short', 'medium', 'long').default('medium'),
    otherwise: Joi.forbidden()
  }),
  format: Joi.when('media_type', {
    is: 'text',
    then: Joi.string().valid('markdown', 'html', 'plain').default('markdown'),
    otherwise: Joi.forbidden()
  }),
  
  // Image-specific options
  aspect_ratio: Joi.when('media_type', {
    is: Joi.string().valid('image', 'video'),
    then: Joi.string().valid('1:1', '16:9', '9:16', '4:3', '3:4').default('16:9'),
    otherwise: Joi.forbidden()
  }),
  style: Joi.when('media_type', {
    is: 'image',
    then: Joi.string().max(200).default('photorealistic'),
    otherwise: Joi.forbidden()
  }),
  
  // Video-specific options
  duration: Joi.when('media_type', {
    is: 'video',
    then: Joi.number().min(1).max(60).default(10), // seconds
    otherwise: Joi.forbidden()
  }),
  
  // Audio-specific options
  voice: Joi.when('media_type', {
    is: 'audio',
    then: Joi.string().valid('alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer').default('alloy'),
    otherwise: Joi.forbidden()
  }),
  
  // Additional options
  keywords: Joi.array().items(Joi.string().max(50)).max(10).default([]),
  cta: Joi.string().max(200).optional(),
  include_seo: Joi.boolean().default(true),
  include_social: Joi.boolean().default(true),
  enable_research: Joi.boolean().default(true),
  
  // Advanced options
  thinking_mode: Joi.boolean().default(false), // For Z.AI GLM-4.6
  streaming: Joi.boolean().default(false),
  temperature: Joi.number().min(0).max(2).default(0.7),
  max_tokens: Joi.number().min(100).max(200000).optional()
});

function validateContentRequest(data) {
  return contentRequestSchema.validate(data, { abortEarly: false, stripUnknown: true });
}

function sanitizeInput(str) {
  if (typeof str !== 'string') return str;
  
  // Remove potentially dangerous characters
  return str
    .replace(/[<>]/g, '') // Remove HTML tags
    .replace(/[{}]/g, '') // Remove curly braces
    .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
    .trim();
}

function enhanceRequest(validated) {
  const enhanced = { ...validated };
  
  // Auto-generate keywords if not provided
  if (enhanced.keywords.length === 0) {
    const words = enhanced.topic.toLowerCase().split(/\s+/);
    enhanced.keywords = words.slice(0, 5);
  }
  
  // Auto-generate CTA if not provided
  if (!enhanced.cta) {
    if (enhanced.media_type === 'text') {
      enhanced.cta = 'Learn more about this topic';
    } else if (enhanced.media_type === 'image') {
      enhanced.cta = 'Explore visually';
    } else if (enhanced.media_type === 'video') {
      enhanced.cta = 'Watch to discover more';
    } else if (enhanced.media_type === 'audio') {
      enhanced.cta = 'Listen to learn more';
    }
  }
  
  return enhanced;
}

module.exports = {
  validateContentRequest,
  sanitizeInput,
  enhanceRequest
};
