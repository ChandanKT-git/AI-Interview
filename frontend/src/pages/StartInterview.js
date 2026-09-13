import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import api, { formatApiError } from "../lib/api";
import { Button, Card, Select, Spinner, Pill, fadeUp } from "../components/ui";
import ResumePanel from "../components/ResumePanel";
import { Briefcase, Package, ArrowRight, Layers, FileText } from "lucide-react";

const INDUSTRIES = ["Technology", "Finance", "Healthcare", "E-commerce", "Consulting", "Gaming", "Education"];
const DIFFICULTIES = ["easy", "medium", "hard"];

export default function StartInterview() {
  const [tab, setTab] = useState("role");
  const [roles, setRoles] = useState([]);
  const [packs, setPacks] = useState([]);
  const [engine, setEngine] = useState("");
  const [form, setForm] = useState({ role: "", industry: "Technology", difficulty: "medium", num_questions: 5 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    api.get("/meta/roles").then((r) => {
      setRoles(r.data.roles);
      setEngine(r.data.ai_engine);
      setForm((f) => ({ ...f, role: r.data.roles[0] }));
    });
    api.get("/packs").then((r) => setPacks(r.data.packs)).catch(() => {});
  }, []);

  const startRole = async () => {
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/interviews", {
        mode: "role", role: form.role, industry: form.industry,
        difficulty: form.difficulty, num_questions: Number(form.num_questions),
      });
      navigate(`/interview/${data.interview_id}`);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
      setBusy(false);
    }
  };

  const startPack = async (packId) => {
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/interviews", { mode: "pack", pack_id: packId });
      navigate(`/interview/${data.interview_id}`);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
      setBusy(false);
    }
  };

  const startResume = async (difficulty, numQuestions) => {
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/interviews", { mode: "resume", difficulty, num_questions: numQuestions });
      navigate(`/interview/${data.interview_id}`);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
      setBusy(false);
    }
  };

  const change = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <div className="max-w-3xl mx-auto px-5 md:px-8 py-10">
      <motion.div {...fadeUp}>
        <div className="overline mb-1">New session</div>
        <h1 className="font-heading font-extrabold text-3xl sm:text-4xl tracking-tight mb-2">Set up your interview</h1>
        <p className="text-muted mb-6">
          AI engine:{" "}
          <Pill className={engine === "groq" ? "border-success/40 text-success bg-success/5" : "border-line text-muted"}>
            {engine === "groq" ? "Groq (live)" : "Local fallback"}
          </Pill>
        </p>

        <div className="grid grid-cols-3 mb-6 border border-line rounded-sm overflow-hidden max-w-lg">
          <button data-testid="tab-role" onClick={() => setTab("role")}
            className={`py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${tab === "role" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}>
            <Briefcase className="w-4 h-4" /> By role
          </button>
          <button data-testid="tab-resume" onClick={() => setTab("resume")}
            className={`py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-colors border-x border-line ${tab === "resume" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}>
            <FileText className="w-4 h-4" /> Resume
          </button>
          <button data-testid="tab-pack" onClick={() => setTab("pack")}
            className={`py-2.5 text-sm font-medium flex items-center justify-center gap-2 transition-colors ${tab === "pack" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}>
            <Package className="w-4 h-4" /> Packs
          </button>
        </div>

        {error && <div data-testid="start-error" className="text-sm text-danger bg-danger/5 border border-danger/30 rounded-sm px-3 py-2 mb-4">{error}</div>}

        {tab === "resume" ? (
          <ResumePanel onStart={startResume} starting={busy} />
        ) : tab === "role" ? (
          <Card className="p-6 space-y-5">
            <Select label="Role" testid="role-select" value={form.role} onChange={change("role")}>
              {roles.map((r) => <option key={r} value={r}>{r}</option>)}
            </Select>
            <div className="grid sm:grid-cols-2 gap-5">
              <Select label="Industry" testid="industry-select" value={form.industry} onChange={change("industry")}>
                {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
              </Select>
              <Select label="Starting difficulty" testid="difficulty-select" value={form.difficulty} onChange={change("difficulty")}>
                {DIFFICULTIES.map((d) => <option key={d} value={d} className="capitalize">{d}</option>)}
              </Select>
            </div>
            <Select label="Number of questions" testid="numq-select" value={form.num_questions} onChange={change("num_questions")}>
              {[1, 3, 5, 7, 10].map((n) => <option key={n} value={n}>{n === 1 ? "1 question (quick)" : `${n} questions`}</option>)}
            </Select>
            <p className="text-xs text-muted flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" /> Difficulty adapts automatically based on your answers.
            </p>
            <Button variant="primary" className="w-full !py-3" onClick={startRole} disabled={busy} data-testid="begin-interview-btn">
              {busy ? <Spinner className="w-4 h-4" /> : <>Begin interview <ArrowRight className="w-4 h-4" /></>}
            </Button>
          </Card>
        ) : (
          <div className="space-y-8">
            {packs.length === 0 ? (
              <Card className="p-10 text-center text-muted">No interview packs available yet.</Card>
            ) : (
              <>
                {["tech", "hr", "behavioural"].map((cat) => {
                  const items = packs.filter((p) => p.is_curated && p.category === cat);
                  if (items.length === 0) return null;
                  const labels = { tech: "Technical roles", hr: "HR screening", behavioural: "Behavioural" };
                  return (
                    <div key={cat}>
                      <div className="flex items-center gap-2 mb-3">
                        <h3 className="font-heading font-bold text-lg">{labels[cat]}</h3>
                        <Pill className="border-primary/30 text-primary bg-primary/5">Curated</Pill>
                      </div>
                      <div className="grid sm:grid-cols-2 gap-3">
                        {items.map((p) => <PackCard key={p.pack_id} p={p} onStart={startPack} busy={busy} />)}
                      </div>
                    </div>
                  );
                })}
                {packs.filter((p) => !p.is_curated).length > 0 && (
                  <div>
                    <h3 className="font-heading font-bold text-lg mb-3">Community packs</h3>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {packs.filter((p) => !p.is_curated).map((p) => <PackCard key={p.pack_id} p={p} onStart={startPack} busy={busy} />)}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </motion.div>
    </div>
  );
}

function PackCard({ p, onStart, busy }) {
  return (
    <Card className="p-5 flex flex-col justify-between gap-4 h-full" hover data-testid={`pack-${p.pack_id}`}>
      <div className="min-w-0">
        <div className="font-heading font-bold text-lg">{p.title}</div>
        <div className="text-sm text-muted mt-0.5">{p.description || `${p.role} · ${p.industry}`}</div>
        <div className="flex flex-wrap items-center gap-2 mt-3">
          <Pill className="border-line text-muted">{p.role}</Pill>
          <Pill className="border-line text-muted capitalize">{p.difficulty}</Pill>
          <Pill className="border-line text-muted">{p.questions?.length} Q</Pill>
        </div>
      </div>
      <Button variant="primary" className="!py-2.5 w-full" onClick={() => onStart(p.pack_id)} disabled={busy} data-testid={`start-pack-${p.pack_id}`}>
        One-click practice
      </Button>
    </Card>
  );
}
