'use strict';

/**
 * Recommend optimizations from a summary.json and config.js optimizationTechniques.
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const pino = require('pino');
const { program } = require('commander');

const log = pino({ level: process.env.LOG_LEVEL || 'info', base: { service: 'bench-recommend' } });

program
  .option('-r, --results <dir>', 'Results directory', path.join(process.cwd(), 'results'))
  .option('--run <runId>', 'Run id (defaults to latest)')
  .option('-c, --config <path>', 'Config path', path.join(__dirname, 'config.js'))
  .parse(process.argv);

main().catch((err) => {
  log.error({ err }, 'Recommendations failed');
  process.exitCode = 1;
});

async function main() {
  const opts = program.opts();
  const resultsDir = path.resolve(opts.results);

  const runId = opts.run || (await findLatestRunId(resultsDir));
  if (!runId) throw new Error(`No runs found in ${resultsDir}`);

  const runDir = path.join(resultsDir, runId);

  const cfg = loadConfig(opts.config);
  const summary = await readJson(path.join(runDir, 'summary.json'));

  const rec = buildRecommendations(summary, cfg);

  await writeJson(path.join(runDir, 'recommendations.json'), rec);
  await fsp.writeFile(path.join(runDir, 'recommendations.txt'), renderHuman(rec), 'utf8');

  log.info({ runId, out: runDir }, 'Recommendations generated');
}

function buildRecommendations(summary, cfg) {
  const techniques = (cfg && cfg.optimizationTechniques) || {};

  const items = [];
  for (const r of summary.results) {
    if (!r.metrics) {
      items.push({
        severity: 'high',
        benchId: r.benchId,
        category: 'runner',
        issue: 'Benchmark execution failed',
        evidence: r.error ? r.error.message : 'Unknown error',
        suggestions: (techniques.resiliency || []).concat(['Inspect logs and dependency availability', 'Validate BASE_URL and auth']),
      });
      continue;
    }

    const thr = r.thresholds || {};
    const m = r.metrics;

    if (thr.p95Ms != null && m.latencyMs.p95 > thr.p95Ms) {
      items.push({
        severity: 'high',
        benchId: r.benchId,
        category: 'latency',
        issue: `p95 latency is ${round(m.latencyMs.p95, 1)}ms (threshold ${thr.p95Ms}ms)`,
        evidence: metricEvidence(r),
        suggestions: uniq([
          ...(techniques.node || []),
          ...(techniques.caching || []),
          ...(techniques.db || []),
          'Add request-level profiling (CPU + DB timings) and trace sampling',
          'Move long work to async jobs (queue) and return 202 + status polling if acceptable',
        ]),
      });
    }

    if (thr.minRps != null && m.rps < thr.minRps) {
      items.push({
        severity: 'high',
        benchId: r.benchId,
        category: 'throughput',
        issue: `Throughput is ${round(m.rps, 1)} rps (minimum ${thr.minRps} rps)`,
        evidence: metricEvidence(r),
        suggestions: uniq([
          ...(techniques.scaling || []),
          ...(techniques.node || []),
          'Check upstream rate limits (Ayrshare/ElevenLabs) and implement local queue + backpressure',
          'Enable HTTP keep-alive and tune server timeouts',
        ]),
      });
    }

    if (thr.maxErrorRate != null && m.errorRate > thr.maxErrorRate) {
      items.push({
        severity: 'critical',
        benchId: r.benchId,
        category: 'errors',
        issue: `Error rate is ${round(m.errorRate * 100, 3)}% (max ${thr.maxErrorRate * 100}%)`,
        evidence: metricEvidence(r),
        suggestions: uniq([
          ...(techniques.resiliency || []),
          'Add structured error logging + correlation ids',
          'Validate external provider credentials and timeouts',
          'Implement bulkheads: separate worker pools for slow endpoints',
        ]),
      });
    }

    if (thr.p95Ms != null && m.latencyMs.p95 > thr.p95Ms * 0.9 && m.latencyMs.p95 <= thr.p95Ms) {
      items.push({
        severity: 'medium',
        benchId: r.benchId,
        category: 'latency',
        issue: 'Latency is close to threshold (warning)',
        evidence: metricEvidence(r),
        suggestions: uniq([...(techniques.caching || []), 'Add lightweight caching for repeated prompts/requests']),
      });
    }
  }

  items.sort((a, b) => severityRank(b.severity) - severityRank(a.severity));

  return {
    runId: summary.runId,
    env: summary.env,
    baseUrl: summary.baseUrl,
    createdAt: new Date().toISOString(),
    totalFindings: items.length,
    findings: items,
  };
}

function metricEvidence(r) {
  return {
    concurrency: r.concurrency,
    rps: r.metrics.rps,
    p95Ms: r.metrics.latencyMs.p95,
    p99Ms: r.metrics.latencyMs.p99,
    errorRate: r.metrics.errorRate,
    violations: r.violations,
  };
}

function renderHuman(rec) {
  const lines = [];
  lines.push(`Run: ${rec.runId}`);
  lines.push(`Env: ${rec.env}`);
  lines.push(`Base URL: ${rec.baseUrl}`);
  lines.push(`Findings: ${rec.totalFindings}`);
  lines.push('');

  for (const f of rec.findings) {
    lines.push(`[${f.severity.toUpperCase()}] ${f.benchId} | ${f.category}`);
    lines.push(`Issue: ${f.issue}`);
    lines.push(`Evidence: ${JSON.stringify(f.evidence)}`);
    lines.push('Suggestions:');
    for (const s of f.suggestions) lines.push(`- ${s}`);
    lines.push('');
  }
  return lines.join('\n') + '\n';
}

function severityRank(s) {
  switch (s) {
    case 'critical': return 3;
    case 'high': return 2;
    case 'medium': return 1;
    default: return 0;
  }
}

function uniq(arr) {
  return [...new Set(arr.filter(Boolean))];
}

function loadConfig(configPath) {
  const p = path.resolve(configPath);
  // eslint-disable-next-line import/no-dynamic-require, global-require
  const cfg = require(p);
  return cfg && cfg.default ? cfg.default : cfg;
}

async function findLatestRunId(resultsDir) {
  const dirs = await listRunDirs(resultsDir);
  return dirs[0] || null;
}

async function listRunDirs(resultsDir) {
  let entries = [];
  try {
    entries = await fsp.readdir(resultsDir, { withFileTypes: true });
  } catch {
    return [];
  }
  const dirs = entries.filter((e) => e.isDirectory() && e.name.startsWith('run-')).map((e) => e.name);
  dirs.sort((a, b) => (a < b ? 1 : -1));
  return dirs;
}

async function readJson(p) {
  const txt = await fsp.readFile(p, 'utf8');
  return JSON.parse(txt);
}

async function writeJson(p, obj) {
  const tmp = `${p}.tmp`;
  await fsp.writeFile(tmp, JSON.stringify(obj, null, 2), 'utf8');
  await fsp.rename(tmp, p);
}

function round(n, d) {
  const p = Math.pow(10, d);
  return Math.round(n * p) / p;
}
