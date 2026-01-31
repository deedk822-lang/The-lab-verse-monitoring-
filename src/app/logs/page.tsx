'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Logs() {
  const logs = [
    {
      timestamp: '2026-01-03 11:45:23',
      level: 'INFO',
      service: 'api-server',
      message: 'Request from client 192.168.1.100',
    },
    {
      timestamp: '2026-01-03 11:44:56',
      level: 'WARN',
      service: 'database',
      message: 'Slow query detected: SELECT * FROM users (2.5s)',
    },
    {
      timestamp: '2026-01-03 11:44:12',
      level: 'ERROR',
      service: 'cache',
      message: 'Redis connection timeout',
    },
    {
      timestamp: '2026-01-03 11:43:45',
      level: 'DEBUG',
      service: 'worker',
      message: 'Processing job: send-email-batch',
    },
  ];

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-600 dark:text-red-400';
      case 'WARN':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'INFO':
        return 'text-blue-600 dark:text-blue-400';
      case 'DEBUG':
        return 'text-gray-600 dark:text-gray-400';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">System Logs</h1>
          <p className="text-muted-foreground mt-2">Real-time system and application logs</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Filter className="h-4 w-4" />
          Filter
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="divide-y">
            {logs.map((log, i) => (
              <div key={i} className="p-4 hover:bg-muted transition-colors font-mono text-sm">
                <div className="flex gap-4">
                  <span className="text-muted-foreground w-40 flex-shrink-0">{log.timestamp}</span>
                  <span className={`font-bold w-16 flex-shrink-0 ${getLevelColor(log.level)}`}>
                    {log.level}
                  </span>
                  <span className="text-muted-foreground w-32 flex-shrink-0">{log.service}</span>
                  <span className="text-foreground flex-1">{log.message}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
