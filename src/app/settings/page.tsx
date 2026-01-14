'use client';

import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function Settings() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-2">Configure monitoring and system settings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Alert Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">CPU Alert Threshold</label>
              <input
                type="number"
                defaultValue="80"
                className="w-full mt-2 p-2 border border-input rounded-md bg-background"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Memory Alert Threshold</label>
              <input
                type="number"
                defaultValue="85"
                className="w-full mt-2 p-2 border border-input rounded-md bg-background"
              />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Email Alerts</label>
              <input type="checkbox" defaultChecked className="h-4 w-4" />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Slack Integration</label>
              <input type="checkbox" defaultChecked className="h-4 w-4" />
            </div>
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">SMS Alerts</label>
              <input type="checkbox" className="h-4 w-4" />
            </div>
            <Button>Configure Integrations</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
