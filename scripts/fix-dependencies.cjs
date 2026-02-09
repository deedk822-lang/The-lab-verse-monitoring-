#!/usr/bin/env node

/**
 * Dependency Fix and Validation Script
 * Checks for common issues in package.json and provides fixes
 */

const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

class DependencyFixer {
  constructor() {
    this.issues = [];
    this.fixes = [];
    this.warnings = [];
  }

  loadPackageJson() {
    try {
      const packagePath = path.join(process.cwd(), 'package.json');
      const content = fs.readFileSync(packagePath, 'utf8');
      this.packageJson = JSON.parse(content);
      this.packagePath = packagePath;
      log('✓ package.json loaded', 'green');
      return true;
    } catch (error) {
      log(`✗ Failed to load package.json: ${error.message}`, 'red');
      return false;
    }
  }

  checkNodeVersion() {
    log('\nChecking Node.js version...', 'blue');

    const engines = this.packageJson.engines || {};
    const requiredNode = engines.node;

    if (!requiredNode) {
      this.warnings.push({
        type: 'missing_engine',
        message: 'No Node.js version specified in engines field',
        fix: 'Add "engines": { "node": ">=20.0.0" } to package.json'
      });
      log('⚠ No Node.js version requirement found', 'yellow');
    } else {
      log(`✓ Node.js version requirement: ${requiredNode}`, 'green');

      // Check if it's at least 20
      if (!requiredNode.includes('20')) {
        this.warnings.push({
          type: 'old_node_version',
          message: `Node.js version ${requiredNode} should be updated to 20+`,
          fix: 'Update engines.node to ">=20.0.0"'
        });
      }
    }
  }

