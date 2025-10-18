const express = require('express');
const Joi = require('joi');
const validate = require('../middleware/validate');
const VideoService = require('../services/videoService');

const router = express.Router();
const service = new VideoService();

const schema = Joi.object({
  prompt: Joi.string().min(3).max(2000).required(),
  duration: Joi.number().integer().min(5).max(60).default(10),
  resolution: Joi.string().valid('720p', '1080p').default('1080p'),
  style: Joi.string().valid('cinematic', 'animated').default('cinematic')
});

router.post('/generate', validate(schema), async (req, res) => {
  try {
    const meta = await service.generateVideo(req.body.prompt, req.body);
    res.json({ success: true, ...meta });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;