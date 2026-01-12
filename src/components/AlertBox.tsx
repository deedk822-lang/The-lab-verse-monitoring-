'use client';

import { AlertCircle, AlertTriangle, InfoIcon } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface AlertBoxProps {
  severity: 'error' | 'warning' | 'info';
  message: string;
  count: number;
}

export function AlertBox({ severity, message, count }: AlertBoxProps) {
  const icons = {
    error: AlertCircle,
    warning: AlertTriangle,
    info: InfoIcon,
  };

  const colors = {
    error: 'bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800',
    warning: 'bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800',
    info: 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800',
  };

  const iconColors = {
    error: 'text-red-600 dark:text-red-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    info: 'text-blue-600 dark:text-blue-400',
  };

  const Icon = icons[severity];

  return (
    <Card className={cn('p-4 border-2', colors[severity])}>
      <div className="flex items-center gap-3">
        <Icon className={cn('h-5 w-5', iconColors[severity])} />
        <div className="flex-1">
          <p className="font-medium text-sm">{message}</p>
        </div>
        <div className={cn('font-bold text-lg', iconColors[severity])}>
          {count}
        </div>
      </div>
    </Card>
  );
}
