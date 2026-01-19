'use strict';

/**
 * Performance Monitoring + Benchmark Runner
 * Node.js 14+ compatible (CommonJS), async/await, autocannon-based load testing.
 *
 * Outputs:
 * - results/<runId>/summary.json
 * - results/<runId>/raw/<benchmarkId>.json
 * - results/<runId>/human/summary.txt
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const autocannon = require('autocannon');
const Redis = require('ioredis');
const pino = require('pino');

const { program } = require('commander');

const DEFAULT_RESULTS_DIR = process.env.RESULTS_DIR || path.join(process.cwd(), 'results');
const DEFAULT_ENV = process.env.NODE_ENV || 'development';
const DEFAULT_BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const DEFAULT_REDIS_URL = process.env.REDIS_URL || '';
const DEFAULT_DURATION_SEC = toInt(process.env.BENCH_DURATION_SEC, 20);
const DEFAULT_WARMUP_SEC = toInt(process.env.BENCH_WARMUP_SEC, 3);
const DEFAULT_TIMEOUT_SEC = toInt(process.env.BENCH_TIMEOUT_SEC, 30);
const DEFAULT_CONN_REUSE = (process.env.BENCH_CONN_REUSE || 'true').toLowerCase() !== 'false';
const DEFAULT_MAX_CONCURRENCY = toInt(process.env.BENCH_MAX_CONCURRENCY, 500);
const DEFAULT_MIN_CONCURRENCY = toInt(process.env.BENCH_MIN_CONCURRENCY, 50);
const DEFAULT_CONCURRENCY_STEP = toInt(process.env.BENCH_CONCURRENCY_STEP, 50);
const DEFAULT_MAX_MEM_MB = toInt(process.env.MAX_MEM_MB, 1024);

const log = pino({
  level: process.env.LOG_LEVEL || (DEFAULT_ENV === 'production' ? 'info' : 'debug'),
  base: { service: 'lab-verse-performance-monitor' },
});

/**
 * @typedef {Object} BenchmarkTarget
 * @property {string} id - Unique benchmark id.
 * @property {string} name - Human-readable name.
 * @property {string} method - HTTP method.
 * @property {string} path - URL path (combined with baseUrl).
 * @property {Object<string,string>=} headers - Optional headers.
 * @property {any=} body - Optional JSON body.
 * @property {number[]=} concurrencyLevels - Optional explicit concurrency levels.
 * @property {number=} durationSec - Optional override duration.
 * @property {number=} timeoutSec - Optional request timeout.
 * @property {Object=} thresholds - Optional thresholds override.
 */

/**
 * @typedef {Object} MonitorConfig
 * @property {string=} baseUrl
 * @property {Object=} thresholds
 * @property {BenchmarkTarget[]} benchmarks
 * @property {Object=} optimizationTechniques
 */

program
  .name('monitor')
  .description('Performance monitoring + benchmarking runner')
  .option('-c, --config <path>', 'Path to config.js', path.join(__dirname, 'config.js'))
  .option('-o, --out <dir>', 'Results output directory', DEFAULT_RESULTS_DIR)
  .option('-b, --base-url <url>', 'Base URL to benchmark', DEFAULT_BASE_URL)
  .option('--redis <url>', 'Redis URL (optional)', DEFAULT_REDIS_URL)
  .option('--duration <sec>', 'Default duration per benchmark (seconds)', String(DEFAULT_DURATION_SEC))
  .option('--warmup <sec>', 'Warmup duration (seconds)', String(DEFAULT_WARMUP_SEC))
  .option('--timeout <sec>', 'Request timeout (seconds)', String(DEFAULT_TIMEOUT_SEC))
  .option('--min-concurrency <n>', 'Minimum concurrency', String(DEFAULT_MIN_CONCURRENCY))
  .option('--max-concurrency <n>', 'Maximum concurrency', String(DEFAULT_MAX_CONCURRENCY))
  .option('--step <n>', 'Concurrency step', String(DEFAULT_CONCURRENCY_STEP))
  .option('--conn-reuse <bool>', 'Connection reuse (keep-alive) true/false', String(DEFAULT_CONN_REUSE))
  .parse(process.argv);

