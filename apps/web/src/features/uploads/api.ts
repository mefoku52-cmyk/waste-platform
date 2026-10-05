import { config } from '../../lib/config';
import { http } from '../../lib/api/http';
import { tokenStore } from '../../lib/auth/token-store';

export type UploadResponse = {
  fileId: string;
  url: string;
  originalName: string;
  size: number;
  contentType: string;
};

export type SignedUrlResponse = {
  fileId: string;
  urlPath: string;
  expiresAt: number;
};

const FILE_ID_RE = /\/uploads\/([a-f0-9]{32}\.[a-z0-9]+)/i;

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const token = tokenStore.getToken();
  const res = await fetch(`${config.apiBaseUrl}/uploads`, {
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

export function extractFileId(url: string): string | null {
  const match = FILE_ID_RE.exec(url);
  return match ? match[1] : null;
}

export async function getSignedUrl(
  fileId: string,
  ttlSeconds = 300,
): Promise<SignedUrlResponse> {
  return http.post<SignedUrlResponse>(
    `/uploads/${fileId}/sign?ttl_seconds=${ttlSeconds}`,
    undefined,
  );
}
