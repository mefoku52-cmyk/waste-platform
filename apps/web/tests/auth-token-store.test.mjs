import test from 'node:test';
import assert from 'node:assert/strict';
import { tokenStore } from '../src/lib/auth/token-store.ts';

function mockBrowserStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  globalThis.window = {
    localStorage: {
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => values.set(key, String(value)),
      removeItem: (key) => values.delete(key),
    },
  };
  return values;
}

test('stores access token only in memory and never stores refresh token', () => {
  const values = mockBrowserStorage();
  tokenStore.clearToken();
  tokenStore.setTokens('access-secret', 'refresh-secret', true);

  assert.equal(tokenStore.getToken(), 'access-secret');
  assert.equal(tokenStore.getRefreshToken(), null);
  assert.equal(values.has('accessToken'), false);
  assert.equal(values.has('refreshToken'), false);
  assert.equal(values.has('rememberMe'), false);

  delete globalThis.window;
  assert.equal(tokenStore.getToken(), 'access-secret');
  tokenStore.clearToken();
});

test('removes credentials persisted by older releases', () => {
  const values = mockBrowserStorage({
    accessToken: 'old-access',
    refreshToken: 'old-refresh',
    rememberMe: 'true',
  });
  tokenStore.clearToken();
  assert.equal(values.has('accessToken'), false);
  assert.equal(values.has('refreshToken'), false);
  assert.equal(values.has('rememberMe'), false);
  delete globalThis.window;
});

test('clearToken invalidates the current in-memory access token', () => {
  mockBrowserStorage();
  tokenStore.setToken('temporary-access');
  tokenStore.clearToken();
  assert.equal(tokenStore.getToken(), null);
  delete globalThis.window;
});
