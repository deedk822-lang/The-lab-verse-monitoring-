import fs from 'fs/promises';
import fetch from 'node-fetch';

export async function createGrafanaDashboard() {
  try {
    const crisis = JSON.parse(await fs.readFile('./tmp/crisis.json', 'utf8'));

    console.log('📊 Creating Grafana dashboard...');

    // Create public dashboard on your instance
    const response = await fetch(`${process.env.GRAFANA_URL}/api/dashboards/db`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GRAFANA_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        dashboard: {
          title: `Crisis: ${crisis.crisis_id}`,
          tags: ['crisis', 'south-africa'],
          timezone: 'browser',
          panels: [
            {
              title: 'Crisis Overview',
              type: 'text',
              gridPos: { h: 8, w: 24, x: 0, y: 0 },
              options: {
                content: `<h1>${crisis.title}</h1><p>${crisis.description}</p><a href="${crisis.sources[0].url}" target="_blank">Source</a>`
              }
            },
            {
              title: 'Impact Map',
              type: 'geomap',  // Show location
              gridPos: { h: 12, w: 24, x: 0, y: 8 },
              // ... map config
            }
          ]
        },
        folderId: 0,
        overwrite: true
      })
    });

    if (!response.ok) {
      throw new Error(`Grafana API error: ${response.statusText}`);
    }

    const dashboard = await response.json();

    // Set public access
    const setPublicResponse = await fetch(`${process.env.GRAFANA_URL}/api/dashboards/uid/${dashboard.uid}/public-dashboards`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.GRAFANA_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        isEnabled: true,
        annotationsEnabled: true,
        timeSelectionEnabled: true
      })
    });

    if (!setPublicResponse.ok) {
      throw new Error(`Grafana API error (setting public access): ${setPublicResponse.statusText}`);
    }

    const dashboardUrl = `${process.env.GRAFANA_URL}/public-dashboards/${dashboard.uid}`;
    console.log('✅ Grafana dashboard public:', dashboardUrl);

    // Output for GitHub Actions
    if (process.env.GITHUB_OUTPUT) {
      await fs.appendFile(process.env.GITHUB_OUTPUT, `grafana_url=${dashboardUrl}\n`);
    }

  } catch (error) {
    console.error('❌ Error creating Grafana dashboard:', error);
    process.exit(1);
  }
}

createGrafanaDashboard();
