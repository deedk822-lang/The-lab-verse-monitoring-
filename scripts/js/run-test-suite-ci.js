#!/usr/bin/env node

/**
 * CI Test Suite Orchestrator
 * 
 * Runs Jest (JavaScript/TypeScript) and pytest (Python) tests with:
 * - Professional error handling
 * - Graceful degradation for missing dependencies
 * - CI-friendly exit codes and logging
 * - Clear failure reporting
 */

import { spawn } from 'child_process';
import { createInterface } from 'readline';

/**
 * Execute a command with proper error handling
 */
function runCommand(command, args, opts = {}) {
  return new Promise((resolve) => {
    console.log(`\n[runner] Executing: ${command} ${args.join(' ')}`);
    
    const child = spawn(command, args, {
      stdio: ['inherit', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
      env: { ...process.env, FORCE_COLOR: '1' },
      ...opts
    });

    let stdout = '';
    let stderr = '';

    // Stream stdout
    if (child.stdout) {
      const rl = createInterface({ input: child.stdout });
      rl.on('line', (line) => {
        console.log(line);
        stdout += line + '\n';
      });
    }

    // Stream stderr
    if (child.stderr) {
      const rl = createInterface({ input: child.stderr });
      rl.on('line', (line) => {
        console.error(line);
        stderr += line + '\n';
      });
    }

    child.on('error', (err) => {
      console.error(`[runner] Failed to start "${command}":`, err.message);
      resolve({ 
        code: null, 
        error: err,
        stdout,
        stderr
      });
    });

    child.on('close', (code) => {
      resolve({ 
        code, 
        error: null,
        stdout,
        stderr
      });
    });
  });
}

/**
 * Run Jest test suite
 */
async function runJest() {
  console.log('\n' + '='.repeat(70));
  console.log('🧪 JavaScript/TypeScript Test Suite (Jest)');
  console.log('='.repeat(70));

  const { code, error, stdout } = await runCommand('npx', [
    'jest',
    '--runInBand',
    '--passWithNoTests',
    '--colors'
  ]);

  if (error) {
    if (error.code === 'ENOENT') {
      console.error('\n[runner] ❌ Jest not found. Run: npm install');
      return { ok: false, reason: 'jest-not-found', details: error.message };
    }
    console.error('\n[runner] ❌ Jest failed to start.');
    return { ok: false, reason: 'jest-startup-failure', details: error.message };
  }

  if (code !== 0) {
    console.error(`\n[runner] ❌ Jest tests failed with exit code ${code}`);
    
    // Parse Jest output for specific failure details
    const failedTests = stdout.match(/FAIL\s+(.+)/g) || [];
    if (failedTests.length > 0) {
      console.error('\n[runner] Failed test files:');
      failedTests.slice(0, 5).forEach(f => console.error('  ' + f));
      if (failedTests.length > 5) {
        console.error(`  ... and ${failedTests.length - 5} more`);
      }
    }
    
    return { ok: false, reason: 'jest-tests-failed', details: `${failedTests.length} test file(s) failed` };
  }

  console.log('\n[runner] ✅ Jest tests completed successfully');
  return { ok: true };
}

/**
 * Run pytest test suite
 */
async function runPytest() {
  console.log('\n' + '='.repeat(70));
  console.log('🐍 Python Test Suite (pytest)');
  console.log('='.repeat(70));

  const { code, error, stdout } = await runCommand('pytest', [
    '-v',
    '--color=yes',
    '--tb=short'
  ]);

  // If pytest is not installed or not found, treat as a soft skip
  if (error) {
    if (error.code === 'ENOENT') {
      console.warn('\n[runner] ⚠️  pytest not found; skipping Python tests');
      console.warn('[runner] Install pytest with: pip install pytest');
      return { ok: true, skipped: true, reason: 'pytest-missing' };
    }
    console.error('\n[runner] ❌ pytest failed to start:', error.message);
    return { ok: false, reason: 'pytest-startup-failure', details: error.message };
  }

  // pytest exit codes:
  // 0 = all tests passed
  // 1 = tests were collected and run but some failed
  // 2 = test execution was interrupted
  // 3 = internal error
  // 4 = command line usage error
  // 5 = no tests collected
  
  if (code === 5) {
    console.warn('\n[runner] ⚠️  No Python tests collected; treating as success');
    return { ok: true, skipped: true, reason: 'no-python-tests' };
  }

  if (code !== 0) {
    console.error(`\n[runner] ❌ pytest failed with exit code ${code}`);
    
    // Parse pytest output for specific failure details
    const failedTests = stdout.match(/FAILED\s+(.+)\s+-/g) || [];
    if (failedTests.length > 0) {
      console.error('\n[runner] Failed tests:');
      failedTests.slice(0, 5).forEach(f => console.error('  ' + f));
      if (failedTests.length > 5) {
        console.error(`  ... and ${failedTests.length - 5} more`);
      }
    }
    
    return { ok: false, reason: 'pytest-tests-failed', details: `${failedTests.length || 'Some'} test(s) failed` };
  }

  console.log('\n[runner] ✅ Python tests completed successfully');
  return { ok: true };
}

/**
 * Print summary report
 */
function printSummary(results) {
  console.log('\n' + '='.repeat(70));
  console.log('📊 TEST SUITE SUMMARY');
  console.log('='.repeat(70));
  
  let allPassed = true;
  let hasSkipped = false;
  
  for (const [suite, result] of Object.entries(results)) {
    const icon = result.ok ? '✅' : '❌';
    const status = result.ok ? 'PASSED' : 'FAILED';
    const skipped = result.skipped ? ' (skipped)' : '';
    
    console.log(`${icon} ${suite.toUpperCase()}: ${status}${skipped}`);
    
    if (result.details) {
      console.log(`   Details: ${result.details}`);
    }
    if (result.reason) {
      console.log(`   Reason: ${result.reason}`);
    }
    
    if (!result.ok) allPassed = false;
    if (result.skipped) hasSkipped = true;
  }
  
  console.log('='.repeat(70));
  
  if (allPassed) {
    console.log('\n🎉 All test suites completed successfully!');
    if (hasSkipped) {
      console.log('\n💡 Some test suites were skipped due to missing dependencies.');
      console.log('   This is normal for CI environments without Python or specific tools.');
    }
  } else {
    console.log('\n❌ Some test suites failed. See details above.');
  }
  
  console.log('');
}

/**
 * Main test orchestrator
 */
async function main() {
  console.log('\n🚀 Starting CI Test Suite Orchestrator');
  console.log(`📅 ${new Date().toISOString()}`);
  console.log(`🖥️  Node ${process.version}`);
  console.log(`📂 ${process.cwd()}`);
  
  const startTime = Date.now();
  
  // Run all test suites
  const results = {
    jest: await runJest(),
    pytest: await runPytest()
  };
  
  const duration = ((Date.now() - startTime) / 1000).toFixed(2);
  
  // Print summary
  printSummary(results);
  
  console.log(`⏱️  Total time: ${duration}s\n`);
  
  // Exit with appropriate code
  const failures = Object.entries(results).filter(([, r]) => !r.ok);
  
  if (failures.length > 0) {
    console.error('\n💔 CI tests failed. Fix the issues above and try again.');
    process.exit(1);
  }
  
  console.log('\n💚 CI tests passed! Ready to merge.');
  process.exit(0);
}

// Handle uncaught errors
process.on('unhandledRejection', (err) => {
  console.error('\n[runner] ❌ Unhandled error:', err);
  process.exit(1);
});

// Execute
main().catch((err) => {
  console.error('\n[runner] ❌ Fatal error:', err);
  process.exit(1);
});
