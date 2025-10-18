const express = require('express');
const AlertService = require('../services/alertService');

const router = express.Router();
const alerts = new AlertService();

router.post('/slack', async (req, res) => {
  try {
    const { title, message, severity = 'info', details } = req.body;
    const out = await alerts.sendSlackAlert(title, message, severity, details);
    res.json({ success: true, ...out });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

module.exports = router;