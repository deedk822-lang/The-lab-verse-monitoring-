const express = require('express');
const router = express.Router();
const { EnhancedKeywordResearchController, upload } = require('../controllers/enhancedKeywordResearchController');

/**
 * @route   POST /api/keyword-research/deep-search
 * @desc    Process keywords with Cohere clustering + Perplexity deep search
 * @access  Public
 */
router.post('/deep-search',
  upload.single('file'),
  EnhancedKeywordResearchController.processWithDeepSearch
);

/**
 * @route   POST /api/keyword-research/topic-insights
 * @desc    Get Perplexity insights for a specific topic
 * @access  Public
 */
router.post('/topic-insights',
  EnhancedKeywordResearchController.getTopicInsights
);

module.exports = router;