main().catch((err) => {
  log.error({ err }, 'Fatal error');
  process.exitCode = 1;
});

/**
 * Main entrypoint.
 * @returns {Promise<void>}
 */
async function main() {
  const opts = program.opts();

  enforceMemoryLimit(DEFAULT_MAX_MEM_MB);

  const cfg = loadConfig(opts.config);
  validateConfig(cfg);

  const baseUrl = opts.baseUrl || cfg.baseUrl || DEFAULT_BASE_URL;
  const resultsDir = path.resolve(opts.out || DEFAULT_RESULTS_DIR);

  const runId = createRunId();
  const runDir = path.join(resultsDir, runId);
  const rawDir = path.join(runDir, 'raw');
  const humanDir = path.join(runDir, 'human');

  await ensureDir(rawDir);
  await ensureDir(humanDir);

  const redis = createRedisClient(opts.redis);
  const ctx = {
    opts,
    cfg,
    baseUrl,
    runId,
    runDir,
    rawDir,
    humanDir,
    redis,
  };

  log.info({ runId, baseUrl, out: runDir }, 'Starting benchmark run');

  const summary = await runAllBenchmarks(ctx);

  await writeJson(path.join(runDir, 'summary.json'), summary);
  await writeHumanSummary(path.join(humanDir, 'summary.txt'), summary);

  await safeQuitRedis(redis);

  log.info({ runId, out: runDir }, 'Benchmark run completed');
}

/**
 * Runs all benchmarks and writes per-benchmark raw outputs.
 *
 * @param {Object} ctx
 * @param {any} ctx.opts
 * @param {MonitorConfig} ctx.cfg
 * @param {string} ctx.baseUrl
 * @param {string} ctx.runId
 * @param {string} ctx.runDir
 * @param {string} ctx.rawDir
 * @param {string} ctx.humanDir
 * @param {import('ioredis') | null} ctx.redis
 * @returns {Promise<Object>} Summary object.
 */
