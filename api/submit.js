export const config = { runtime: 'edge' };

export default async function handler(request) {
  const NEW_WORKER = 'https://royal-frost-baec.benjamin-0f3.workers.dev/api/submit';
  
  if (request.method === 'GET') {
    return new Response(JSON.stringify({ ok: true, service: 'proxy-v2' }), {
      headers: { 'Content-Type': 'application/json' }
    });
  }

  const body = await request.text();
  const resp = await fetch(NEW_WORKER, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body
  });
  const data = await resp.text();
  return new Response(data, {
    status: resp.status,
    headers: { 'Content-Type': 'application/json' }
  });
}
// redeploy Ven 29 mai 2026 09:21:47 CEST
