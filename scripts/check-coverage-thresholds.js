#!/usr/bin/env node

/**
 * Coverage Threshold Checker
 * Validates that coverage meets minimum thresholds
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rootDir = path.resolve(__dirname, '..');
const coverageSummaryPath = path.join(rootDir, 'coverage', 'coverage-summary.json');

const THRESHOLDS = {
  lines: 80,
  statements: 80,
  functions: 75,
  branches: 70
};

async function checkCoverageThresholds() {
  console.log('🔍 Checking coverage thresholds...\n');
  
  if (!fs.existsSync(coverageSummaryPath)) {
    console.log('⚠️  No coverage summary found. Run tests with coverage first:');
    console.log('   npm run test:coverage\n');
    process.exit(1);
  }
  
  const coverageData = JSON.parse(fs.readFileSync(coverageSummaryPath, 'utf8'));
  
  if (!coverageData.total) {
    console.error('❌ Invalid coverage data format');
    process.exit(1);
  }
  
  const { total } = coverageData;
  const results = [];
  let allPassed = true;
  
  console.log('Coverage Thresholds Check');
  console.log('='.repeat(60));
  console.log(`${'Metric'.padEnd(15)} ${'Current'.padEnd(10)} ${'Threshold'.padEnd(10)} ${'Status'}`);
  console.log('='.repeat(60));
  
  for (const [metric, threshold] of Object.entries(THRESHOLDS)) {
    const current = total[metric]?.pct || 0;
    const passed = current >= threshold;
    const status = passed ? '✅ PASS' : '❌ FAIL';
    
    console.log(
      `${metric.padEnd(15)} ${current.toFixed(2).padEnd(10)}% ${threshold.toFixed(2).padEnd(10)}% ${status}`
    );
    
    results.push({
      metric,
      current,
      threshold,
      passed
    });
    
    if (!passed) {
      allPassed = false;
    }
  }
  
  console.log('='.repeat(60));
  console.log();
  
  if (allPassed) {
    console.log('🎉 All coverage thresholds met!\n');
    process.exit(0);
  } else {
    console.error('❌ Coverage thresholds not met. Please improve test coverage.\n');
    
    const failed = results.filter(r => !r.passed);
    console.log('Failed metrics:');
    failed.forEach(({ metric, current, threshold }) => {
      const gap = threshold - current;
      console.log(`  • ${metric}: ${current.toFixed(2)}% (need ${gap.toFixed(2)}% more)`);
    });
    console.log();
    
    // Don't fail in CI during initial setup
    if (process.env.CI && process.env.COVERAGE_STRICT !== 'true') {
      console.log('ℹ️  Running in CI - treating as warning for now');
      console.log('   Set COVERAGE_STRICT=true to enforce thresholds\n');
      process.exit(0);
    }
    
    process.exit(1);
  }
}

checkCoverageThresholds().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
