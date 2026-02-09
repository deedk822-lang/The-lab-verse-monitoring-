'use client';

import { useScrollProgress } from '@/hooks/useScrollProgress';

export function HeroSection() {
  const progress = useScrollProgress();

  return (
    <section className="relative overflow-hidden border-b border-border bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-8 py-16 text-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <p className="text-xs uppercase tracking-[0.3em] text-white/60">
          Lab-verse monitoring
        </p>
        <h1 className="text-4xl font-semibold sm:text-5xl">
          AI operations, live telemetry, and confidence in every signal.
        </h1>
        <p className="max-w-2xl text-base text-white/70">
          Stream real-time agent thoughts, track performance budgets, and keep
          the system calm under load with a cinematic observability command
          center.
        </p>
        <div className="flex flex-wrap gap-3">
          <span className="rounded-full border border-white/20 bg-white/10 px-4 py-1 text-xs">
            60fps telemetry
          </span>
          <span className="rounded-full border border-white/20 bg-white/10 px-4 py-1 text-xs">
            Lighthouse gates
          </span>
          <span className="rounded-full border border-white/20 bg-white/10 px-4 py-1 text-xs">
            Live agent stream
          </span>
        </div>
      </div>
      <div className="absolute bottom-0 left-0 h-1 w-full bg-white/10">
        <div
          className="h-full bg-gradient-to-r from-purple-400 via-sky-400 to-emerald-400 transition-all"
          style={{ width: `${Math.min(progress * 100, 100)}%` }}
        />
      </div>
    </section>
  );
}
