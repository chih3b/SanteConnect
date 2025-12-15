import React, { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

const API_PATIENT = "http://localhost:8000";
const API_DOCTOR = "http://localhost:8003";

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [userRole, setUserRole] = useState(localStorage.getItem("userRole"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token && userRole) {
      fetchUser();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, userRole]);

  const fetchUser = async () => {
    try {
      const apiBase = userRole === "doctor" ? API_DOCTOR : API_PATIENT;
      const endpoint =
        userRole === "doctor" ? "/auth/doctor/me" : "/auth/me";

      const response = await fetch(`${apiBase}${endpoint}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setUser({ ...data.user, role: userRole });
      } else {
        logout();
      }
    } catch (error) {
      console.error("Auth error:", error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, role = "patient") => {
    const apiBase = role === "doctor" ? API_DOCTOR : API_PATIENT;
    const endpoint = role === "doctor" ? "/auth/doctor/login" : "/auth/login";

    const response = await fetch(`${apiBase}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem("token", data.token);
      localStorage.setItem("userRole", role);
      setToken(data.token);
      setUserRole(role);
      setUser({ ...data.user, role });
      return { success: true };
    }

    return { success: false, error: data.detail || "Login failed" };
  };

  const register = async (
    email,
    password,
    name,
    role = "patient",
    extraData = {}
  ) => {
    const apiBase = role === "doctor" ? API_DOCTOR : API_PATIENT;
    const endpoint =
      role === "doctor" ? "/auth/doctor/register" : "/auth/register";

    const body =
      role === "doctor"
        ? { email, password, name, ...extraData }
        : { email, password, name };

    const response = await fetch(`${apiBase}${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (response.ok) {
      localStorage.setItem("token", data.token);
      localStorage.setItem("userRole", role);
      setToken(data.token);
      setUserRole(role);
      setUser({ ...data.user, role });
      return { success: true };
    }

    return { success: false, error: data.detail || "Registration failed" };
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userRole");
    setToken(null);
    setUserRole(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, token, userRole, loading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
};
