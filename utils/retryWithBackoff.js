/**
 * Retries an async function with exponential backoff.
 *
 * @param {Function} fn The async function to retry.
 * @param {number} [maxRetries=3] The maximum number of retries.
 * @param {number} [delay=1000] The initial delay in milliseconds.
 * @param {number} [maxDelay=30000] The maximum delay in milliseconds.
 * @returns {Promise<any>} A promise that resolves with the result of the function.
 * @throws {Error} Throws the last error if all retries fail.
 */
export async function retryWithBackoff(fn, maxRetries = 3, delay = 1000, maxDelay = 30000) {
  let lastError;
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        const backoffDelay = Math.min(delay * 2 ** i, maxDelay);
        await new Promise(resolve => setTimeout(resolve, backoffDelay));
      }
    }
  }
  throw lastError;
}
