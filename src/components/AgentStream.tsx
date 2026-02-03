'use client';

import { useEffect, useRef, useState } from 'react';

interface LinearUpdate {
  task_id: string;
  status?: string;
  comment?: string;
}

interface AgentThought {
  type: 'agent_thought' | 'connected' | 'linear_action' | 'error' | 'heartbeat';
  agent?: string;
  event_id?: string;
  timestamp: string;
  thought?: string;
  confidence?: number;
  action?: string;
  linear_update?: LinearUpdate;
  message?: string;
}

type GlowColor = 'green' | 'purple' | 'red';

const glowClasses: Record<GlowColor, string> = {
  green: 'from-emerald-500/10',
  purple: 'from-purple-500/10',
  red: 'from-rose-500/10',
};

export default function AgentStream() {
  const [thoughts, setThoughts] = useState<AgentThought[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [currentGlow, setCurrentGlow] = useState<GlowColor>('purple');
  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const connectStream = () => {
      const eventSource = new EventSource('/api/agent-stream');
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setCurrentGlow('green');
      };

      eventSource.onmessage = (event) => {
        let data: AgentThought | null = null;
        try {
          data = JSON.parse(event.data) as AgentThought;
        } catch {
          return;
        }

        if (!data) {
          return;
        }

        if (data.type !== 'heartbeat') {
          setThoughts((prev) => [...prev, data].slice(-50));
        }

        if (scrollRef.current) {
          scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }

        if (data.type === 'linear_action' && data.linear_update) {
          void triggerLinearUpdate(data.linear_update);
        }

        if (data.confidence !== undefined) {
          if (data.confidence > 0.8) {
            setCurrentGlow('green');
          } else if (data.confidence > 0.5) {
            setCurrentGlow('purple');
          } else {
            setCurrentGlow('red');
          }
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        setCurrentGlow('red');
        eventSource.close();
        setTimeout(connectStream, 3000);
      };
    };

    connectStream();

    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const triggerLinearUpdate = async (update: LinearUpdate) => {
    try {
      await fetch('/api/linear/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      });
    } catch {
      setThoughts((prev) =>
        [
          ...prev,
          {
            type: 'error',
            timestamp: new Date().toISOString(),
            message: 'Failed to sync Linear update',
          },
        ].slice(-50),
      );
    }
  };

  return (
    <div className="relative w-full h-96 rounded-3xl overflow-hidden backdrop-blur-3xl bg-gradient-to-br from-slate-900/90 to-purple-900/30 border border-white/10 shadow-[0_0_50px_rgba(168,85,247,0.3)]">
      <div
        className={`absolute inset-0 bg-gradient-to-br ${glowClasses[currentGlow]} to-transparent transition-colors duration-1000`}
      />

      <div className="flex items-center justify-between p-6 border-b border-white/10 relative z-10">
        <div className="flex items-center gap-3">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
            } shadow-[0_0_10px_currentColor]`}
          />
          <span className="text-xs font-mono uppercase tracking-[0.2em] text-white/60">
            {isConnected ? 'Kimi K2.5 Live Stream' : 'Reconnecting...'}
          </span>
        </div>
        <div className="flex gap-4 text-white/40 text-xs font-mono">
          <span className="px-2 py-1 rounded-full bg-white/5">SSE</span>
          <span className="px-2 py-1 rounded-full bg-white/5">Linear Sync</span>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="h-[calc(100%-80px)] overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent relative z-10"
      >
        {thoughts.length === 0 && (
          <div className="text-white/50 text-sm font-mono">
            Waiting for agent thoughts...
          </div>
        )}

        {thoughts.map((thought, idx) => (
          <div
            key={thought.event_id ?? `${thought.timestamp}-${idx}`}
            className="group relative transition-all duration-300"
          >
            {thought.type === 'agent_thought' && (
              <div className="p-4 rounded-2xl backdrop-blur-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono text-purple-300">
                      {thought.agent || 'kimi-k2.5'}
                    </span>
                  </div>
                  <span className="text-[10px] text-white/40 font-mono">
                    {new Date(thought.timestamp).toLocaleTimeString()}
                  </span>
                </div>

                <p className="text-sm text-white/90 leading-relaxed mb-2">
                  {thought.thought}
                </p>

                {thought.confidence !== undefined && (
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-emerald-500 transition-all duration-500"
                        style={{ width: `${thought.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-mono text-white/50">
                      {(thought.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                )}

                {thought.action && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-emerald-400 font-mono">
                    <span>Action:</span>
                    <span>{thought.action}</span>
                  </div>
                )}
              </div>
            )}

            {thought.type === 'linear_action' && (
              <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/30 text-xs text-blue-300 font-mono">
                → Syncing to Linear: {thought.linear_update?.comment || 'Status update'}
              </div>
            )}

            {thought.type === 'error' && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 font-mono">
                Error: {thought.message || 'Stream error'}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-slate-950 to-transparent pointer-events-none" />
    </div>
  );
}
