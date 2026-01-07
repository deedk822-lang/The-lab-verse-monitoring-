
import express from 'express';

const app = express();
const port = 7860;

// Middleware to parse JSON bodies
app.use(express.json());

// Root endpoint for health checks
app.get('/', (req, res) => {
  res.status(200).json({ message: 'RankYak Bridge alive' });
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