async function runAllBenchmarks(ctx) {
  const startedAt = new Date().toISOString();

  const defaults = {
    durationSec: toInt(ctx.opts.duration, DEFAULT_DURATION_SEC),
    warmupSec: toInt(ctx.opts.warmup, DEFAULT_WARMUP_SEC),
    timeoutSec: toInt(ctx.opts.timeout, DEFAULT_TIMEOUT_SEC),
    connReuse: String(ctx.opts.connReuse).toLowerCase() !== 'false',
    minConcurrency: toInt(ctx.opts.minConcurrency, DEFAULT_MIN_CONCURRENCY),
    maxConcurrency: toInt(ctx.opts.maxConcurrency, DEFAULT_MAX_CONCURRENCY),
    step: toInt(ctx.opts.step, DEFAULT_CONCURRENCY_STEP),
  };

  const globalThresholds = normalizeThresholds(ctx.cfg.thresholds || {});
  const results = [];
  const failures = [];

  for (const bench of ctx.cfg.benchmarks) {
    const concurrencyLevels = Array.isArray(bench.concurrencyLevels) && bench.concurrencyLevels.length
      ? bench.concurrencyLevels
      : buildConcurrencyLevels(defaults.minConcurrency, defaults.maxConcurrency, defaults.step);

    for (const concurrency of concurrencyLevels) {
      const benchId = `${bench.id}-c${concurrency}`;
      const rawPath = path.join(ctx.rawDir, `${benchId}.json`);

      const warmupSec = defaults.warmupSec;
      const durationSec = bench.durationSec != null ? bench.durationSec : defaults.durationSec;
      const timeoutSec = bench.timeoutSec != null ? bench.timeoutSec : defaults.timeoutSec;

      log.info({ benchId, name: bench.name, concurrency, durationSec }, 'Running benchmark');

      try {
        if (warmupSec > 0) {
          await runWarmup(ctx, bench, concurrency, warmupSec, timeoutSec, defaults.connReuse);
        }

        const raw = await startBench(ctx, bench, concurrency, durationSec, timeoutSec, defaults.connReuse);
        await writeJson(rawPath, raw);

        const computed = computeMetrics(raw);
        const thresholds = mergeThresholds(globalThresholds, normalizeThresholds(bench.thresholds || {}));
        const passFail = evaluateThresholds(computed, thresholds);

        const record = {
          runId: ctx.runId,
          env: DEFAULT_ENV,
          baseUrl: ctx.baseUrl,
          benchId,
          benchmark: { id: bench.id, name: bench.name, method: bench.method, path: bench.path },
          concurrency,
          durationSec,
          metrics: computed,
          thresholds,
          pass: passFail.pass,
          violations: passFail.violations,
          rawFile: path.relative(ctx.runDir, rawPath),
          createdAt: new Date().toISOString(),
        };

        results.push(record);

        if (!record.pass) failures.push(record);

        await safeRedisStore(ctx.redis, `bench:${ctx.runId}:${benchId}`, record);

        log.info(
          {
            benchId,
            pass: record.pass,
            rps: round(record.metrics.rps, 1),
            p95: round(record.metrics.latencyMs.p95, 1),
            errRate: round(record.metrics.errorRate * 100, 3),
          },
          'Benchmark completed'
        );
      } catch (err) {
        const errorRecord = {
          runId: ctx.runId,
          env: DEFAULT_ENV,
          baseUrl: ctx.baseUrl,
          benchId,
          benchmark: { id: bench.id, name: bench.name, method: bench.method, path: bench.path },
          concurrency,
          durationSec,
          error: serializeError(err),
          createdAt: new Date().toISOString(),
        };

        failures.push(errorRecord);
        results.push({ ...errorRecord, pass: false, metrics: null, thresholds: null, violations: ['runner_error'] });

        log.error({ benchId, err }, 'Benchmark failed');
        await writeJson(rawPath.replace(/\.json$/, '.error.json'), errorRecord);
        await safeRedisStore(ctx.redis, `bench:${ctx.runId}:${benchId}:error`, errorRecord);
      }
    }
  }

  const endedAt = new Date().toISOString();

  return {
    runId: ctx.runId,
    env: DEFAULT_ENV,
    baseUrl: ctx.baseUrl,
    startedAt,
    endedAt,
    host: {
      hostname: os.hostname(),
      platform: process.platform,
      release: os.release(),
      cpus: os.cpus().length,
      node: process.version,
    },
    defaults: {
      durationSec: defaults.durationSec,
      warmupSec: defaults.warmupSec,
      timeoutSec: defaults.timeoutSec,
      connReuse: defaults.connReuse,
    },
    totals: {
      benchmarks: ctx.cfg.benchmarks.length,
      scenarios: results.length,
      failed: failures.length,
      passed: results.length - failures.length,
    },
    results,
    failures,
  };
}

async function runWarmup(ctx, bench, concurrency, warmupSec, timeoutSec, connReuse) {
  log.debug({ id: bench.id, concurrency, warmupSec }, 'Warmup start');
  try {
    await startBench(ctx, bench, concurrency, warmupSec, timeoutSec, connReuse, { warmup: true });
  } catch (err) {
    log.warn({ err, id: bench.id }, 'Warmup failed (continuing)');
  }
}

