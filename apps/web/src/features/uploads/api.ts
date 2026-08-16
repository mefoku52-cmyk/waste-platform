import { config } from '../../lib/config';
import { tokenStore } from '../../lib/auth/token-store';

export async function uploadFile(file: File): Promise<{ url: string }> {
  const form = new FormData();
  form.append('file', file);
  const token = tokenStore.getToken();
  const res = await fetch(`${config.apiBaseUrl}/api/v1/uploads`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Upload failed');
  }
  return res.json();
}
