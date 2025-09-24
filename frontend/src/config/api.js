const rawBase = (import.meta.env.VITE_API_BASE_URL || '').trim();
const apiBaseUrl = rawBase && rawBase !== '/' ? rawBase.replace(/\/$/, '') : '';

export const getApiBaseUrl = () => apiBaseUrl;

export const apiUrl = (path = '') => {
  const safePath = path.startsWith('/') ? path : `/${path}`;
  return apiBaseUrl ? `${apiBaseUrl}${safePath}` : safePath;
};

export const assetUrl = (path) => {
  if (!path) return path;
  if (/^https?:\/\//i.test(path)) return path;
  return apiUrl(path);
};
