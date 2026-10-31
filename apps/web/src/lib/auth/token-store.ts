/** Browser-session token storage. Tokens are deliberately never persisted. */
let accessToken: string | null = null;

function clearLegacyStorage(): void {
  if (typeof window === 'undefined') return;
  // Remove tokens previously written by older releases on first interaction.
  window.localStorage.removeItem('accessToken');
  window.localStorage.removeItem('refreshToken');
  window.localStorage.removeItem('rememberMe');
}

export const tokenStore = {
  getToken(): string | null {
    clearLegacyStorage();
    return accessToken;
  },
  setToken(token: string): void {
    clearLegacyStorage();
    accessToken = token;
  },
  /** Refresh tokens are intentionally not exposed to browser JavaScript storage. */
  getRefreshToken(): string | null {
    clearLegacyStorage();
    return null;
  },
  /** Compatibility shim for existing callers; the value is never retained. */
  setRefreshToken(_token: string): void {
    clearLegacyStorage();
  },
  setTokens(access: string, _refresh?: string | null, _remember?: boolean): void {
    this.setToken(access);
  },
  clearToken(): void {
    accessToken = null;
    clearLegacyStorage();
  },
};
