const { PythonShell } = require('python-shell');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;

// Configure multer for file uploads
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

class KeywordResearchController {
  /**
   * Process keyword research from uploaded CSV
   */
  static async processKeywords(req, res) {
    try {
      if (!req.file) {
        return res.status(400).json({ error: 'No CSV file uploaded' });
      }

      const numTopics = parseInt(req.body.num_topics) || 4;
      const filePath = req.file.path;

      // Call Python service
      const options = {
        mode: 'json',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: path.join(__dirname, '../services'),
        args: [filePath, numTopics]
      };

      PythonShell.run('keywordResearchService.py', options, async (err, results) => {
        // Clean up uploaded file
        await fs.unlink(filePath).catch(console.error);

        if (err) {
          console.error('Python script error:', err);
          return res.status(500).json({ error: 'Keyword processing failed', details: err.message });
        }

        const result = results[0];
        res.json({
          success: true,
          data: result,
          message: `Processed ${result.total_keywords} keywords into ${result.num_topics} topics`
        });
      });
    } catch (error) {
      console.error('Keyword research error:', error);
      res.status(500).json({ error: 'Internal server error', details: error.message });
    }
  }

  /**
   * Generate content ideas from topic analysis
   */
  static async generateContentIdeas(req, res) {
    try {
      const { topic_summary } = req.body;

      if (!topic_summary || !Array.isArray(topic_summary)) {
        return res.status(400).json({ error: 'topic_summary array required' });
      }

      // Call Python service
      const options = {
        mode: 'json',
        pythonPath: 'python3',
        pythonOptions: ['-u'],
        scriptPath: path.join(__dirname, '../services'),
        args: [JSON.stringify(topic_summary)]
      };

      PythonShell.run('keywordResearchService.py', options, (err, results) => {
        if (err) {
          console.error('Python script error:', err);
          return res.status(500).json({ error: 'Content idea generation failed', details: err.message });
        }

        res.json({
          success: true,
          ideas: results
        });
      });
    } catch (error) {
      console.error('Content idea generation error:', error);
      res.status(500).json({ error: 'Failed to generate content ideas', details: error.message });
    }
  }
}

module.exports = { KeywordResearchController, upload };
