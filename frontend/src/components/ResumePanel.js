import React, { useEffect, useRef, useState } from "react";
import api, { formatApiError, getToken } from "../lib/api";
import { Button, Card, Select, Textarea, Spinner, Pill } from "./ui";
import { Upload, FileText, ArrowRight, RefreshCw, Sparkles, CheckCircle2 } from "lucide-react";

const DIFFICULTIES = ["easy", "medium", "hard"];

export default function ResumePanel({ onStart, starting }) {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [mode, setMode] = useState("upload"); // upload | paste
  const [text, setText] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");
  const [replacing, setReplacing] = useState(false);
  const [difficulty, setDifficulty] = useState("medium");
  const [numQ, setNumQ] = useState(5);
  const fileRef = useRef(null);

  useEffect(() => {
    api.get("/resume").then((r) => { setProfile(r.data.profile); }).finally(() => setLoading(false));
  }, []);

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(""); setAnalyzing(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/resume/upload`, {
        method: "POST", headers: { Authorization: `Bearer ${getToken()}` }, body: fd,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(formatApiError(data.detail));
      setProfile(data.profile); setReplacing(false);
    } catch (err) {
      setError(err.message || "Could not analyze the file.");
    } finally {
      setAnalyzing(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const analyzeText = async () => {
    setError(""); setAnalyzing(true);
    try {
      const { data } = await api.post("/resume/text", { text });
      setProfile(data.profile); setReplacing(false); setText("");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) return <div className="flex justify-center py-12"><Spinner className="w-6 h-6 text-primary" /></div>;

  // ---- Import UI (no profile yet, or replacing) ----
  if (!profile || replacing) {
    return (
      <Card className="p-6 md:p-8">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-5 h-5 text-primary" />
          <h3 className="font-heading font-bold text-lg">Import your resume</h3>
        </div>
        <p className="text-sm text-muted mb-5">
          We'll analyze your background and generate interview questions tailored to your real experience.
        </p>

        <div className="grid grid-cols-2 mb-5 border border-line rounded-sm overflow-hidden max-w-xs">
          <button data-testid="resume-mode-upload" onClick={() => setMode("upload")}
            className={`py-2 text-sm font-medium transition-colors ${mode === "upload" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}>Upload file</button>
          <button data-testid="resume-mode-paste" onClick={() => setMode("paste")}
            className={`py-2 text-sm font-medium transition-colors ${mode === "paste" ? "bg-primary text-white" : "bg-white text-muted hover:bg-surface"}`}>Paste text</button>
        </div>

        {error && <div data-testid="resume-error" className="text-sm text-danger bg-danger/5 border border-danger/30 rounded-sm px-3 py-2 mb-4">{error}</div>}

        {mode === "upload" ? (
          <div>
            <input ref={fileRef} type="file" accept=".pdf,.docx,.txt" onChange={handleFile} className="hidden" data-testid="resume-file-input" />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={analyzing}
              data-testid="resume-upload-btn"
              className="w-full border-2 border-dashed border-line rounded-sm py-10 flex flex-col items-center gap-2 text-muted hover:border-primary hover:text-primary transition-colors disabled:opacity-60"
            >
              {analyzing ? <Spinner className="w-6 h-6" /> : <Upload className="w-7 h-7" />}
              <span className="text-sm font-medium">{analyzing ? "Analyzing resume..." : "Click to upload PDF, DOCX or TXT"}</span>
              <span className="text-xs">Max 5MB</span>
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <Textarea testid="resume-text-input" rows={8} value={text} onChange={(e) => setText(e.target.value)}
              placeholder="Paste your resume, or your LinkedIn 'About' + 'Experience' sections here..." />
            <Button variant="primary" className="w-full !py-3" onClick={analyzeText} disabled={analyzing || text.trim().length < 30} data-testid="resume-analyze-btn">
              {analyzing ? <Spinner className="w-4 h-4" /> : <><Sparkles className="w-4 h-4" /> Analyze resume</>}
            </Button>
          </div>
        )}
        {profile && replacing && (
          <button onClick={() => setReplacing(false)} className="text-sm text-muted hover:text-ink mt-4">Cancel</button>
        )}
      </Card>
    );
  }

  // ---- Profile ready ----
  return (
    <div className="space-y-5">
      <Card className="p-6" data-testid="resume-profile">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-2 text-success">
            <CheckCircle2 className="w-5 h-5" />
            <span className="font-heading font-bold text-lg">Resume analyzed</span>
          </div>
          <Button variant="ghost" className="!px-3 !py-1.5" onClick={() => { setReplacing(true); setError(""); }} data-testid="resume-replace-btn">
            <RefreshCw className="w-4 h-4" /> Replace
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Pill className="border-primary/30 text-primary bg-primary/5"><FileText className="w-3.5 h-3.5 mr-1" />{profile.role_guess}</Pill>
          <Pill className="border-line text-muted">{profile.seniority}</Pill>
        </div>
        {profile.summary && <p className="text-sm text-muted leading-relaxed mb-4">{profile.summary}</p>}
        {profile.skills?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {profile.skills.map((s, i) => <Pill key={i} className="border-line text-ink">{s}</Pill>)}
          </div>
        )}
      </Card>

      <Card className="p-6 space-y-5">
        <h3 className="font-heading font-bold text-lg">Tailored interview</h3>
        <div className="grid sm:grid-cols-2 gap-5">
          <Select label="Starting difficulty" testid="resume-difficulty-select" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {DIFFICULTIES.map((d) => <option key={d} value={d} className="capitalize">{d}</option>)}
          </Select>
          <Select label="Number of questions" testid="resume-numq-select" value={numQ} onChange={(e) => setNumQ(e.target.value)}>
            {[1, 3, 5, 7, 10].map((n) => <option key={n} value={n}>{n === 1 ? "1 question (quick)" : `${n} questions`}</option>)}
          </Select>
        </div>
        <p className="text-xs text-muted flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" /> Questions will reference your skills & experience.</p>
        <Button variant="primary" className="w-full !py-3" onClick={() => onStart(difficulty, Number(numQ))} disabled={starting} data-testid="start-resume-interview-btn">
          {starting ? <Spinner className="w-4 h-4" /> : <>Start resume interview <ArrowRight className="w-4 h-4" /></>}
        </Button>
      </Card>
    </div>
  );
}
