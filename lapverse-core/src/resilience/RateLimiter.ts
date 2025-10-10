type RateLimiterOptions = { limit: number; durationMs: number };

type Bucket = { count: number; resetAt: number };

export class RateLimiter {
  private buckets = new Map<string, Bucket>();
  constructor(private options: RateLimiterOptions){}

  tryConsume(key: string): boolean {
    const now = Date.now();
    const bucket = this.buckets.get(key);
    if (!bucket || now >= bucket.resetAt) {
      this.buckets.set(key, { count: 1, resetAt: now + this.options.durationMs });
      return true;
    }
    if (bucket.count < this.options.limit) {
      bucket.count += 1;
      return true;
    }
    return false;
  }

  getRemaining(key: string): number {
    const now = Date.now();
    const bucket = this.buckets.get(key);
    if (!bucket || now >= bucket.resetAt) return this.options.limit;
    return Math.max(0, this.options.limit - bucket.count);
  }

  getLimit(): number { return this.options.limit; }
}
