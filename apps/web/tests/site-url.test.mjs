import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(
  new URL('../src/lib/site.ts', import.meta.url),
  'utf8'
);

test('produkčný fallback je verejná HTTPS doména CMEP', () => {
  assert.match(source, /PRODUCTION_FALLBACK\s*=\s*'https:\/\/trc-cmep\.sk'/);
});

test('konfigurovaná URL sa validuje pred použitím', () => {
  assert.match(source, /normalizedPublicUrl/);
  assert.match(source, /hostname\s*===\s*'localhost'/);
  assert.match(source, /parsed\.protocol\s*!==\s*'https:'/);
});

test('produkčný request nepoužíva host hlavičky ako fallback', () => {
  assert.match(
    source,
    /if\s*\(process\.env\.NODE_ENV\s*===\s*'production'\)\s*return PRODUCTION_FALLBACK/
  );
});

test('sú exportované funkcie pre sitemap, robots a requesty', () => {
  assert.match(source, /export function siteBaseUrlFromEnv/);
  assert.match(source, /export async function siteBaseUrl/);
});
