const ACCESS_TOKEN_KEY = 'auth_access_token';
const REFRESH_TOKEN_KEY = 'auth_refresh_token';
const REMEMBER_KEY = 'auth_remember';

export const tokenStore = {
  setTokens: (
    accessToken: string,
    refreshToken: string,
    remember = true,
  ) => {
    if (typeof window === 'undefined') return;

    const storage = remember ? localStorage : sessionStorage;

    storage.setItem(ACCESS_TOKEN_KEY, accessToken);
    storage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    storage.setItem(REMEMBER_KEY, remember ? '1' : '0');

    const otherStorage = remember ? sessionStorage : localStorage;
    otherStorage.removeItem(ACCESS_TOKEN_KEY);
    otherStorage.removeItem(REFRESH_TOKEN_KEY);
    otherStorage.removeItem(REMEMBER_KEY);
  },

  setToken: (accessToken: string, remember = true) => {
    if (typeof window === 'undefined') return;

    const storage = remember ? localStorage : sessionStorage;
    storage.setItem(ACCESS_TOKEN_KEY, accessToken);
    storage.setItem(REMEMBER_KEY, remember ? '1' : '0');
  },

  getToken: () => {
    if (typeof window === 'undefined') return null;

    return (
      localStorage.getItem(ACCESS_TOKEN_KEY) ||
      sessionStorage.getItem(ACCESS_TOKEN_KEY)
    );
  },

  getRefreshToken: () => {
    if (typeof window === 'undefined') return null;

    return (
      localStorage.getItem(REFRESH_TOKEN_KEY) ||
      sessionStorage.getItem(REFRESH_TOKEN_KEY)
    );
  },

  clearToken: () => {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(REMEMBER_KEY);

    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(REMEMBER_KEY);

    // Odstránenie starého kľúča z predchádzajúcej implementácie.
    localStorage.removeItem('auth_token');
  },

  isRemembered: () => {
    if (typeof window === 'undefined') return true;

    return (
      localStorage.getItem(REMEMBER_KEY) === '1' ||
      sessionStorage.getItem(REMEMBER_KEY) !== '0'
    );
  },
};
