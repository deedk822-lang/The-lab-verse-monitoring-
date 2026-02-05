import type { ReactNode } from 'react';

type BentoGridProps = {
  children: ReactNode;
};

export function BentoGrid({ children }: BentoGridProps) {
  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {children}
    </div>
  );
}
