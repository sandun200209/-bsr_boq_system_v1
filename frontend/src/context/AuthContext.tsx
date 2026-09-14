import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { api, getAuthToken, setAuthToken } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username_or_email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (roles: string[]) => boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    const currentToken = getAuthToken();
    if (!currentToken) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const u = await api.getMe();
      setUser(u);
    } catch {
      setUser(null);
      setAuthToken(null);
      setTokenState(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();

    // Listen for 401 unauthorized events across components
    const handleUnauthorized = () => {
      setUser(null);
      setAuthToken(null);
      setTokenState(null);
    };

    window.addEventListener('bsr_auth_unauthorized', handleUnauthorized);
    return () => window.removeEventListener('bsr_auth_unauthorized', handleUnauthorized);
  }, []);

  const login = async (username_or_email: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.login(username_or_email, password);
      setAuthToken(res.access_token);
      setTokenState(res.access_token);
      setUser(res.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    api.logout().catch(() => {});
    setAuthToken(null);
    setTokenState(null);
    setUser(null);
  };

  const hasRole = (roles: string[]): boolean => {
    if (!user) return false;
    return roles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        hasRole,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