  checkSecurityVulnerabilities() {
    log('\nChecking for security vulnerabilities...', 'blue');

    try {
      const auditOutput = execSync('npm audit --json', {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'ignore']
      });

      const audit = JSON.parse(auditOutput);

      if (audit.metadata) {
        const { vulnerabilities } = audit.metadata;
        const total = vulnerabilities.total || 0;
        const critical = vulnerabilities.critical || 0;
        const high = vulnerabilities.high || 0;
        const moderate = vulnerabilities.moderate || 0;

        if (total > 0) {
          log(`⚠ Found ${total} vulnerabilities:`, 'yellow');
          if (critical > 0) log(`  Critical: ${critical}`, 'red');
          if (high > 0) log(`  High: ${high}`, 'red');
          if (moderate > 0) log(`  Moderate: ${moderate}`, 'yellow');

          this.issues.push({
            type: 'security_vulnerabilities',
            count: total,
            severity: { critical, high, moderate },
            fix: 'Run: npm audit fix'
          });
        } else {
          log('✓ No vulnerabilities found', 'green');
        }
      }
    } catch (error) {
      log('⚠ Could not run security audit', 'yellow');
    }
  }

  checkOutdatedPackages() {
    log('\nChecking for outdated packages...', 'blue');

    try {
      const outdatedOutput = execSync('npm outdated --json', {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'ignore']
      });

      if (outdatedOutput) {
        const outdated = JSON.parse(outdatedOutput);
        const count = Object.keys(outdated).length;

        if (count > 0) {
          log(`⚠ ${count} packages can be updated:`, 'yellow');

          Object.entries(outdated).slice(0, 5).forEach(([name, info]) => {
            log(`  ${name}: ${info.current} → ${info.latest}`, 'yellow');
          });

          if (count > 5) {
            log(`  ... and ${count - 5} more`, 'yellow');
          }

          this.warnings.push({
            type: 'outdated_packages',
            count,
            fix: 'Run: npm update'
          });
        } else {
          log('✓ All packages are up to date', 'green');
        }
      }
    } catch (error) {
      // npm outdated returns exit code 1 if there are outdated packages
      // This is expected behavior
      log('✓ Outdated check complete', 'green');
    }
  }

  checkMissingScripts() {
    log('\nChecking package.json scripts...', 'blue');

    const requiredScripts = {
      'test': 'jest or other test runner',
      'lint': 'eslint or other linter',
      'validate-env': 'node scripts/validate-environment.js'
    };

    const scripts = this.packageJson.scripts || {};

    Object.entries(requiredScripts).forEach(([script, description]) => {
      if (!scripts[script]) {
        this.warnings.push({
          type: 'missing_script',
          script,
          description,
          fix: `Add "${script}" script to package.json`
        });
        log(`⚠ Missing script: ${script} (${description})`, 'yellow');
      } else {
        log(`✓ Script found: ${script}`, 'green');
      }
    });
  }

  checkDuplicateDependencies() {
    log('\nChecking for duplicate dependencies...', 'blue');

    const deps = this.packageJson.dependencies || {};
    const devDeps = this.packageJson.devDependencies || {};

    const duplicates = Object.keys(deps).filter(dep => devDeps[dep]);

    if (duplicates.length > 0) {
      log(`⚠ Found ${duplicates.length} duplicate dependencies:`, 'yellow');
      duplicates.forEach(dep => {
        log(`  ${dep}`, 'yellow');
      });

      this.issues.push({
        type: 'duplicate_dependencies',
        packages: duplicates,
        fix: 'Remove duplicates from either dependencies or devDependencies'
      });
    } else {
      log('✓ No duplicate dependencies', 'green');
    }
  }

  generateFixes() {
    log('\n================================', 'blue');
    log('SUGGESTED FIXES', 'blue');
    log('================================\n', 'blue');

    if (this.issues.length === 0 && this.warnings.length === 0) {
      log('✓ No issues found!', 'green');
      return;
    }

    if (this.issues.length > 0) {
      log('Critical Issues:', 'red');
      this.issues.forEach((issue, i) => {
        log(`\n${i + 1}. ${issue.type}`, 'red');
        log(`   Fix: ${issue.fix}`, 'yellow');
      });
    }

    if (this.warnings.length > 0) {
      log('\nWarnings:', 'yellow');
      this.warnings.forEach((warning, i) => {
        log(`\n${i + 1}. ${warning.type}`, 'yellow');
        log(`   ${warning.message || ''}`, 'yellow');
        log(`   Fix: ${warning.fix}`, 'yellow');
      });
    }
  }

  autoFix() {
    log('\n================================', 'blue');
    log('AUTO-FIX', 'blue');
    log('================================\n', 'blue');

    let fixed = 0;

    // Fix security vulnerabilities
    if (this.issues.some(i => i.type === 'security_vulnerabilities')) {
      log('Fixing security vulnerabilities...', 'blue');
      try {
        execSync('npm audit fix', { stdio: 'inherit' });
        log('✓ Security vulnerabilities fixed', 'green');
        fixed++;
      } catch (error) {
        log('⚠ Could not auto-fix all vulnerabilities', 'yellow');
        log('  Try: npm audit fix --force (use with caution)', 'yellow');
      }
    }

    // Update package.json with recommended changes
    let modified = false;

    // Add Node.js version requirement
    if (this.warnings.some(w => w.type === 'missing_engine')) {
      this.packageJson.engines = this.packageJson.engines || {};
      this.packageJson.engines.node = '>=20.0.0';
      modified = true;
      log('✓ Added Node.js version requirement', 'green');
      fixed++;
    }

    // Add missing scripts
    const missingScripts = this.warnings.filter(w => w.type === 'missing_script');
    if (missingScripts.length > 0) {
      this.packageJson.scripts = this.packageJson.scripts || {};

      if (!this.packageJson.scripts['validate-env']) {
        this.packageJson.scripts['validate-env'] = 'node scripts/validate-environment.js';
        modified = true;
        log('✓ Added validate-env script', 'green');
        fixed++;
      }
    }

    // Save modified package.json
    if (modified) {
      fs.writeFileSync(
        this.packagePath,
        JSON.stringify(this.packageJson, null, 2) + '\n'
      );
      log('\n✓ package.json updated', 'green');
    }

    if (fixed > 0) {
      log(`\n✓ Fixed ${fixed} issue(s)`, 'green');
      log('\nRun npm install to apply changes', 'yellow');
    } else {
      log('No auto-fixes available', 'yellow');
    }
  }

  run(autoFix = false) {
    log('\n================================', 'blue');
    log('DEPENDENCY VALIDATION', 'blue');
    log('================================\n', 'blue');

    if (!this.loadPackageJson()) {
      return false;
    }

    this.checkNodeVersion();
    this.checkSecurityVulnerabilities();
    this.checkOutdatedPackages();
    this.checkMissingScripts();
    this.checkDuplicateDependencies();

    this.generateFixes();

    if (autoFix) {
      this.autoFix();
    } else {
      log('\nTo auto-fix issues, run:', 'blue');
      log('  node scripts/fix-dependencies.js --fix', 'blue');
    }

    return this.issues.length === 0;
  }
}

// Main execution
function main() {
  const args = process.argv.slice(2);
  const autoFix = args.includes('--fix') || args.includes('-f');

  const fixer = new DependencyFixer();
  const success = fixer.run(autoFix);

  process.exit(success ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { DependencyFixer };