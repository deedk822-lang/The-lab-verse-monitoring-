export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    region: process.env.VERCEL_REGION,
    edge: true
  };

  return new Response(JSON.stringify(health), {
    status: 200,
    headers: {
      'content-type': 'application/json',
      'cache-control': 'public, s-maxage=60'
    }
  });
}
