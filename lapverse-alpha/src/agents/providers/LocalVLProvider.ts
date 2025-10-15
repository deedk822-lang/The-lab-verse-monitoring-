import { Ollama } from 'ollama';
import { z } from 'zod';
import { fetchWithTimeout } from '../../utils/http';
import { retry } from '../../utils/retry';
import { Task } from '../../types';

// A more generic response schema for simpler VL models
export const VLEvaluationSchema = z.object({
  description: z.string().min(10),
  assessment: z.enum(["Good", "Bad", "Uncertain"]),
});
export type VLEvaluation = z.infer<typeof VLEvaluationSchema>;

export class LocalVLProvider {
  private ollama: Ollama;
  private model = 'moondream'; // Using the smaller, more efficient model

  constructor() {
    const ollamaHost = process.env.OLLAMA_HOST || 'http://localhost:11434';
    this.ollama = new Ollama({ host: ollamaHost });
  }

  async evaluateVisual(task: Task & { imageUrl?: string }): Promise<VLEvaluation> {
    if (!task.imageUrl) throw new Error('imageUrl required for this task');

    let imageBuffer: Buffer;

    if (/^https?:\/\//.test(task.imageUrl)) {
      imageBuffer = await retry(async () => {
        const response = await fetchWithTimeout(task.imageUrl!, {}, 8000);
        if (!response.ok) throw new Error(`Image fetch failed with status: ${response.status}`);
        const arrayBuffer = await response.arrayBuffer();
        return Buffer.from(arrayBuffer);
      }, 2, 300);
    } else {
      const fs = await import('fs/promises');
      imageBuffer = await fs.readFile(task.imageUrl);
    }

    // A simpler prompt for the moondream model
    const prompt = `Describe this image and assess its quality. Respond in JSON format with keys "description" and "assessment" (Good, Bad, or Uncertain).`;

    const rawResponse = await retry(async () => {
      const resp = await this.ollama.generate({
        model: this.model,
        prompt,
        images: [imageBuffer],
        format: 'json',
      });
      return resp.response;
    }, 3, 500);

    let parsedJson: unknown;
    try {
      parsedJson = JSON.parse(rawResponse);
    } catch (e) {
      console.error("Failed to parse VL model response as JSON:", rawResponse);
      throw new Error('Local VL provider returned non-JSON response.');
    }

    const validationResult = VLEvaluationSchema.safeParse(parsedJson);
    if (!validationResult.success) {
      console.error("VL model response schema mismatch:", validationResult.error.format());
      throw new Error('Local VL provider response failed schema validation.');
    }

    return validationResult.data;
  }
}