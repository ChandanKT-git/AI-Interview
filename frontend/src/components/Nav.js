import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui";
import { Mic, LayoutDashboard, LogOut, ShieldCheck } from "lucide-react";

export default function Nav() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  const doLogout = async () => {
    await logout();
    navigate("/");
  };

  const isRecruiter = user && (user.role === "recruiter" || user.role === "admin");

  return (
    <header className="sticky top-0 z-50 border-b border-line bg-white/70 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-5 md:px-8 h-16 flex items-center justify-between">
        <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-2.5" data-testid="nav-logo">
          <div className="w-8 h-8 bg-primary text-white flex items-center justify-center rounded-sm">
            <Mic className="w-4 h-4" />
          </div>
          <span className="font-heading font-bold text-lg tracking-tight">Interview<span className="text-primary">Coach</span></span>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {user ? (
            <>
              <Link to="/dashboard">
                <Button variant={pathname === "/dashboard" ? "outline" : "ghost"} className="!px-3" data-testid="nav-dashboard-btn">
                  <LayoutDashboard className="w-4 h-4" />
                  <span className="hidden sm:inline">Dashboard</span>
                </Button>
              </Link>
              {isRecruiter && (
                <Link to="/recruiter">
                  <Button variant={pathname === "/recruiter" ? "outline" : "ghost"} className="!px-3" data-testid="nav-recruiter-btn">
                    <ShieldCheck className="w-4 h-4" />
                    <span className="hidden sm:inline">Recruiter</span>
                  </Button>
                </Link>
              )}
              <div className="hidden md:flex items-center gap-2 ml-2 pl-3 border-l border-line">
                <div className="text-right leading-tight">
                  <div className="text-sm font-medium">{user.name}</div>
                  <div className="text-xs text-muted capitalize">{user.role}</div>
                </div>
              </div>
              <Button variant="ghost" className="!px-3" onClick={doLogout} data-testid="nav-logout-btn">
                <LogOut className="w-4 h-4" />
              </Button>
            </>
          ) : (
            <>
              <Link to="/auth">
                <Button variant="ghost" data-testid="nav-login-btn">Log in</Button>
              </Link>
              <Link to="/auth?mode=register">
                <Button variant="primary" data-testid="nav-signup-btn">Get Started</Button>
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
