'use client';

import { LineChart as LC, BarChart as BC, PieChart as PC } from 'recharts';

export function LineChart() {
  return (
    <div className="w-full h-64 bg-muted rounded flex items-center justify-center">
      <p className="text-muted-foreground">Chart rendering here</p>
    </div>
  );
}

export function BarChart() {
  return (
    <div className="w-full h-64 bg-muted rounded flex items-center justify-center">
      <p className="text-muted-foreground">Chart rendering here</p>
    </div>
  );
}

export function Pie() {
  return (
    <div className="w-full h-64 bg-muted rounded flex items-center justify-center">
      <p className="text-muted-foreground">Chart rendering here</p>
    </div>
  );
}
