const express = require('express');
const router = express.Router();
const { KeywordResearchController, upload } = require('../controllers/keywordResearchController');

/**
 * @route   POST /api/keyword-research
 * @desc    Upload and process keyword CSV file
 * @access  Public (add auth middleware as needed)
 */
router.post('/', upload.single('file'), KeywordResearchController.processKeywords);

/**
 * @route   POST /api/keyword-research/content-ideas
 * @desc    Generate content ideas from topic analysis
 * @access  Public
 */
router.post('/content-ideas', KeywordResearchController.generateContentIdeas);

module.exports = router;
