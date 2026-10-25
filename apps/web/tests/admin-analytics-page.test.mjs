import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const source = await readFile(
  new URL('../src/app/dashboard/admin/analytics/page.tsx', import.meta.url),
  'utf8',
);

test('admin analytics page volá sdielaný http klient s admin stats endpoint', () => {
  assert.match(source, /http\.get/);
  assert.match(source, /\/analytics\/admin\/stats/);
});

test('admin analytics page nepoužíva surový fetch a ručný token z localStorage', () => {
  assert.ok(!/await fetch\(/.test(source));
  assert.ok(!/localStorage\.getItem/.test(source));
  assert.ok(!/config\.apiBaseUrl/.test(source));
});
