/**
 * Normalized API error used across the app.
 *
 * The HTTP client must throw a real `Error` instance (not a plain object),
 * otherwise callers that do `e instanceof Error` silently drop the backend
 * message and show a generic fallback. `ApiError` keeps the previous shape
 * (`message`, `status`, `errors`) AND satisfies `instanceof Error`.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly errors?: unknown;

  constructor(message: string, status: number, errors?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errors = errors;
    // Keep `instanceof ApiError` working when compiled down to ES5/ES2015 targets.
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/**
 * Build an `ApiError` from a parsed backend error body.
 *
 * FastAPI returns errors as `{ "detail": "..." }` (string) or, for validation
 * errors, `{ "detail": [{ loc, msg }] }`. Both must map to a readable message.
 */
export function toApiError(status: number, errorData: unknown): ApiError {
  const data =
    errorData && typeof errorData === 'object' ? (errorData as Record<string, unknown>) : {};

  const message = extractMessage(data.detail) ?? extractMessage(data.message);
  return new ApiError(message ?? 'An unexpected error occurred', status, data.errors);
}

function extractMessage(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim()) {
    return value;
  }
  if (Array.isArray(value)) {
    const parts = value
      .map((item) =>
        item && typeof item === 'object'
          ? extractMessage((item as Record<string, unknown>).msg)
          : extractMessage(item),
      )
      .filter((part): part is string => Boolean(part));
    if (parts.length > 0) {
      return parts.join('; ');
    }
  }
  return undefined;
}

/**
 * Safe, readable message for any thrown value.
 *
 * Handles real `Error`/`ApiError` instances as well as the legacy
 * plain-object shape, so a caught error never disappears behind a fallback.
 */
export function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (error && typeof error === 'object') {
    const message = (error as { message?: unknown }).message;
    if (typeof message === 'string' && message.trim()) {
      return message;
    }
  }
  return fallback;
}
