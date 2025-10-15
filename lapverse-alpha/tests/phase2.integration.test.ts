import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { LocalVLProvider } from '../src/agents/providers/LocalVLProvider';
import { Task } from '../src/types';
import * as fs from 'fs/promises';
import * as path from 'path';
import { fetchWithTimeout } from '../src/utils/http';
import { Ollama } from 'ollama';

const shouldRunIntegrationTest = process.env.RUN_REAL_INTEGRATION === 'true';
const tempImagePath = path.join(__dirname, 'temp_cat_image.jpg');
const imageUrl = 'http://www.public-domain-image.com/public-domain-images-pictures-free-stock-photos/fauna-animals-public-domain-images-pictures/cats-and-kittens-public-domain-images-pictures/cat-domestic.jpg';

describe.runIf(shouldRunIntegrationTest)('Phase2: Hardened Provider Integration', () => {

  beforeAll(async () => {
    const ollama = new Ollama({ host: process.env.OLLAMA_HOST || 'http://localhost:11434' });
    console.log('Pulling moondream model for integration test...');
    await ollama.pull({ model: 'moondream', stream: false });
    console.log('Model pull complete.');

    console.log('Downloading image for integration test...');
    const response = await fetchWithTimeout(imageUrl, {}, 15000);
    if (!response.ok) throw new Error(`Failed to download image: ${response.statusText}`);
    const arrayBuffer = await response.arrayBuffer();
    await fs.writeFile(tempImagePath, Buffer.from(arrayBuffer));
    console.log('Image downloaded successfully.');
  }, 3 * 60 * 1000); // 3 minute timeout for model and image download

  afterAll(async () => {
    try {
      await fs.unlink(tempImagePath);
      console.log('Cleaned up temporary image.');
    } catch (error) {
      // Ignore cleanup errors
    }
  });

  it('Integration: LocalVLProvider should process a local image and return a valid response', async () => {
    const provider = new LocalVLProvider();
    const task: Task = {
      id: 'test-task-local-1',
      content: 'A simple photo of a cat.', // Content isn't used by the new prompt
      imageUrl: tempImagePath
    };

    const response = await provider.evaluateVisual(task);

    expect(response).toBeDefined();
    expect(response.description).toBeTypeOf('string');
    expect(response.description.length).toBeGreaterThan(10);
    expect(['Good', 'Bad', 'Uncertain']).toContain(response.assessment);

    console.log('LocalVLProvider Integration Test Passed. Description:', response.description);
  }, 90000); // 90s for the inference itself
});