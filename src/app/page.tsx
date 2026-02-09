import { BentoGrid } from '@/components/BentoGrid';
import { CommandHUD } from '@/components/CommandHUD';
import { HeroSection } from '@/components/HeroSection';
import { SmartRow } from '@/components/SmartRow';

export default function Dashboard() {
  return (
    <>
      <HeroSection />
      <main className="mx-auto max-w-6xl space-y-10 px-6 py-10">
        <SmartRow items={['Fix #421', 'Agent Sync', 'Latency Patch']} />
        <BentoGrid>
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Performance
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-foreground">
              2.1s LCP
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Smoothest render window across the last 24 hours.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Agents
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-foreground">
              12 Active
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Real-time confidence stream stabilized above 0.87.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Budget
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-foreground">
              148kb JS
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Lighthouse budget guardrails holding the line.
            </p>
          </div>
        </BentoGrid>
      </main>
      <CommandHUD open />
    </>
  );
}
