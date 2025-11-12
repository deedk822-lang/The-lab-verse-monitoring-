#!/usr/bin/env node

/**
 * Test Report Generator
 * Creates a comprehensive test report from Jest output
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rootDir = path.resolve(__dirname, '..');

async function generateTestReport() {
  console.log('📝 Generating test report...\n');
  
  const report = {
    generatedAt: new Date().toISOString(),
    summary: {
      totalTests: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      duration: 0
    },
    coverage: null,
    environment: {
      node: process.version,
      platform: process.platform,
      ci: process.env.CI === 'true'
    }
  };
  
  try {
    // Read coverage summary if available
    const coveragePath = path.join(rootDir, 'coverage', 'coverage-summary.json');
    if (fs.existsSync(coveragePath)) {
      const coverageData = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
      report.coverage = coverageData.total;
      console.log('✅ Coverage data included');
    }
    
    // Read JUnit results if available
    const junitPath = path.join(rootDir, 'test-results', 'junit.xml');
    if (fs.existsSync(junitPath)) {
      const junitContent = fs.readFileSync(junitPath, 'utf8');
      
      // Parse test counts from JUnit XML
      const testMatch = junitContent.match(/tests="(\d+)"/);
      const failureMatch = junitContent.match(/failures="(\d+)"/);
      const skippedMatch = junitContent.match(/skipped="(\d+)"/);
      const timeMatch = junitContent.match(/time="([\d.]+)"/);
      
      if (testMatch) report.summary.totalTests = parseInt(testMatch[1]);
      if (failureMatch) report.summary.failed = parseInt(failureMatch[1]);
      if (skippedMatch) report.summary.skipped = parseInt(skippedMatch[1]);
      if (timeMatch) report.summary.duration = parseFloat(timeMatch[1]);
      
      report.summary.passed = report.summary.totalTests - report.summary.failed - report.summary.skipped;
      
      console.log('✅ Test results included');
    }
    
    // Calculate health metrics
    report.health = calculateHealth(report);
    
    // Write report
    const reportPath = path.join(rootDir, 'test-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    console.log(`✅ Report generated: ${reportPath}\n`);
    
    // Print summary
    printSummary(report);
    
  } catch (error) {
    console.error('❌ Error generating report:', error.message);
    process.exit(1);
  }
}

function calculateHealth(report) {
  let score = 100;
  const issues = [];
  
  // Check test pass rate
  if (report.summary.totalTests > 0) {
    const passRate = (report.summary.passed / report.summary.totalTests) * 100;
    if (passRate < 100) {
      score -= (100 - passRate) * 0.5;
      issues.push(`Test pass rate: ${passRate.toFixed(1)}%`);
    }
  }
  
  // Check coverage
  if (report.coverage) {
    const avgCoverage = (
      report.coverage.lines.pct +
      report.coverage.statements.pct +
      report.coverage.functions.pct +
      report.coverage.branches.pct
    ) / 4;
    
    if (avgCoverage < 80) {
      score -= (80 - avgCoverage) * 0.5;
      issues.push(`Coverage: ${avgCoverage.toFixed(1)}%`);
    }
  }
  
  return {
    score: Math.max(0, Math.round(score)),
    issues,
    status: score >= 90 ? 'excellent' : score >= 70 ? 'good' : score >= 50 ? 'fair' : 'poor'
  };
}

function printSummary(report) {
  console.log('='.repeat(60));
  console.log('TEST REPORT SUMMARY');
  console.log('='.repeat(60));
  console.log(`Generated:       ${new Date(report.generatedAt).toLocaleString()}`);
  console.log(`Environment:     Node ${report.environment.node} on ${report.environment.platform}`);
  console.log(`CI Mode:         ${report.environment.ci ? 'Yes' : 'No'}`);
  console.log();
  console.log('TEST RESULTS:');
  console.log(`  Total:         ${report.summary.totalTests}`);
  console.log(`  Passed:        ${report.summary.passed} ✅`);
  console.log(`  Failed:        ${report.summary.failed} ${report.summary.failed > 0 ? '❌' : ''}`);
  console.log(`  Skipped:       ${report.summary.skipped}`);
  console.log(`  Duration:      ${report.summary.duration}s`);
  
  if (report.coverage) {
    console.log();
    console.log('COVERAGE:');
    console.log(`  Lines:         ${report.coverage.lines.pct}%`);
    console.log(`  Statements:    ${report.coverage.statements.pct}%`);
    console.log(`  Functions:     ${report.coverage.functions.pct}%`);
    console.log(`  Branches:      ${report.coverage.branches.pct}%`);
  }
  
  if (report.health) {
    console.log();
    console.log('HEALTH:');
    console.log(`  Score:         ${report.health.score}/100 (${report.health.status})`);
    if (report.health.issues.length > 0) {
      console.log(`  Issues:        ${report.health.issues.join(', ')}`);
    }
  }
  
  console.log('='.repeat(60));
  console.log();
}

generateTestReport().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
