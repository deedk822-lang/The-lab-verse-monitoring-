/**
 * Enhanced Keyword Research Controller - Fixed
 * Handles multiple results properly with warnings
 */

const { processKeywordsWithDeepSearch } = require('../services/keywordResearchService');

module.exports = async (req, res) => {
  const { csv_path, num_topics = 4, enable_deep_search = true, deep_search_top_n = 3 } = req.body;

  if (!csv_path) {
    return res.status(400).json({
      error: 'Missing required field: csv_path'
    });
  }

  try {
    // Process keywords
    const results = await processKeywordsWithDeepSearch({
      csv_path,
      num_topics,
      enable_deep_search,
      deep_search_top_n
    });

    // Handle empty results
    if (!results || (Array.isArray(results) && results.length === 0)) {
      return res.status(500).json({
        error: 'Keyword processing returned no results',
        csv_path
      });
    }

    // Handle multiple results (log warning if unexpected)
    if (Array.isArray(results)) {
      if (results.length > 1) {
        console.warn(`⚠️  Keyword processing returned ${results.length} results, expected 1`);
        console.warn('   Using first result, others will be ignored');
      }

      // Use first result
      const result = results[0];

      return res.json({
        success: true,
        result,
        metadata: {
          csv_path,
          num_topics,
          enable_deep_search,
          deep_search_top_n,
          results_count: results.length,
          warning: results.length > 1 ?
            `Multiple results returned (${results.length}), using first result` :
            null
        }
      });
    }

    // Single result (not array)
    return res.json({
      success: true,
      result: results,
      metadata: {
        csv_path,
        num_topics,
        enable_deep_search,
        deep_search_top_n
      }
    });

  } catch (error) {
    console.error('Keyword research error:', error);

    // Differentiate between service errors and processing errors
    if (error.message.includes('COHERE_API_KEY') || error.message.includes('PERPLEXITY_API_KEY')) {
      return res.status(503).json({
        error: 'Service configuration error',
        message: 'Required API keys not configured',
        details: error.message,
        required: ['COHERE_API_KEY', 'PERPLEXITY_API_KEY (optional)']
      });
    }

    if (error.message.includes('ENOENT') || error.message.includes('file')) {
      return res.status(404).json({
        error: 'File not found',
        message: `CSV file not found: ${csv_path}`,
        details: error.message
      });
    }

    // General error
    return res.status(500).json({
      error: 'Keyword research failed',
      message: error.message,
      csv_path
    });
  }
};

// Health check endpoint
module.exports.healthCheck = async (req, res) => {
  try {
    // Check if required services are available
    const cohereAvailable = !!process.env.COHERE_API_KEY;
    const perplexityAvailable = !!process.env.PERPLEXITY_API_KEY;

    return res.json({
      status: cohereAvailable ? 'healthy' : 'degraded',
      services: {
        cohere: cohereAvailable ? 'available' : 'not_configured',
        perplexity: perplexityAvailable ? 'available' : 'not_configured',
        deep_search: perplexityAvailable ? 'enabled' : 'disabled'
      },
      note: !perplexityAvailable ?
        'Deep search disabled - Perplexity API not configured (optional)' :
        null
    });
  } catch (error) {
    return res.status(500).json({
      status: 'unhealthy',
      error: error.message
    });
  }
};