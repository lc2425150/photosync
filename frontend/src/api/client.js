const BASE = '/api/v1'
const TIMEOUT_MS = 30000

async function request(path, opts = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const r = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...opts.headers },
      signal: controller.signal,
      ...opts,
    })
    if (!r.ok) {
      const body = await r.json().catch(() => ({}))
      const msg = body?.error?.message || body?.message || `HTTP ${r.status}`
      throw new Error(msg)
    }
    // 204 No Content
    if (r.status === 204) return null
    return r.json()
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  get: (p) => request(p),
  post: (p, d) => request(p, { method: 'POST', body: JSON.stringify(d) }),
  put: (p, d) => request(p, { method: 'PUT', body: JSON.stringify(d) }),
  delete: (p) => request(p, { method: 'DELETE' }),
}
