const express = require('express');
const router = express.Router();
const contentController = require('../controllers/content');

// Content creation endpoint
router.post('/content', contentController.createContent.bind(contentController));

// Stats endpoint
router.get('/stats', contentController.getStats.bind(contentController));

module.exports = router;
