// src/services/testWorkflow.js
import { generateContent, streamContent } from './contentGenerator.js';

/**
 * Test the AI workflow by generating and streaming content.
 */
(async () => {
  try {
    // Test content generation
    const content = await generateContent("Write a short message about AI", {
      maxTokens: 100,
      temperature: 0.7,
    });
    console.log("Generated Content:", content);

    // Test content streaming
    console.log("\nStreamed Content:");
    for await (const chunk of streamContent("Count to 5", {
      maxTokens: 50,
    })) {
      process.stdout.write(chunk);
    }
  } catch (error) {
    console.error("Error:", error.message);
  }
})();