function startBench(ctx, bench, concurrency, durationSec, timeoutSec, connReuse, flags = {}) {
  const url = new URL(bench.path, ctx.baseUrl).toString();

  const headers = Object.assign(
    { 'content-type': 'application/json' },
    bench.headers || {},
    envAuthHeaders()
  );

  const method = (bench.method || 'GET').toUpperCase();

  const body = bench.body != null ? JSON.stringify(bench.body) : undefined;

  return new Promise((resolve, reject) => {
    const instance = autocannon(
      {
        url,
        method,
        headers,
        body,
        connections: concurrency,
        duration: durationSec,
        timeout: timeoutSec,
        pipelining: 1,
        maxConnectionRequests: connReuse ? undefined : 1,
        overallRate: 0
      },
      (err, result) => {
        if (err) return reject(err);

        resolve({
          meta: {
            warmup: Boolean(flags.warmup),
            benchId: bench.id,
            name: bench.name,
            url,
            method,
            concurrency,
            durationSec,
            createdAt: new Date().toISOString(),
          },
          result,
        });
      }
    );

    instance.on('error', reject);
  });
}

function computeMetrics(raw) {
  const r = raw && raw.result ? raw.result : {};
  const latency = r.latency || {};
  const errors = (r.errors || 0) + (r.timeouts || 0) + (r['non2xx'] || 0);

  const requests = (r.requests && r.requests.total) ? r.requests.total : 0;
  const rps = (r.requests && r.requests.average) ? r.requests.average : 0;

  const errorRate = requests > 0 ? errors / requests : 0;

  return {
    rps,
    requestsTotal: requests,
    errorsTotal: errors,
    errorRate,
    latencyMs: {
      min: toNum(latency.min),
      mean: toNum(latency.average),
      p50: toNum(latency.p50),
      p75: toNum(latency.p75),
      p90: toNum(latency.p90),
      p95: toNum(latency.p95),
      p99: toNum(latency.p99),
      max: toNum(latency.max),
      stdev: toNum(latency.stddev),
    },
    throughputBytesSec: r.throughput && r.throughput.average ? r.throughput.average : 0,
  };
}

function normalizeThresholds(t) {
  return {
    p95Ms: toNum(t.p95Ms, null),
    p99Ms: toNum(t.p99Ms, null),
    minRps: toNum(t.minRps, null),
    maxErrorRate: toNum(t.maxErrorRate, null),
  };
}

function mergeThresholds(base, override) {
  return {
    p95Ms: override.p95Ms != null ? override.p95Ms : base.p95Ms,
    p99Ms: override.p99Ms != null ? override.p99Ms : base.p99Ms,
    minRps: override.minRps != null ? override.minRps : base.minRps,
    maxErrorRate: override.maxErrorRate != null ? override.maxErrorRate : base.maxErrorRate,
  };
}

function evaluateThresholds(metrics, thresholds) {
  const violations = [];

  if (thresholds.p95Ms != null && metrics.latencyMs.p95 > thresholds.p95Ms) {
    violations.push(`p95_ms>${thresholds.p95Ms}`);
  }
  if (thresholds.p99Ms != null && metrics.latencyMs.p99 > thresholds.p99Ms) {
    violations.push(`p99_ms>${thresholds.p99Ms}`);
  }
  if (thresholds.minRps != null && metrics.rps < thresholds.minRps) {
    violations.push(`rps<${thresholds.minRps}`);
  }
  if (thresholds.maxErrorRate != null && metrics.errorRate > thresholds.maxErrorRate) {
    violations.push(`error_rate>${thresholds.maxErrorRate}`);
  }

  return { pass: violations.length === 0, violations };
}

function loadConfig(configPath) {
  const p = path.resolve(configPath);
  // eslint-disable-next-line import/no-dynamic-require, global-require
  const cfg = require(p);
  return cfg && cfg.default ? cfg.default : cfg;
}

function validateConfig(cfg) {
  if (!cfg || typeof cfg !== 'object') throw new Error('config must export an object');
  if (!Array.isArray(cfg.benchmarks) || cfg.benchmarks.length === 0) {
    throw new Error('config.benchmarks must be a non-empty array');
  }
  for (const b of cfg.benchmarks) {
    if (!b.id || !b.name || !b.path) throw new Error(`benchmark missing id/name/path: ${JSON.stringify(b)}`);
    if (!b.method) throw new Error(`benchmark missing method: ${b.id}`);
  }
}

