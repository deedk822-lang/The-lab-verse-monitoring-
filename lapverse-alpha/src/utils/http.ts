export async function fetchWithTimeout(url: string, opts: RequestInit = {}, timeoutMs = 10_000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...opts, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(id);
  }
}