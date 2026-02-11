import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

export default function MonitoringDashboard() {
  const [overview, setOverview] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [costs, setCosts] = useState(null);
  const [synthetic, setSynthetic] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // Fetch all monitoring data
  const fetchData = async () => {
    try {
      const [overviewRes, perfRes, alertsRes, costsRes, syntheticRes] = await Promise.all([
        fetch('/api/monitoring/overview'),
        fetch('/api/monitoring/performance'),
        fetch('/api/monitoring/alerts?limit=10'),
        fetch('/api/monitoring/costs'),
        fetch('/api/monitoring/synthetic'),
      ]);

      if (!overviewRes.ok) throw new Error('Failed to fetch overview');

      setOverview(await overviewRes.json());
      setPerformance(await perfRes.json());
      setAlerts(await alertsRes.json());
      setCosts(await costsRes.json());
      setSynthetic(await syntheticRes.json());
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching monitoring data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh effect
  useEffect(() => {
    fetchData();

    if (autoRefresh) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Manual refresh
  const handleRefresh = () => {
    setLoading(true);
    fetchData();
  };

  // Send test alert
  const sendTestAlert = async () => {
    try {
      const response = await fetch('/api/monitoring/alerts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: 'Test Alert',
          message: 'This is a test alert from the dashboard',
          severity: 'low',
          channels: ['log'],
        }),
      });

      if (response.ok) {
        alert('Test alert sent successfully!');
        fetchData();
      }
    } catch (err) {
      alert('Failed to send test alert: ' + err.message);
    }
  };

  // Trigger synthetic check
  const runSyntheticCheck = async () => {
    try {
      const response = await fetch('/api/monitoring/synthetic/check', {
        method: 'POST',
      });

      if (response.ok) {
        alert('Synthetic check completed!');
        fetchData();
      }
    } catch (err) {
      alert('Failed to run synthetic check: ' + err.message);
    }
  };

  if (loading && !overview) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Data</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            🔍 Lab Verse Monitoring Dashboard
          </h1>
          <div className="flex gap-3">
            <button
              onClick={handleRefresh}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
              disabled={loading}
            >
              {loading ? '⏳' : '🔄'} Refresh
            </button>
            <button
              onClick={sendTestAlert}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
            >
              📢 Test Alert
            </button>
            <button
              onClick={runSyntheticCheck}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              ✓ Run Check
            </button>
          </div>
        </div>

        {/* Auto-refresh toggle */}
        <div className="mt-4 flex items-center gap-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-gray-600">Auto-refresh</span>
          </label>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="text-sm border rounded px-2 py-1"
            disabled={!autoRefresh}
          >
            <option value={10000}>10s</option>
            <option value={30000}>30s</option>
            <option value={60000}>1m</option>
            <option value={300000}>5m</option>
          </select>
          <span className="text-xs text-gray-500">
            Last updated: {new Date(overview?.timestamp).toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatusCard
          title="System Health"
          value={overview?.system?.uptime?.formatted || 'N/A'}
          subtitle="Uptime"
          icon="💚"
          color="green"
        />
        <StatusCard
          title="Total Requests"
          value={performance?.stats?.requests?.count || 0}
          subtitle={`Avg: ${performance?.stats?.requests?.avgDuration?.toFixed(0) || 0}ms`}
          icon="📊"
          color="blue"
        />
        <StatusCard
          title="Active Alerts"
          value={alerts?.stats?.total || 0}
          subtitle={`Critical: ${alerts?.stats?.bySeverity?.critical || 0}`}
          icon="🚨"
          color={alerts?.stats?.bySeverity?.critical > 0 ? 'red' : 'yellow'}
        />
        <StatusCard
          title="Total Cost"
          value={`$${costs?.total?.toFixed(2) || '0.00'}`}
          subtitle={`Monthly proj: $${costs?.projections?.monthly?.toFixed(2) || '0.00'}`}
          icon="💰"
          color="purple"
        />
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Request Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Request Performance</h2>
          {performance?.stats?.requests && (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-sm text-gray-600">P50</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {performance.stats.requests.p50?.toFixed(0)}ms
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">P95</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {performance.stats.requests.p95?.toFixed(0)}ms
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">P99</p>
                  <p className="text-2xl font-bold text-red-600">
                    {performance.stats.requests.p99?.toFixed(0)}ms
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* System & Cost */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* System Stats */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">System Stats</h2>
            <div className="space-y-3">
              <MemoryBar label="Heap Used" value={overview?.system?.memory?.heapUsed} max={overview?.system?.memory?.heapTotal} color="blue" />
              <MemoryBar label="RSS" value={overview?.system?.memory?.rss} max={overview?.system?.memory?.heapTotal * 1.5} color="purple" />
              <MemoryBar label="External" value={overview?.system?.memory?.external} max={overview?.system?.memory?.heapTotal * 0.5} color="green" />
            </div>
          </div>

          {/* Cost Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Cost Distribution</h2>
            <ResponsiveContainer width="100%" height={150}>
              <PieChart>
                <Pie
                  data={Object.entries(costs?.byService || {}).map(([name, value]) => ({ name, value }))}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={60}
                  fill="#8884d8"
                >
                  {Object.keys(costs?.byService || {}).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toFixed(4)}`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Alerts and Synthetic Monitoring */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Alerts</h2>
          <div className="space-y-2">
            {alerts?.history?.map(alert => (
              <div key={alert.id} className={`p-3 rounded-lg border-l-4 ${
                {
                  critical: 'bg-red-50 border-red-500',
                  high: 'bg-orange-50 border-orange-500',
                  medium: 'bg-yellow-50 border-yellow-500',
                  low: 'bg-blue-50 border-blue-500',
                }[alert.severity]
              }`}>
                <div className="flex justify-between text-sm">
                  <p className="font-semibold">{alert.title}</p>
                  <p className="text-gray-500">{new Date(alert.timestamp).toLocaleTimeString()}</p>
                </div>
                <p className="text-xs text-gray-700 mt-1">{alert.message}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Synthetic Checks */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Synthetic Checks</h2>
          <div className="space-y-3">
            {synthetic?.endpoints?.map(endpoint => (
              <div key={endpoint.name} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-semibold">{endpoint.name}</p>
                  <p className="text-xs text-gray-500">{endpoint.url}</p>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${endpoint.success ? 'text-green-600' : 'text-red-600'}`}>
                    {endpoint.success ? 'Up' : 'Down'}
                  </p>
                  <p className="text-xs text-gray-500">{endpoint.duration.toFixed(2)}s</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Status Card Component
function StatusCard({ title, value, subtitle, icon, color }) {
  const colorClasses = {
    green: 'bg-green-50 border-green-200 text-green-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    red: 'bg-red-50 border-red-200 text-red-800',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    purple: 'bg-purple-50 border-purple-200 text-purple-800',
  };

  return (
    <div className={`rounded-lg border-2 p-4 ${colorClasses[color]}`}>
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium opacity-80">{title}</h3>
        <span className="text-2xl">{icon}</span>
      </div>
      <p className="text-2xl font-bold mb-1">{value}</p>
      <p className="text-xs opacity-70">{subtitle}</p>
    </div>
  );
}

// Memory Bar Component
function MemoryBar({ label, value, max, color }) {
  const percentage = (value / max) * 100;

  const colorClasses = {
    blue: 'bg-blue-500',
    purple: 'bg-purple-500',
    green: 'bg-green-500',
  };

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-mono">{(value / 1024 / 1024).toFixed(2)} MB</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colorClasses[color]}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
}
