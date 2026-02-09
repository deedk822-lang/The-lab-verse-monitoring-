#!/usr/bin/env node

/**
 * Kimi CLI - Control Nerve System for Vaal AI Empire
 * Standalone version without external dependencies
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');

// CLI Colors
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
  bgBlue: '\x1b[44m'
};

// Utility Functions
const printHeader = () => {
  console.log(`
${colors.cyan}${colors.bright}
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🚀 VAAL AI EMPIRE - KIMI CLI CONTROL                       ║
║                         Central Nerve System v1.0                            ║
╚══════════════════════════════════════════════════════════════════════════════╝${colors.reset}
`);
};

const printSection = (title) => {
  console.log(`\n${colors.magenta}${colors.bright}▶ ${title}${colors.reset}`);
  console.log(`${colors.magenta}${'─'.repeat(50)}${colors.reset}`);
};

const printSuccess = (message) => {
  console.log(`${colors.green}✓ ${message}${colors.reset}`);
};

const printError = (message) => {
  console.log(`${colors.red}✗ ${message}${colors.reset}`);
};

const printWarning = (message) => {
  console.log(`${colors.yellow}⚠ ${message}${colors.reset}`);
};

const printInfo = (message) => {
  console.log(`${colors.blue}ℹ ${message}${colors.reset}`);
};

const printData = (label, value) => {
  console.log(`${colors.cyan}${label}:${colors.reset} ${value}`);
};

// System Check Functions
const checkSystemHealth = async () => {
  printSection('SYSTEM HEALTH CHECK');

  const health = {
    timestamp: new Date().toISOString(),
    status: 'checking',
    components: {}
  };

  // Check Node.js
  try {
    const nodeVersion = process.version;
    health.components.nodejs = { status: 'healthy', version: nodeVersion };
    printSuccess(`Node.js: ${nodeVersion}`);
  } catch (error) {
    health.components.nodejs = { status: 'error', error: error.message };
    printError('Node.js: Not available');
  }

  // Check file system
  try {
    const requiredFiles = ['package.json'];
    let allFilesExist = true;

    requiredFiles.forEach(file => {
      if (fs.existsSync(file)) {
        printSuccess(`File ${file}: Present`);
      } else {
        printError(`File ${file}: Missing`);
        allFilesExist = false;
      }
    });

    health.components.filesystem = {
      status: allFilesExist ? 'healthy' : 'warning',
      files: requiredFiles.length
    };
  } catch (error) {
    health.components.filesystem = { status: 'error', error: error.message };
    printError('File system check failed');
  }

  // Check environment
  try {
    const envFile = '.env';
    if (fs.existsSync(envFile) || fs.existsSync('.env.local')) {
      printSuccess('Environment file: Present');
      health.components.environment = { status: 'healthy', configured: true };
    } else {
      printWarning('Environment file: Not found, using defaults');
      health.components.environment = { status: 'warning', configured: false };
    }
  } catch (error) {
    health.components.environment = { status: 'error', error: error.message };
    printError('Environment check failed');
  }

  // Check API health
  await new Promise(resolve => {
    const port = process.env.PORT || 3000;
    const options = {
      hostname: 'localhost',
      port: port,
      path: '/health',
      method: 'GET',
      timeout: 2000
    };

    const req = http.request(options, res => {
      if (res.statusCode === 200) {
        health.components.api = { status: 'healthy' };
        printSuccess('API Health: Responding OK');
      } else {
        health.components.api = { status: 'warning', http_code: res.statusCode };
        printWarning(`API Health: Responded with ${res.statusCode}`);
      }
      resolve();
    });

    req.on('timeout', () => {
      health.components.api = { status: 'error', error: 'Timeout' };
      printError('API Health: Unreachable (Timeout)');
      req.destroy();
      resolve();
    });

    req.on('error', e => {
      health.components.api = { status: 'error', error: e.message };
      printError('API Health: Unreachable');
      resolve();
    });

    req.end();
  });

  // Overall status
  const componentStatuses = Object.values(health.components).map(c => c.status);
  const hasErrors = componentStatuses.includes('error');
  const hasWarnings = componentStatuses.includes('warning');

  health.status = hasErrors ? 'error' : (hasWarnings ? 'warning' : 'healthy');

  console.log(`\n${colors.bright}Overall Status: ${
    health.status === 'healthy' ? colors.bgGreen : (health.status === 'warning' ? colors.yellow : colors.bgRed)
  } ${health.status.toUpperCase()} ${colors.reset}`);
};

const showSystemInfo = () => {
    printSection('SYSTEM INFORMATION');
    printData('Hostname', os.hostname());
    printData('Platform', `${os.platform()} ${os.arch()}`);
    printData('OS Release', os.release());
    printData('CPU Cores', os.cpus().length);
    printData('Memory (Total)', `${(os.totalmem() / 1024 / 1024 / 1024).toFixed(2)} GB`);
    printData('Memory (Free)', `${(os.freemem() / 1024 / 1024 / 1024).toFixed(2)} GB`);
    printData('Uptime', `${(os.uptime() / 3600).toFixed(2)} hours`);
    printData('Node.js Version', process.version);
    printData('CLI Path', __filename);
};

const showHelp = () => {
    printHeader();
    printSection('AVAILABLE COMMANDS');
    console.log(`
  ${colors.bright}status${colors.reset}     - Perform a comprehensive system health check.
  ${colors.bright}info${colors.reset}       - Display detailed system and environment information.
  ${colors.bright}help${colors.reset}       - Show this help message.
    `);
    printSection('USAGE');
    console.log(`
  node kimi-cli-standalone.cjs <command>
    `);
};

const main = async () => {
    const args = process.argv.slice(2);
    const command = args[0] || 'help';

    if (command !== 'help') {
      printHeader();
    }

    switch (command) {
        case 'status':
            await checkSystemHealth();
            break;
        case 'info':
            showSystemInfo();
            break;
        case 'help':
            showHelp();
            break;
        default:
            printError(`Unknown command: ${command}`);
            showHelp();
            break;
    }
};

main().catch(err => {
    printError('An unexpected error occurred:');
    console.error(err);
    process.exit(1);
});
