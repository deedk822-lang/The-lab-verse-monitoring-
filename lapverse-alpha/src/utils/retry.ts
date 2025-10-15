export async function retry<T>(
  fn: () => Promise<T>,
  attempts = 3,
  backoffMs = 200
): Promise<T> {
  let lastErr: any;
  for (let i = 0; i < attempts; i++) {
    try {
      if (i) await new Promise(r => setTimeout(r, backoffMs * Math.pow(2, i - 1)));
      return await fn();
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}