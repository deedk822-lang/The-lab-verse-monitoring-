'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { BarChart, LineChart, Pie } from '@/components/charts';
import { AlertBox } from '@/components/AlertBox';
import { StatCard } from '@/components/StatCard';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-6">Loading dashboard...</div>;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">System Overview</h1>
        <div className="text-sm text-muted-foreground">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="CPU Usage"
          value="45%"
          trend={2}
          status="normal"
        />
        <StatCard
          title="Memory"
          value="62%"
          trend={-3}
          status="normal"
        />
        <StatCard
          title="Network I/O"
          value="1.2 GB/s"
          trend={5}
          status="normal"
        />
        <StatCard
          title="Disk Usage"
          value="78%"
          trend={1}
          status="warning"
        />
      </div>

      {/* Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <AlertBox severity="error" message="3 critical alerts" count={3} />
        <AlertBox severity="warning" message="5 warnings" count={5} />
        <AlertBox severity="info" message="2 notices" count={2} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">CPU Usage Over Time</h2>
          <LineChart />
        </Card>
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Memory Distribution</h2>
          <Pie />
        </Card>
        <Card className="p-6 lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Request Performance</h2>
          <BarChart />
        </Card>
      </div>
    </div>
  );
}
