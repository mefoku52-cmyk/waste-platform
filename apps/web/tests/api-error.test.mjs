import { test } from 'node:test';
import assert from 'node:assert/strict';

import { ApiError, toApiError, errorMessage } from '../src/lib/api/api-error.ts';

test('toApiError keeps the backend detail and is a real Error', () => {
  const err = toApiError(400, { detail: 'Stripe error: account cannot make live charges' });
  assert.ok(err instanceof Error);
  assert.ok(err instanceof ApiError);
  assert.equal(err.message, 'Stripe error: account cannot make live charges');
  assert.equal(err.status, 400);
});

test('toApiError joins FastAPI validation error details', () => {
  const err = toApiError(422, {
    detail: [
      { loc: ['body', 'days'], msg: 'Input should be a valid integer' },
      { loc: ['body', 'tier'], msg: 'Unknown tier/days combo' },
    ],
  });
  assert.equal(err.message, 'Input should be a valid integer; Unknown tier/days combo');
  assert.equal(err.status, 422);
});

test('toApiError falls back to message field then a generic default', () => {
  assert.equal(toApiError(500, { message: 'boom' }).message, 'boom');
  assert.equal(toApiError(500, {}).message, 'An unexpected error occurred');
  assert.equal(toApiError(500, null).message, 'An unexpected error occurred');
});

test('toApiError preserves the errors payload', () => {
  const err = toApiError(400, { detail: 'x', errors: { field: 'bad' } });
  assert.deepEqual(err.errors, { field: 'bad' });
});

test('errorMessage reads Error instances (regression for instanceof check)', () => {
  // The previous bug: http.ts threw a plain object, so `e instanceof Error` was
  // false and the backend detail was replaced by a generic fallback.
  const apiError = toApiError(400, { detail: 'real backend reason' });
  assert.equal(errorMessage(apiError, 'fallback'), 'real backend reason');
});

test('errorMessage still tolerates legacy plain-object throws', () => {
  assert.equal(errorMessage({ message: 'legacy shape' }, 'fallback'), 'legacy shape');
  assert.equal(errorMessage({}, 'fallback'), 'fallback');
  assert.equal(errorMessage(null, 'fallback'), 'fallback');
  assert.equal(errorMessage('nope', 'fallback'), 'fallback');
});
