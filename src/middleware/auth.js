const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../config/env');

module.exports = (req, res, next) => {
  const hdr = req.headers.authorization;
  if (!hdr) return res.status(401).json({ error: 'Missing token' });
  try {
    req.user = jwt.verify(hdr.split(' ')[1], JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Invalid token' });
  }
};