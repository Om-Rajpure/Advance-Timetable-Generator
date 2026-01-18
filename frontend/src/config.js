// Automatically use local backend if on localhost/127.0.0.1, ignoring stale .env
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
export const API_BASE_URL = isLocal ? 'http://127.0.0.1:5000' : (import.meta.env.VITE_API_BASE_URL || '');
