type BreakerOptions = { timeout: number; errorThreshold: number; reset: number };

export class CircuitBreaker<TResult> {
  private failures = 0;
  private state: 'closed'|'open'|'half-open' = 'closed';
  private openedAt = 0;

  constructor(private fn: () => Promise<TResult>, private opts: BreakerOptions){ }

  async execute(invocation?: () => Promise<TResult>): Promise<TResult> {
    const now = Date.now();
    if (this.state === 'open' && now - this.openedAt < this.opts.reset) {
      throw new Error('circuit-open');
    }
    if (this.state === 'open' && now - this.openedAt >= this.opts.reset) {
      this.state = 'half-open';
    }

    const run = invocation ?? this.fn;
    try {
      const result = await this.withTimeout(run());
      this.failures = 0;
      this.state = 'closed';
      return result;
    } catch (err) {
      this.failures += 1;
      if (this.failures >= this.opts.errorThreshold) {
        this.state = 'open';
        this.openedAt = Date.now();
      }
      throw err;
    }
  }

  private withTimeout<T>(p: Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      const to = setTimeout(() => reject(new Error('timeout')), this.opts.timeout);
      p.then(v => { clearTimeout(to); resolve(v); })
       .catch(e => { clearTimeout(to); reject(e); });
    });
  }
}
