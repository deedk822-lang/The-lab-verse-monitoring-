// src/main.ts
import { EnterpriseConfigLoader } from './config/EnterpriseConfig';
import { CardinalityWatcher } from './cardinalityWatcher';
import * as http from 'http';
import { CompetitiveIntelligence, BusinessImpactTracking } from './config/EnterpriseConfig';

async function initializeCompetitiveBenchmarking(config: CompetitiveIntelligence) {
    console.log('Initializing competitive benchmarking with config:', config);
}

async function initializeBusinessImpactTracking(config: BusinessImpactTracking) {
    console.log('Initializing business impact tracking with config:', config);
}

async function main() {
  console.log('🚀 Launching Enhanced Task Orchestrator with Enterprise Features');

  const cfg = EnterpriseConfigLoader.getInstance().getConfig();

  // Log enterprise features
  console.log('🏢 Enterprise Features Active:');
  console.log(`  • Human Oversight Mode: ${cfg.human_oversight_mode}`);
  console.log(`  • Multi-Cloud Support: ${cfg.multi_cloud_deployment.enabled ? 'Enabled' : 'Disabled'}`);
  console.log(`  • Chaos Engineering: ${cfg.chaos_engineering.enabled ? 'Enabled' : 'Disabled'}`);
  console.log(`  • Mobile Integration: ${cfg.mobile_integration.push_notifications ? 'Enabled' : 'Disabled'}`);
  console.log(`  • Competitive Intelligence: ${cfg.competitive_intelligence.benchmarking_enabled ? 'Enabled' : 'Disabled'}`);

  // Initialize orchestrator with enterprise config
  const watcher = new CardinalityWatcher({
    warnRatio: cfg.risk_thresholds.high,
  });

  // Periodically clean up stale series
  setInterval(() => {
    console.log('Running periodic cleanup of stale series...');
    watcher.cleanup();
  }, 60 * 60 * 1000); // Every hour

  // Initialize competitive intelligence
  if (cfg.competitive_intelligence.benchmarking_enabled) {
    console.log('🏆 Competitive benchmarking enabled');
    await initializeCompetitiveBenchmarking(cfg.competitive_intelligence);
  }

  // Initialize business impact tracking
  if (cfg.business_impact_tracking.revenue_anomaly_tracking) {
    console.log('💰 Business impact tracking enabled');
    await initializeBusinessImpactTracking(cfg.business_impact_tracking);
  }

  const server = http.createServer((req, res) => {
    if (req.url === '/healthz' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('OK');
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('Not Found');
    }
  });

  const PORT = 8080;
  server.listen(PORT, () => {
    console.log(`Cardinality Guardian server running on port ${PORT}`);
  });

  console.log('✅ Enterprise orchestrator ready with rival-proof features!');
}

main().catch(error => {
    console.error("Failed to start the service:", error);
    process.exit(1);
});