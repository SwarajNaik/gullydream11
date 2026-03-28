"use client";

import { createContext, useCallback, useContext, useMemo } from "react";

interface AuthUser {
  user_id: number;
  email: string;
  username: string;
  display_name: string;
  role: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  login: (token: string, user: AuthUser) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Read from localStorage (client-side only)
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const userStr = typeof window !== "undefined" ? localStorage.getItem("auth_user") : null;
  const user: AuthUser | null = userStr ? JSON.parse(userStr) : null;

  const login = useCallback((newToken: string, newUser: AuthUser) => {
    localStorage.setItem("access_token", newToken);
    localStorage.setItem("auth_user", JSON.stringify(newUser));
    window.location.href = "/home";
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("auth_user");
    window.location.href = "/login";
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      login,
      logout,
      isAuthenticated: !!token && !!user,
      isAdmin: user?.role === "ADMIN",
    }),
    [user, token, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
