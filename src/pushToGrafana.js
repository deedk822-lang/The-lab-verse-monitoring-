// src/pushToGrafana.js
import axios from 'axios';
import promClient from 'prom-client';

const { GRAFANA_CLOUD_PROM_URL, GRAFANA_CLOUD_PROM_USER, GRAFANA_CLOUD_API_KEY } = process.env;

export async function pushMetrics() {
  if (!GRAFANA_CLOUD_PROM_URL) return;   // local dev-safe

  const metrics = await promClient.register.metrics();
  try {
    await axios.post(
      GRAFANA_CLOUD_PROM_URL,
      metrics,
      {
        headers: { 'Content-Type': 'text/plain' },
        auth: { username: GRAFANA_CLOUD_PROM_USER, password: GRAFANA_CLOUD_API_KEY }
      }
    );
  } catch (err) {
    console.error('Error pushing metrics to Grafana Cloud:', err.message);
  }
}

// push every 10 s
if (GRAFANA_CLOUD_PROM_URL) {
  setInterval(pushMetrics, 10_000).unref();
}
