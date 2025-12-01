const express = require('express');
const router = express.Router();
const contentController = require('../controllers/content');

// Content creation endpoint
router.post('/content', contentController.createContent.bind(contentController));

// Test endpoint (no real API calls)
router.post('/test', contentController.testEndpoint.bind(contentController));
router.get('/test', contentController.testEndpoint.bind(contentController));

// Stats endpoint
router.get('/stats', contentController.getStats.bind(contentController));

// Health check
router.get('/health', contentController.healthCheck.bind(contentController));

module.exports = router;
