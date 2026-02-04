// Auth controller - handles authentication API calls

import { LoginCredentials, SignupData, AuthResponse, User } from '../models/user';
import { useAuthStore } from '../models/authStore';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8096';

class AuthController {
  private getHeaders(includeAuth = false): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (includeAuth) {
      const tokens = useAuthStore.getState().tokens;
      if (tokens?.access_token) {
        headers['Authorization'] = `Bearer ${tokens.access_token}`;
      }
    }
    
    return headers;
  }

  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data: AuthResponse = await response.json();
    useAuthStore.getState().login(data.user, data.tokens);
    return data;
  }

  async signup(data: SignupData): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Signup failed');
    }

    const result: AuthResponse = await response.json();
    useAuthStore.getState().login(result.user, result.tokens);
    return result;
  }

  async refresh(): Promise<boolean> {
    const tokens = useAuthStore.getState().tokens;
    if (!tokens?.refresh_token) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ refresh_token: tokens.refresh_token }),
      });

      if (!response.ok) {
        useAuthStore.getState().logout();
        return false;
      }

      const data = await response.json();
      useAuthStore.getState().setTokens(data.tokens);
      return true;
    } catch {
      useAuthStore.getState().logout();
      return false;
    }
  }

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: this.getHeaders(true),
      });
    } finally {
      useAuthStore.getState().logout();
    }
  }

  async getMe(): Promise<User> {
    const response = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders(true),
    });

    if (!response.ok) {
      throw new Error('Failed to get user info');
    }

    const user: User = await response.json();
    useAuthStore.getState().setUser(user);
    return user;
  }
}

export const authController = new AuthController();