async function ensureDir(dir) {
  await fsp.mkdir(dir, { recursive: true });
}

async function writeJson(filePath, data) {
  const tmp = `${filePath}.tmp`;
  await fsp.writeFile(tmp, JSON.stringify(data, null, 2), 'utf8');
  await fsp.rename(tmp, filePath);
}

async function writeHumanSummary(outPath, summary) {
  const lines = [];
  lines.push(`Run: ${summary.runId}`);
  lines.push(`Env: ${summary.env}`);
  lines.push(`Base URL: ${summary.baseUrl}`);
  lines.push(`Started: ${summary.startedAt}`);
  lines.push(`Ended: ${summary.endedAt}`);
  lines.push(`Scenarios: ${summary.totals.scenarios} | Passed: ${summary.totals.passed} | Failed: ${summary.totals.failed}`);
  lines.push('');

  for (const r of summary.results) {
    if (!r.metrics) {
      lines.push(`[FAIL] ${r.benchId} - runner error`);
      continue;
    }
    const status = r.pass ? 'PASS' : 'FAIL';
    lines.push(
      `[${status}] ${r.benchId} | rps=${round(r.metrics.rps, 1)} | p95=${round(r.metrics.latencyMs.p95, 1)}ms | err=${round(
        r.metrics.errorRate * 100,
        3
      )}%` + (r.pass ? '' : ` | violations=${r.violations.join(',')}`)
    );
  }

  await fsp.writeFile(outPath, lines.join('\n') + '\n', 'utf8');
}

function createRunId() {
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  const rand = crypto.randomBytes(4).toString('hex');
  return `run-${ts}-${rand}`;
}

function buildConcurrencyLevels(min, max, step) {
  const levels = [];
  for (let c = min; c <= max; c += step) levels.push(c);
  return levels;
}

function createRedisClient(redisUrl) {
  if (!redisUrl) {
    log.info('Redis disabled (no REDIS_URL provided)');
    return null;
  }

  const client = new Redis(redisUrl, {
    lazyConnect: true,
    enableReadyCheck: true,
    maxRetriesPerRequest: 1,
    retryStrategy: (times) => Math.min(times * 250, 2000),
    reconnectOnError: () => true,
  });

  client.on('error', (err) => log.warn({ err }, 'Redis error'));
  client.on('close', () => log.warn('Redis connection closed'));
  client.on('reconnecting', () => log.info('Redis reconnecting'));

  client.connect().catch((err) => log.warn({ err }, 'Redis connect failed (continuing without Redis)'));

  return client;
}

async function safeRedisStore(redis, key, value) {
  if (!redis) return;
  try {
    await redis.set(key, JSON.stringify(value), 'EX', 60 * 60 * 24 * 7);
  } catch (err) {
    log.warn({ err, key }, 'Redis set failed');
  }
}

async function safeQuitRedis(redis) {
  if (!redis) return;
  try {
    await redis.quit();
  } catch (err) {
    log.warn({ err }, 'Redis quit failed');
  }
}

function envAuthHeaders() {
  const token = process.env.AUTH_BEARER_TOKEN;
  if (!token) return {};
  return { authorization: `Bearer ${token}` };
}

function enforceMemoryLimit(maxMb) {
  if (!maxMb) return;
  setInterval(() => {
    const rssMb = process.memoryUsage().rss / (1024 * 1024);
    if (rssMb > maxMb) {
      log.error({ rssMb, maxMb }, 'Memory limit exceeded');
      process.exit(2);
    }
  }, 2000).unref();
}

function serializeError(err) {
  return {
    name: err && err.name ? err.name : 'Error',
    message: err && err.message ? err.message : String(err),
    stack: err && err.stack ? err.stack : undefined,
  };
}

function toInt(v, fallback) {
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : fallback;
}
function toNum(v, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}
function round(n, d) {
  const p = Math.pow(10, d);
  return Math.round(n * p) / p;
}
