'use strict';

/**
 * Analyze benchmark runs and generate:
 * - results/<runId>/report.json
 * - results/<runId>/report.txt
 */

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const pino = require('pino');
const { program } = require('commander');

const log = pino({ level: process.env.LOG_LEVEL || 'info', base: { service: 'bench-analyze' } });

program
  .option('-r, --results <dir>', 'Results directory', path.join(process.cwd(), 'results'))
  .option('--run <runId>', 'Run id to analyze (defaults to latest)')
  .parse(process.argv);

main().catch((err) => {
  log.error({ err }, 'Analyze failed');
  process.exitCode = 1;
});

async function main() {
  const opts = program.opts();
  const resultsDir = path.resolve(opts.results);

  const runId = opts.run || (await findLatestRunId(resultsDir));
  if (!runId) throw new Error(`No runs found in ${resultsDir}`);

  const runDir = path.join(resultsDir, runId);
  const summaryPath = path.join(runDir, 'summary.json');
  const summary = await readJson(summaryPath);

  const report = buildReport(summary);

  const latestTwo = await findLatestTwoRunIds(resultsDir);
  if (latestTwo.length === 2) {
    const [prevId, curId] = latestTwo;
    if (curId === runId) {
      const prev = await readJson(path.join(resultsDir, prevId, 'summary.json'));
      report.comparison = compareRuns(prev, summary);
    }
  }

  await writeJson(path.join(runDir, 'report.json'), report);
  await fsp.writeFile(path.join(runDir, 'report.txt'), renderHumanReport(report), 'utf8');

  log.info({ runId, out: runDir }, 'Report generated');
}

function buildReport(summary) {
  const byBenchmark = {};

  for (const r of summary.results) {
    const key = r.benchmark ? r.benchmark.id : r.benchId;
    if (!byBenchmark[key]) {
      byBenchmark[key] = {
        id: r.benchmark ? r.benchmark.id : key,
        name: r.benchmark ? r.benchmark.name : key,
        scenarios: [],
      };
    }
    byBenchmark[key].scenarios.push(r);
  }

  const scenarioFlat = summary.results.filter((x) => x.metrics);

  const bestP95 = [...scenarioFlat].sort((a, b) => a.metrics.latencyMs.p95 - b.metrics.latencyMs.p95)[0] || null;
  const bestRps = [...scenarioFlat].sort((a, b) => b.metrics.rps - a.metrics.rps)[0] || null;

  const worstP95 = [...scenarioFlat].sort((a, b) => b.metrics.latencyMs.p95 - a.metrics.latencyMs.p95)[0] || null;
  const worstErr = [...scenarioFlat].sort((a, b) => b.metrics.errorRate - a.metrics.errorRate)[0] || null;

  return {
    runId: summary.runId,
    env: summary.env,
    baseUrl: summary.baseUrl,
    startedAt: summary.startedAt,
    endedAt: summary.endedAt,
    totals: summary.totals,
    highlights: {
      bestP95: pickHighlight(bestP95),
      bestRps: pickHighlight(bestRps),
      worstP95: pickHighlight(worstP95),
      worstErrorRate: pickHighlight(worstErr),
    },
    benchmarks: Object.values(byBenchmark),
    comparison: null,
  };
}

function compareRuns(prev, cur) {
  const prevMap = new Map(prev.results.map((r) => [r.benchId, r]));
  const deltas = [];

  for (const r of cur.results) {
    const p = prevMap.get(r.benchId);
    if (!p || !r.metrics || !p.metrics) continue;

    deltas.push({
      benchId: r.benchId,
      benchmark: r.benchmark,
      concurrency: r.concurrency,
      delta: {
        rpsPct: pctChange(p.metrics.rps, r.metrics.rps),
        p95Pct: pctChange(p.metrics.latencyMs.p95, r.metrics.latencyMs.p95),
        errRatePct: pctChange(p.metrics.errorRate, r.metrics.errorRate),
      },
      prev: pickMetrics(p.metrics),
      cur: pickMetrics(r.metrics),
    });
  }

  return {
    prevRunId: prev.runId,
    curRunId: cur.runId,
    scenarioCountCompared: deltas.length,
    deltas,
  };
}

function pickHighlight(r) {
  if (!r || !r.metrics) return null;
  return {
    benchId: r.benchId,
    name: r.benchmark ? r.benchmark.name : r.benchId,
    concurrency: r.concurrency,
    pass: r.pass,
    metrics: pickMetrics(r.metrics),
  };
}

function pickMetrics(m) {
  return {
    rps: m.rps,
    p95Ms: m.latencyMs.p95,
    p99Ms: m.latencyMs.p99,
    errorRate: m.errorRate,
    requestsTotal: m.requestsTotal,
    errorsTotal: m.errorsTotal,
  };
}

function renderHumanReport(report) {
  const lines = [];
  lines.push(`Run: ${report.runId}`);
  lines.push(`Env: ${report.env}`);
  lines.push(`Base URL: ${report.baseUrl}`);
  lines.push(`Scenarios: ${report.totals.scenarios} | Passed: ${report.totals.passed} | Failed: ${report.totals.failed}`);
  lines.push('');

  lines.push('Highlights:');
  lines.push(`- Best p95: ${fmtHighlight(report.highlights.bestP95)}`);
  lines.push(`- Best rps: ${fmtHighlight(report.highlights.bestRps)}`);
  lines.push(`- Worst p95: ${fmtHighlight(report.highlights.worstP95)}`);
  lines.push(`- Worst error: ${fmtHighlight(report.highlights.worstErrorRate)}`);
  lines.push('');

  if (report.comparison) {
    lines.push(`Comparison: ${report.comparison.prevRunId} -> ${report.comparison.curRunId}`);
    lines.push(`Compared scenarios: ${report.comparison.scenarioCountCompared}`);
    const topRegress = [...report.comparison.deltas]
      .sort((a, b) => (b.delta.p95Pct || 0) - (a.delta.p95Pct || 0))
      .slice(0, 5);
    lines.push('Top p95 regressions:');
    for (const d of topRegress) {
      lines.push(
        `- ${d.benchId}: p95 ${pctFmt(d.delta.p95Pct)} | rps ${pctFmt(d.delta.rpsPct)} | err ${pctFmt(d.delta.errRatePct)}`
      );
    }
    lines.push('');
  }

  return lines.join('\n') + '\n';
}

function fmtHighlight(h) {
  if (!h) return 'n/a';
  return `${h.benchId} (c=${h.concurrency}) p95=${round(h.metrics.p95Ms, 1)}ms rps=${round(h.metrics.rps, 1)} err=${round(
    h.metrics.errorRate * 100,
    3
  )}%`;
}

function pctChange(oldV, newV) {
  if (oldV === 0) return null;
  return ((newV - oldV) / oldV) * 100;
}
function pctFmt(v) {
  if (v == null) return 'n/a';
  return `${round(v, 2)}%`;
}

async function findLatestRunId(resultsDir) {
  const runs = await listRunDirs(resultsDir);
  return runs[0] || null;
}

async function findLatestTwoRunIds(resultsDir) {
  const runs = await listRunDirs(resultsDir);
  return runs.slice(0, 2).reverse();
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
