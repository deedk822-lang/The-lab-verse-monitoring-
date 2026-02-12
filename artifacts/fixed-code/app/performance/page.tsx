'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

export default function Performance() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Performance Metrics</h1>
        <p className="text-muted-foreground mt-2">Real-time performance analytics and optimization</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>API Response Times</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Avg Response Time</span>
                <span className="font-bold">145ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span>P95 Response Time</span>
                <span className="font-bold">234ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span>P99 Response Time</span>
                <span className="font-bold">512ms</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Throughput</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Requests/sec</span>
                <span className="font-bold">2,450</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Success Rate</span>
                <span className="font-bold text-green-600">99.95%</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Error Rate</span>
                <span className="font-bold text-red-600">0.05%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
