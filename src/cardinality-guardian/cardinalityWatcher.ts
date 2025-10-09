import fetch from 'node-fetch';

interface SeriesMeta {
  count: number;
  lastAlert: number;
  lastSeen: number;
}

export class CardinalityWatcher {
  private store = new Map<string, SeriesMeta>();
  private readonly max: number;
  private readonly warnRatio: number;
  private readonly cooldownMs: number;
  private readonly ttlMs: number;
  private readonly webhook?: string;

  /* Simple async mutex per key (queue-based, no deadlocks) */
  private locks = new Map<string, Promise<void>>();
  private resolvers = new Map<string, () => void>();

  constructor(opts?: {
    maxSeries?: number;
    warnRatio?: number;
    alertCooldownMs?: number;
    staleAgeMs?: number;
    slackWebhook?: string;
  }) {
    this.max = opts?.maxSeries ?? 100_000;
    this.warnRatio = opts?.warnRatio ?? 0.8;
    this.cooldownMs = opts?.alertCooldownMs ?? 5 * 60 * 1000;
    this.ttlMs = opts?.staleAgeMs ?? 24 * 60 * 60 * 1000;
    this.webhook = opts?.slackWebhook ?? process.env.SLACK_WEBHOOK;
  }

  /** Main API: return true = accepted, false = dropped */
  async validate(metric: string, labels: Record<string, string>): Promise<boolean> {
    const key = this.keyOf(metric, labels);
    await this.lock(key);
    try {
      const now = Date.now();
      let meta = this.store.get(key);
      if (!meta) {
        meta = { count: 0, lastAlert: 0, lastSeen: now };
      }
      meta.count += 1;
      meta.lastSeen = now;
      this.store.set(key, meta);

      // Hard limit breached → drop + delete
      if (meta.count > this.max) {
        this.store.delete(key);
        this.sendDropAlert(metric, labels, meta.count).catch(() => {/* ignore */});
        return false;
      }

      // Warning threshold + cooldown
      const warnThresh = Math.floor(this.max * this.warnRatio);
      if (meta.count >= warnThresh && now - meta.lastAlert >= this.cooldownMs) {
        meta.lastAlert = now;
        this.sendWarnAlert(metric, meta.count).catch(() => {/* ignore */});
      }
      return true;
    } finally {
      this.unlock(key);
    }
  }

  /** Periodic housekeeping—call from a timer */
  cleanup(): void {
    const horizon = Date.now() - this.ttlMs;
    for (const [k, m] of this.store.entries()) {
      if (m.lastSeen < horizon && m.count < this.max * 0.1) {
        this.store.delete(k);
      }
    }
  }

  /* ---------- private ---------- */
  private keyOf(metric: string, labels: Record<string, string>): string {
    const pairs = Object.entries(labels)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([k, v]) => `${k}=${v}`)
      .join(',');
    return `${metric}{${pairs}}`;
  }

  private async lock(key: string): Promise<void> {
    while (this.locks.has(key)) {
      await this.locks.get(key)!;
    }
    let resolve: () => void;
    const p = new Promise<void>(r => (resolve = r));
    this.locks.set(key, p);
    this.resolvers.set(key, resolve!);
  }

  private unlock(key: string): void {
    const resolve = this.resolvers.get(key);
    if (resolve) {
      this.resolvers.delete(key);
      this.locks.delete(key);
      resolve();
    }
  }

  private async sendWarnAlert(metric: string, count: number): Promise<void> {
    const text = `🚨 High cardinality: ${metric} has ${count} series (threshold ${Math.floor(this.max * this.warnRatio)})`;
    console.warn(`[CardinalityWatcher] ${text}`);
    await this.postWebhook(text);
  }

  private async sendDropAlert(metric: string, labels: Record<string, string>, count: number): Promise<void> {
    const text = `❌ Dropped metric ${metric} – cardinality ${count} exceeded hard limit ${this.max}`;
    console.warn(`[CardinalityWatcher] ${text}`);
    await this.postWebhook(text);
  }

  private async postWebhook(text: string): Promise<void> {
    if (!this.webhook) return;
    const controller = new AbortController();
    const t = setTimeout(() => controller.abort(), 5_000);
    try {
      await fetch(this.webhook, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(t);
    }
  }
}