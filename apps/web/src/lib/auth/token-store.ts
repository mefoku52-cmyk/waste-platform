const TOKEN_KEY = 'auth_token';
const REMEMBER_KEY = 'auth_remember';

export const tokenStore = {
  setToken: (token: string, remember = true) => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(REMEMBER_KEY, remember ? '1' : '0');
  },
  getToken: () => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(TOKEN_KEY);
  },
  clearToken: () => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REMEMBER_KEY);
  },
  isRemembered: () => {
    if (typeof window === 'undefined') return true;
    return localStorage.getItem(REMEMBER_KEY) !== '0';
  },
};
