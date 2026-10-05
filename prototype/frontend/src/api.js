// Thin fetch wrapper. Attaches Bearer token from localStorage, throws on !ok.
// 409 (double-book) is surfaced via err.status so callers can route accordingly.

const BASE = '/api';

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function authHeader() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...authHeader(),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  const text = await res.text();
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    // Preserve structured detail (e.g. 402 {message, booking_status, hold_expires_at}) on err.body;
    // err.message is always a string.
    const detail = (data && data.detail) || res.statusText || 'Request failed';
    let message = detail;
    if (typeof detail === 'object') {
      message = Array.isArray(detail)
        ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
        : detail.message || JSON.stringify(detail);
    }
    throw new ApiError(String(message), res.status, data);
  }
  return data;
}

export const api = {
  get: (p) => request(p),
  post: (p, body) => request(p, { method: 'POST', body }),
  patch: (p, body) => request(p, { method: 'PATCH', body }),
  del: (p) => request(p, { method: 'DELETE' }),
};
