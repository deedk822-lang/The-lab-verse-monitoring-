'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { CheckCircle, AlertCircle } from 'lucide-react';

export default function Health() {
  const services = [
    {
      name: 'API Server',
      status: 'healthy',
      uptime: '99.98%',
      lastCheck: '2 seconds ago',
      responseTime: '45ms',
    },
    {
      name: 'Database',
      status: 'healthy',
      uptime: '99.95%',
      lastCheck: '5 seconds ago',
      responseTime: '12ms',
    },
    {
      name: 'Cache (Redis)',
      status: 'healthy',
      uptime: '99.99%',
      lastCheck: '3 seconds ago',
      responseTime: '2ms',
    },
    {
      name: 'Message Queue',
      status: 'healthy',
      uptime: '99.92%',
      lastCheck: '8 seconds ago',
      responseTime: '5ms',
    },
    {
      name: 'Search Index',
      status: 'degraded',
      uptime: '98.50%',
      lastCheck: '1 second ago',
      responseTime: '234ms',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Service Health</h1>
        <p className="text-muted-foreground mt-2">Monitor health and status of all services</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-4">
        {services.map((service) => (
          <Card key={service.name}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3 flex-1">
                  {service.status === 'healthy' ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : (
                    <AlertCircle className="h-6 w-6 text-yellow-600" />
                  )}
                  <div className="flex-1">
                    <h3 className="font-semibold">{service.name}</h3>
                    <p className="text-sm text-muted-foreground">Status: {service.status}</p>
                  </div>
                </div>
                <div className="text-right text-sm">
                  <p className="font-semibold">{service.uptime}</p>
                  <p className="text-muted-foreground">uptime</p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Response Time</p>
                  <p className="font-mono font-bold">{service.responseTime}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Last Check</p>
                  <p className="font-mono text-sm">{service.lastCheck}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
