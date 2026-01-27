'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  Zap,
  AlertCircle,
  Clock,
  Activity,
  Settings,
  LogOut,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const nav Items = [
  {
    title: 'Dashboard',
    href: '/',
    icon: BarChart3,
  },
  {
    title: 'Performance',
    href: '/performance',
    icon: Zap,
  },
  {
    title: 'Alerts',
    href: '/alerts',
    icon: AlertCircle,
  },
  {
    title: 'Logs',
    href: '/logs',
    icon: Clock,
  },
  {
    title: 'Health',
    href: '/health',
    icon: Activity,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border/40 bg-background">
      <div className="flex flex-col h-full">
        <div className="p-6">
          <Link href="/" className="flex items-center gap-2 font-bold text-lg">
            <Activity className="h-6 w-6 text-primary" />
            <span>Lab-Verse</span>
          </Link>
        </div>
        
        <nav className="flex-1 px-3 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            
            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? 'default' : 'ghost'}
                  className="w-full justify-start gap-3"
                >
                  <Icon className="h-4 w-4" />
                  {item.title}
                </Button>
              </Link>
            );
          })}
        </nav>
        
        <div className="p-3 border-t border-border/40">
          <Button variant="ghost" className="w-full justify-start gap-3 text-destructive">
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </div>
      </div>
    </aside>
  );
}
