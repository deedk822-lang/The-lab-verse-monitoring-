const express = require('express');
const Joi = require('joi');
const validate = require('../middleware/validate');
const TTSService = require('../services/ttsService');

const router = express.Router();
const service = new TTSService();

const schema = Joi.object({
  text: Joi.string().min(1).max(10000).required(),
  voiceId: Joi.string().default('21m00Tcm4TlvDq8ikWAM'),
  stability: Joi.number().min(0).max(1).default(0.75),
  similarityBoost: Joi.number().min(0).max(1).default(0.75)
});

router.post('/', validate(schema), async (req, res) => {
  try {
    const { audioBuffer, cached } = await service.generateSpeech(req.body.text, req.body);
    if (cached) res.set('X-Cache', 'HIT');
    res.set({'Content-Type':'audio/mpeg','Content-Disposition':'attachment; filename="speech.mp3"'});
    res.send(audioBuffer);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;