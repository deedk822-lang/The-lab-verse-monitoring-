import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      services: {
        database: 'healthy',
        cache: 'healthy',
        queue: 'healthy',
      },
      uptime: process.uptime(),
      version: '1.0.0',
    };

    return NextResponse.json(health);
  } catch (error) {
    return NextResponse.json(
      { status: 'unhealthy', error: 'Health check failed' },
      { status: 503 }
    );
  }
}
