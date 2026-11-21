function readCookie(name) {
  const prefix = `${encodeURIComponent(name)}=`;
  const item = document.cookie.split('; ').find((part) => part.startsWith(prefix));
  return item ? decodeURIComponent(item.slice(prefix.length)) : '';
}

export async function api(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  const method = (options.method || 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrfCookie = path.startsWith('/admin/') ? 'moki_admin_csrf' : 'moki_csrf';
    const csrf = readCookie(csrfCookie);
    if (csrf) headers.set('X-CSRF-Token', csrf);
  }
  const response = await fetch(`/api${path}`, { ...options, headers, credentials: 'include' });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    let message = 'Something went wrong. Please try again.';
    if (typeof detail === 'string') message = detail;
    else if (Array.isArray(detail)) message = detail.map((item) => item.msg).join(', ');
    const error = new Error(message); error.status = response.status; throw error;
  }
  return payload;
}

export function jsonRequest(method, body) { return { method, body: JSON.stringify(body) }; }
