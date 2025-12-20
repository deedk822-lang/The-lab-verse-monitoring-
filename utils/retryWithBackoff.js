/**
 * Retries a function with exponential backoff.
 *
 * @param {Function} fn The function to retry.
 * @param {number} maxRetries The maximum number of retries.
 * @param {number} delay The initial delay in milliseconds.
 * @returns {Promise<any>} A promise that resolves with the result of the function.
 */
export async function retryWithBackoff(fn, maxRetries = 3, delay = 1000) {
  let lastError;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * 2 ** i));
      }
    }
  }
  throw lastError;
}
