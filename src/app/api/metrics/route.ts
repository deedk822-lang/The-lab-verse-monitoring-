import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Real metrics would come from your monitoring system
    // For now, returning mock data
    const metrics = {
      cpu: Math.random() * 100,
      memory: Math.random() * 100,
      network: Math.random() * 2,
      disk: Math.random() * 100,
      timestamp: new Date().toISOString(),
      uptime: 99.98,
      requests: Math.floor(Math.random() * 10000),
      errors: Math.floor(Math.random() * 100),
      alerts: {
        critical: 3,
        warning: 5,
        info: 2,
      },
    };

    return NextResponse.json(metrics, {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('Metrics API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch metrics' },
      { status: 500 }
    );
  }
}
