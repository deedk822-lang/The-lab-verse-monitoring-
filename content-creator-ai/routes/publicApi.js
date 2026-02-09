const express = require('express');
const router = express.Router();
const contentController = require('../controllers/content');

// Test endpoint (no real API calls)
router.post('/test', contentController.testEndpoint.bind(contentController));
router.get('/test', contentController.testEndpoint.bind(contentController));

// Health check
router.get('/health', contentController.healthCheck.bind(contentController));

module.exports = router;
