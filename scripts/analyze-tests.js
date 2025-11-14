#!/usr/bin/env node

/**
 * Test Analysis Script
 * Analyzes test performance and generates metrics
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rootDir = path.resolve(__dirname, '..');
const testResultsDir = path.join(rootDir, 'test-results');
const coverageDir = path.join(rootDir, 'coverage');

// Ensure directories exist
if (!fs.existsSync(testResultsDir)) {
  fs.mkdirSync(testResultsDir, { recursive: true });
}

async function analyzeTests() {
  console.log('🔍 Analyzing test performance...\n');
  
  const metrics = {
    timestamp: new Date().toISOString(),
    totalTests: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
    duration: 0,
    avgTestDuration: 0,
    slowestTest: null,
    fastestTest: null,
    coverage: {
      lines: 0,
      statements: 0,
      functions: 0,
      branches: 0
    },
    thresholds: {
      lines: 80,
      statements: 80,
      functions: 75,
      branches: 70
    },
    healthScore: 100,
    efficiency: 100,
    status: 'passing'
  };
  
  try {
    // Read JUnit XML if it exists
    const junitPath = path.join(testResultsDir, 'junit.xml');
    if (fs.existsSync(junitPath)) {
      console.log('✅ Found JUnit test results');
      // Parse basic test info from JUnit XML (simplified)
      const junitContent = fs.readFileSync(junitPath, 'utf8');
      const testMatch = junitContent.match(/tests="(\d+)"/);
      const failureMatch = junitContent.match(/failures="(\d+)"/);
      const timeMatch = junitContent.match(/time="([\d.]+)"/);
      
      if (testMatch) metrics.totalTests = parseInt(testMatch[1]);
      if (failureMatch) metrics.failed = parseInt(failureMatch[1]);
      if (timeMatch) metrics.duration = parseFloat(timeMatch[1]) * 1000;
      metrics.passed = metrics.totalTests - metrics.failed;
    }
    
    // Read coverage summary if it exists
    const coverageSummaryPath = path.join(coverageDir, 'coverage-summary.json');
    if (fs.existsSync(coverageSummaryPath)) {
      console.log('✅ Found coverage summary');
      const coverageData = JSON.parse(fs.readFileSync(coverageSummaryPath, 'utf8'));
      
      if (coverageData.total) {
        metrics.coverage.lines = coverageData.total.lines?.pct || 0;
        metrics.coverage.statements = coverageData.total.statements?.pct || 0;
        metrics.coverage.functions = coverageData.total.functions?.pct || 0;
        metrics.coverage.branches = coverageData.total.branches?.pct || 0;
      }
    } else {
      console.log('⚠️  No coverage summary found - using default values');
    }
    
    // Calculate derived metrics
    if (metrics.totalTests > 0) {
      metrics.avgTestDuration = Math.round(metrics.duration / metrics.totalTests);
    }
    
    // Calculate health score (weighted average)
    const coverageScore = (
      metrics.coverage.lines * 0.3 +
      metrics.coverage.statements * 0.3 +
      metrics.coverage.functions * 0.2 +
      metrics.coverage.branches * 0.2
    );
    
    const passRate = metrics.totalTests > 0 
      ? (metrics.passed / metrics.totalTests) * 100 
      : 100;
    
    metrics.healthScore = Math.round(
      coverageScore * 0.6 + passRate * 0.4
    );
    
    // Calculate efficiency (tests per second)
    if (metrics.duration > 0) {
      metrics.efficiency = Math.round((metrics.totalTests / (metrics.duration / 1000)) * 10) / 10;
    }
    
    // Determine status
    if (metrics.failed > 0) {
      metrics.status = 'failing';
    } else if (metrics.healthScore < 70) {
      metrics.status = 'warning';
    } else {
      metrics.status = 'passing';
    }
    
    // Add slowest/fastest test placeholders
    metrics.slowestTest = {
      name: 'Integration tests',
      duration: metrics.avgTestDuration * 2
    };
    metrics.fastestTest = {
      name: 'Unit tests',
      duration: Math.round(metrics.avgTestDuration * 0.5)
    };
    
  } catch (error) {
    console.error('❌ Error analyzing tests:', error.message);
  }
  
  // Write metrics to file
  const metricsPath = path.join(rootDir, 'test-metrics.json');
  fs.writeFileSync(metricsPath, JSON.stringify(metrics, null, 2));
  
  // Print summary
  console.log('\n📊 Test Analysis Summary\n');
  console.log('='.repeat(50));
  console.log(`Status:          ${getStatusEmoji(metrics.status)} ${metrics.status.toUpperCase()}`);
  console.log(`Health Score:    ${metrics.healthScore}/100`);
  console.log(`Total Tests:     ${metrics.totalTests}`);
  console.log(`Passed:          ${metrics.passed}`);
  console.log(`Failed:          ${metrics.failed}`);
  console.log(`Duration:        ${metrics.duration}ms`);
  console.log(`Avg/Test:        ${metrics.avgTestDuration}ms`);
  console.log(`Efficiency:      ${metrics.efficiency} tests/sec`);
  console.log('='.repeat(50));
  console.log('\n📈 Coverage Metrics\n');
  console.log('='.repeat(50));
  console.log(`Lines:           ${metrics.coverage.lines}% ${getCoverageStatus(metrics.coverage.lines, metrics.thresholds.lines)}`);
  console.log(`Statements:      ${metrics.coverage.statements}% ${getCoverageStatus(metrics.coverage.statements, metrics.thresholds.statements)}`);
  console.log(`Functions:       ${metrics.coverage.functions}% ${getCoverageStatus(metrics.coverage.functions, metrics.thresholds.functions)}`);
  console.log(`Branches:        ${metrics.coverage.branches}% ${getCoverageStatus(metrics.coverage.branches, metrics.thresholds.branches)}`);
  console.log('='.repeat(50));
  
  console.log(`\n✅ Metrics saved to: ${metricsPath}\n`);
  
  return metrics;
}

function getStatusEmoji(status) {
  switch (status) {
    case 'passing': return '🟢';
    case 'warning': return '🟡';
    case 'failing': return '🔴';
    default: return '⚪';
  }
}

function getCoverageStatus(current, threshold) {
  return current >= threshold ? '✅' : '❌';
}

// Run analysis
analyzeTests().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
