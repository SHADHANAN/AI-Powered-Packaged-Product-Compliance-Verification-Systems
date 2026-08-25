/**
 * Centralized JWT token storage helpers.
 *
 * All localStorage access for auth tokens is isolated here.
 * Components must NEVER read/write localStorage directly for auth.
 */

const TOKEN_KEY = 'access_token';

/** Retrieve the stored JWT, or null if absent. */
export const getToken = () => localStorage.getItem(TOKEN_KEY);

/** Persist a JWT to localStorage. */
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token);

/** Remove the JWT from localStorage. */
export const removeToken = () => localStorage.removeItem(TOKEN_KEY);

/** Returns true if a token is currently stored. */
export const hasToken = () => !!localStorage.getItem(TOKEN_KEY);
