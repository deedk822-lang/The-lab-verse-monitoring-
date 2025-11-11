// Mock implementation for fast tests
// Jest will automatically use this when contentGenerator is imported

export async function generateContent(prompt) {
  return `Mocked response for: ${prompt}`;
}

export async function* streamContent(prompt) {
  yield 'Mock ';
  yield 'stream ';
  yield `data for: ${prompt}`;
}

export function validatePrompt(prompt) {
  return typeof prompt === 'string' && prompt.length > 0;
}
