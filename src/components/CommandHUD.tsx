'use client';

import { useAgentStream } from '@/hooks/useAgentStream';

type CommandHUDProps = {
  open: boolean;
};

export function CommandHUD({ open }: CommandHUDProps) {
  const thoughts = useAgentStream();

  return (
    <aside
      className={`fixed right-6 top-24 w-80 rounded-2xl border border-border bg-card/95 p-5 shadow-xl backdrop-blur transition-opacity ${
        open ? 'opacity-100' : 'opacity-0 pointer-events-none'
      }`}
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">Agent Stream</h2>
        <span className="text-xs text-muted-foreground">Live</span>
      </div>
      <div className="space-y-3 text-xs text-muted-foreground">
        {thoughts.length === 0 ? (
          <p className="rounded-lg border border-dashed border-border px-3 py-2 text-center">
            Waiting for telemetry...
          </p>
        ) : (
          thoughts.map((thought, index) => (
            <div key={`${thought.agent}-${index}`} className="border-l border-purple-400/40 pl-3">
              <div className="text-[11px] font-semibold text-foreground">
                {thought.agent}
              </div>
              <div>{thought.thought}</div>
              <div className="text-[10px] text-muted-foreground">
                Confidence {thought.confidence}
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
