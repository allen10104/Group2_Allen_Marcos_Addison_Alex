// This file contains the API client configuration for the SyncUp frontend application. 
// It sets up an Axios instance with a base URL and handles token management, 
// including automatic token refreshing when the access token expires.
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const client = axios.create({ baseURL: API_URL });

// Using localstorage instead of sessionstorage because we want the token to persist
// between each tab

// Retrieves the access and refresh tokens from local storage.
function getTokens() {
  return {
    accessToken: localStorage.getItem("accessToken"),
    refreshToken: localStorage.getItem("refreshToken"),
  };
}
 
// Stores the access and refresh tokens in local storage.
export function setTokens({ access_token, refresh_token }) {
  localStorage.setItem("accessToken", access_token);
  localStorage.setItem("refreshToken", refresh_token);
}

// Clears the access and refresh tokens from local storage.
export function clearTokens() {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
}

// Intercepts outgoing requests to add the Authorization header with the access token if it exists.
client.interceptors.request.use((config) => {
  const { accessToken } = getTokens();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let refreshPromise = null;

// Intercepts incoming responses to handle 401 Unauthorized errors.
// If a 401 error occurs and a refresh token is available, it attempts to refresh the access token.
// If the refresh is successful, it retries the original request with the new access token.
// If the refresh fails, it clears the tokens and redirects the user to the login page. 
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const { refreshToken } = getTokens();

    if (error.response?.status !== 401 || originalRequest._retried || !refreshToken) {
      return Promise.reject(error);
    }
    originalRequest._retried = true;

    try {
      if (!refreshPromise) {
        refreshPromise = axios
          .post(`${API_URL}/auth/refresh`, { refresh_token: refreshToken })
          .finally(() => {
            refreshPromise = null;
          });
      }
      const { data } = await refreshPromise;
      setTokens(data);
      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      return client(originalRequest);
    } catch (refreshError) {
      clearTokens();
      window.location.href = "/login";
      return Promise.reject(refreshError);
    }
  }
);