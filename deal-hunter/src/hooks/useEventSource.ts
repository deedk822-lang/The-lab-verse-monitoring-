// hooks/useEventSource.ts
import { useState, useEffect, useRef } from 'react';

interface EventData {
type: string;
data: any;
}

export function useEventSource(url: string) {
const [data, setData] = useState<EventData | null>(null);
const [error, setError] = useState<Error | null>(null);
const eventSourceRef = useRef<EventSource | null>(null);

useEffect(() => {
try {
const eventSource = new EventSource(url);
eventSourceRef.current = eventSource;

eventSource.onmessage = (event) => {
try {
const parsedData = JSON.parse(event.data);
setData(parsedData);
setError(null);
} catch (err) {
setError(new Error('Failed to parse event data'));
}
};

eventSource.onerror = (event) => {
setError(new Error('EventSource failed'));
};

return () => {
if (eventSourceRef.current) {
eventSourceRef.current.close();
}
};
} catch (err) {
setError(err as Error);
}
}, [url]);

return { data, error };
}
