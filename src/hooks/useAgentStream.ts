import { useEffect, useState } from 'react';

type AgentThought = {
  agent: string;
  thought: string;
  confidence: string;
};

export function useAgentStream() {
  const [thoughts, setThoughts] = useState<AgentThought[]>([]);

  useEffect(() => {
    const eventSource = new EventSource('/api/agents/stream');

    eventSource.onmessage = (event) => {
      const payload = JSON.parse(event.data) as AgentThought;
      setThoughts((previous) => [...previous.slice(-19), payload]);
    };
    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  return thoughts;
}
