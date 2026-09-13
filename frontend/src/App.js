import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { FullSpinner } from "./components/ui";
import Nav from "./components/Nav";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import StartInterview from "./pages/StartInterview";
import Interview from "./pages/Interview";
import Results from "./pages/Results";
import Recruiter from "./pages/Recruiter";
import Share from "./pages/Share";
import "./App.css";

function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <FullSpinner />;
  if (!user) return <Navigate to="/auth" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

function Shell({ children }) {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Nav />
      <main className="flex-1">{children}</main>
    </div>
  );
}

function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Shell><Landing /></Shell>} />
      <Route path="/auth" element={<Shell><Auth /></Shell>} />
      <Route path="/dashboard" element={<Protected><Shell><Dashboard /></Shell></Protected>} />
      <Route path="/start" element={<Protected><Shell><StartInterview /></Shell></Protected>} />
      <Route path="/interview/:id" element={<Protected><Shell><Interview /></Shell></Protected>} />
      <Route path="/results/:id" element={<Protected><Shell><Results /></Shell></Protected>} />
      <Route path="/recruiter" element={<Protected roles={["recruiter", "admin"]}><Shell><Recruiter /></Shell></Protected>} />
      <Route path="/share/:shareId" element={<Shell><Share /></Shell>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </AuthProvider>
  );
}
