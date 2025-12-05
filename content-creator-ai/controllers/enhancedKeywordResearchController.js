const { PythonShell } = require('python-shell');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;

const storage = multer.diskStorage({
  destination: async (req, file, cb) => {
    const uploadDir = path.join(__dirname, '../uploads');
    await fs.mkdir(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}-${file.originalname}`);
  }
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    if (path.extname(file.originalname).toLowerCase() !== '.csv') {
      return cb(new Error('Only CSV files are allowed'));
    }
    cb(null, true);
  }
});

class EnhancedKeywordResearchController {
  /**
   * Process keywords with Perplexity deep search
   */
  static async processWithDeepSearch(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No CSV file uploaded' });
      }

      const numTopics = parseInt(req.body.num_topics) || 4;
      const enableDeepSearch = req.body.enable_deep_search !== 'false';
      const deepSearchTopN = parseInt(req.body.deep_search_top_n) || 3;
      const filePath = req.file.path;

      const options = {
        mode: 'json',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: path.join(__dirname, '../services'),
        args: [
          '--csv-path', filePath,
          '--num-topics', numTopics,
          '--enable-deep-search', enableDeepSearch,
          '--deep-search-top-n', deepSearchTopN
        ]
      };

      // Execute Python script
      PythonShell.run('keywordResearchWithPerplexity.py', options, async (err, results) => {
        // Clean up uploaded file
        await fs.unlink(filePath).catch(console.error);

        if (err) {
          console.error('Python script error:', err);
          return res.status(500).json({
            error: 'Keyword processing failed',
            details: err.message
          });
        }

        const result = results[0];

        res.json({
          success: true,
          data: {
            topics: result.enriched_topics,
            summary: result.summary,
            topic_summary: result.topic_summary
          },
          message: `Processed ${result.summary.total_keywords} keywords into ${result.summary.num_topics} topics with deep search insights`
        });
      });
    } catch (error) {
      console.error('Enhanced keyword research error:', error);
      res.status(500).json({
        error: 'Internal server error',
        details: error.message
      });
    }
  }

  /**
   * Get detailed insights for a specific topic
   */
  static async getTopicInsights(req, res) {
    try {
      const { topic_name, keywords } = req.body;

      if (!topic_name || !keywords) {
        return res.status(400).json({
          error: 'topic_name and keywords array required'
        });
      }

      // Call Python service for deep search on single topic
      const options = {
        mode: 'json',
        pythonPath: 'python3',
        scriptPath: path.join(__dirname, '../services'),
        args: ['--single-topic', topic_name, '--keywords', JSON.stringify(keywords)]
      };

      PythonShell.run('keywordResearchWithPerplexity.py', options, (err, results) => {
        if (err) {
          return res.status(500).json({ error: 'Failed to get insights' });
        }

        res.json({
          success: true,
          insights: results
        });
      });
    } catch (error) {
      console.error('Topic insights error:', error);
      res.status(500).json({ error: 'Failed to retrieve topic insights' });
    }
  }
}

module.exports = { EnhancedKeywordResearchController, upload };
