'use client';

import { ArrowUp, ArrowDown } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface StatCardProps {
  title: string;
  value: string | number;
  trend?: number;
  status?: 'normal' | 'warning' | 'critical';
}

export function StatCard({ title, value, trend = 0, status = 'normal' }: StatCardProps) {
  const isPositive = trend >= 0;
  const statusColor = {
    normal: 'text-green-600 dark:text-green-400',
    warning: 'text-yellow-600 dark:text-yellow-400',
    critical: 'text-red-600 dark:text-red-400',
  };

  return (
    <Card className="p-4">
      <div className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold">{value}</p>
        {trend !== 0 && (
          <div className="flex items-center gap-1 pt-2">
            {isPositive ? (
              <ArrowUp className="h-4 w-4 text-red-500" />
            ) : (
              <ArrowDown className="h-4 w-4 text-green-500" />
            )}
            <span className={cn('text-sm font-medium', statusColor[status])}>
              {Math.abs(trend)}%
            </span>
          </div>
        )}
      </div>
    </Card>
  );
}
