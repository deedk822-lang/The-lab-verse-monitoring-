'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { AlertCircle, AlertTriangle } from 'lucide-react';

export default function Alerts() {
  const alerts = [
    {
      id: 1,
      severity: 'critical',
      title: 'High CPU Usage Detected',
      description: 'CPU usage exceeded 90% for more than 5 minutes',
      time: '2 minutes ago',
    },
    {
      id: 2,
      severity: 'warning',
      title: 'Disk Space Low',
      description: 'Available disk space is below 20%',
      time: '10 minutes ago',
    },
    {
      id: 3,
      severity: 'warning',
      title: 'Memory Pressure',
      description: 'Memory usage is above 80%',
      time: '15 minutes ago',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Alerts & Incidents</h1>
        <p className="text-muted-foreground mt-2">Monitor and manage system alerts in real-time</p>
      </div>

      <div className="space-y-4">
        {alerts.map((alert) => (
          <Card key={alert.id} className="border-l-4 border-l-red-500">
            <CardContent className="p-4">
              <div className="flex gap-4">
                {alert.severity === 'critical' ? (
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-1" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-1" />
                )}
                <div className="flex-1">
                  <h3 className="font-semibold">{alert.title}</h3>
                  <p className="text-sm text-muted-foreground">{alert.description}</p>
                  <p className="text-xs text-muted-foreground mt-2">{alert.time}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
