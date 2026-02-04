/**
 * Auth Context - Provides authentication state and methods to the app
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import {
  User,
  TokenResponse,
  LoginCredentials,
  RegisterData,
  authApi,
  tokenStorage,
  getValidAccessToken,
} from '../services/auth';

// Context types
interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAdmin: boolean;
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: tokenStorage.getUser(),
    isAuthenticated: !!tokenStorage.getAccessToken(),
    isLoading: true,
    isAdmin: tokenStorage.getUser()?.role === 'admin',
  });

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = await getValidAccessToken();
      
      if (token) {
        try {
          const user = await authApi.getMe();
          tokenStorage.setUser(user);
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
            isAdmin: user.role === 'admin',
          });
        } catch (error) {
          // Token invalid, clear everything
          tokenStorage.clear();
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            isAdmin: false,
          });
        }
      } else {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isAdmin: false,
        });
      }
    };

    initAuth();
  }, []);

  // Login
  const login = useCallback(async (credentials: LoginCredentials) => {
    const tokens = await authApi.login(credentials);
    tokenStorage.setTokens(tokens);
    
    const user = await authApi.getMe();
    tokenStorage.setUser(user);
    
    setState({
      user,
      isAuthenticated: true,
      isLoading: false,
      isAdmin: user.role === 'admin',
    });
  }, []);

  // Register
  const register = useCallback(async (data: RegisterData) => {
    await authApi.register(data);
    // Auto-login after registration
    await login({ email: data.email, password: data.password });
  }, [login]);

  // Logout
  const logout = useCallback(() => {
    tokenStorage.clear();
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isAdmin: false,
    });
  }, []);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    const token = await getValidAccessToken();
    if (token) {
      const user = await authApi.getMe();
      tokenStorage.setUser(user);
      setState(prev => ({
        ...prev,
        user,
        isAdmin: user.role === 'admin',
      }));
    }
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Export context for testing
export { AuthContext };
