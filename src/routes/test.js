import express from 'express';
import { ProviderFactory } from 'services/ProviderFactory.js';
import { getAvailableProviders } from '../config/providers.js';
import { logger } from '../utils/logger.js';
import ayrshareService from '../services/ayrshareService.js';

const router = express.Router();

router.post('/run-all', async (req, res) => {
  // ... (rest of the file is unchanged)
