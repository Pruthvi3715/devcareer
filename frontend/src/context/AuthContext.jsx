import React, { createContext, useState, useEffect } from "react";
import API_BASE from "../utils/api";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [user, setUser] = useState(null);

  // Set default auth headers or handle fetch
  useEffect(() => {
    if (token) {
      localStorage.setItem("token", token);
      fetchUserProfile();
    } else {
      localStorage.removeItem("token");
      setUser(null);
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE}/user/profile`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        // Token might be expired
        setToken(null);
      }
    } catch (e) {
      console.error("Error fetching user profile", e);
    }
  };

  const login = async (email, password) => {
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      setToken(data.access_token);
      return true;
    }
    return false;
  };

  const signup = async (email, password) => {
    const response = await fetch(`${API_BASE}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    return response.ok;
  };

  const logout = () => {
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, signup, logout, fetchUserProfile }}>
      {children}
    </AuthContext.Provider>
  );
};
