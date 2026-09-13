import React, { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "../context/AuthContext";
import { Button, Card, Input, Select, Spinner } from "../components/ui";
import { formatApiError } from "../lib/api";
import { Mic } from "lucide-react";

export default function Auth() {
  const [params] = useSearchParams();
  const [mode, setMode] = useState(params.get("mode") === "register" ? "register" : "login");
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "candidate" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const change = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(form.email, form.password);
      else await register(form);
      navigate("/dashboard");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-5 py-12 md:py-20">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <div className="flex items-center gap-2.5 mb-8 justify-center">
          <div className="w-9 h-9 bg-primary text-white flex items-center justify-center rounded-sm">
            <Mic className="w-4.5 h-4.5" />
          </div>
          <span className="font-heading font-bold text-xl">Interview<span className="text-primary">Coach</span></span>
        </div>

        <Card className="p-7">
          <div className="grid grid-cols-2 mb-6 border border-line rounded-sm overflow-hidden">
            <button
              data-testid="tab-login"
              onClick={() => { setMode("login"); setError(""); }}
              className={`py-2.5 text-sm font-medium transition-colors ${mode === "login" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}
            >
              Log in
            </button>
            <button
              data-testid="tab-register"
              onClick={() => { setMode("register"); setError(""); }}
              className={`py-2.5 text-sm font-medium transition-colors ${mode === "register" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={submit} className="space-y-4">
            {mode === "register" && (
              <Input label="Full name" testid="auth-name" value={form.name} onChange={change("name")} placeholder="Jane Doe" required />
            )}
            <Input label="Email" testid="auth-email" type="email" value={form.email} onChange={change("email")} placeholder="you@example.com" required />
            <Input label="Password" testid="auth-password" type="password" value={form.password} onChange={change("password")} placeholder="••••••••" required minLength={6} />
            {mode === "register" && (
              <Select label="I am a..." testid="auth-role" value={form.role} onChange={change("role")}>
                <option value="candidate">Candidate (practicing interviews)</option>
                <option value="recruiter">Recruiter (building interview packs)</option>
              </Select>
            )}

            {error && (
              <div data-testid="auth-error" className="text-sm text-danger bg-danger/5 border border-danger/30 rounded-sm px-3 py-2">
                {error}
              </div>
            )}

            <Button type="submit" variant="primary" className="w-full !py-3" disabled={busy} data-testid="auth-submit">
              {busy ? <Spinner className="w-4 h-4" /> : mode === "login" ? "Log in" : "Create account"}
            </Button>
          </form>

        </Card>

        <p className="text-center text-xs text-muted mt-6">
          By continuing you agree to practice hard. <Link to="/" className="underline">Back home</Link>
        </p>
      </motion.div>
    </div>
  );
}
