/**
 * Auth Service - Handles authentication API calls and token management
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8096';

// Token storage keys
const ACCESS_TOKEN_KEY = 'noon_access_token';
const REFRESH_TOKEN_KEY = 'noon_refresh_token';
const USER_KEY = 'noon_user';

// Types
export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: 'user' | 'admin';
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthError {
  detail: string | { msg: string }[];
}

// Token management
export const tokenStorage = {
  getAccessToken: (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  getUser: (): User | null => {
    const data = localStorage.getItem(USER_KEY);
    return data ? JSON.parse(data) : null;
  },
  
  setTokens: (tokens: TokenResponse): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  },
  
  setUser: (user: User): void => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  
  clear: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

// API helpers
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(
      typeof error.detail === 'string' 
        ? error.detail 
        : error.detail?.[0]?.msg || 'Request failed'
    );
  }
  return response.json();
}

// Auth API calls
export const authApi = {
  async register(data: RegisterData): Promise<User> {
    const response = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<User>(response);
  },

  async login(credentials: LoginCredentials): Promise<TokenResponse> {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    return handleResponse<TokenResponse>(response);
  },

  async getMe(): Promise<User> {
    const token = tokenStorage.getAccessToken();
    if (!token) throw new Error('Not authenticated');
    
    const response = await fetch(`${API_BASE}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return handleResponse<User>(response);
  },

  async refresh(): Promise<TokenResponse> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token');
    
    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    return handleResponse<TokenResponse>(response);
  },
};

// Token refresh logic
let refreshPromise: Promise<TokenResponse> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  // Deduplicate concurrent refresh requests
  if (refreshPromise) {
    const tokens = await refreshPromise;
    return tokens.access_token;
  }
  
  try {
    refreshPromise = authApi.refresh();
    const tokens = await refreshPromise;
    tokenStorage.setTokens(tokens);
    return tokens.access_token;
  } catch (error) {
    tokenStorage.clear();
    return null;
  } finally {
    refreshPromise = null;
  }
}

// Check if token is expired (with 30s buffer)
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to ms
    return Date.now() > exp - 30000; // 30s buffer
  } catch {
    return true;
  }
}

// Get valid access token (refresh if needed)
export async function getValidAccessToken(): Promise<string | null> {
  const token = tokenStorage.getAccessToken();
  if (!token) return null;
  
  if (isTokenExpired(token)) {
    return refreshAccessToken();
  }
  
  return token;
}
