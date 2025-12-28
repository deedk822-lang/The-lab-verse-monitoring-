// utils/retryWithBackoff.js - FIXED
export async function retryWithBackoff(fn, maxRetries = 3, initialDelay = 1000, maxDelay = 30000) {
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      if (i < maxRetries - 1) {
        // ✅ Exponential backoff with maximum delay cap
        const delay = Math.min(initialDelay * (2 ** i), maxDelay);

        console.log(`Retry attempt ${i + 1}/${maxRetries} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}
