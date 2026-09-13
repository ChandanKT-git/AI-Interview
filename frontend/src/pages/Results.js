import React, { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, LabelList } from "recharts";
import api from "../lib/api";
import { Button, Card, Spinner, Pill, fadeUp } from "../components/ui";
import {
  Trophy, ThumbsUp, AlertTriangle, Lightbulb, BookOpen, RotateCcw,
  LayoutDashboard, ChevronDown, Share2, Download, Check, Mic,
} from "lucide-react";

const color = (s) => (s >= 75 ? "#198754" : s >= 50 ? "#002FA7" : "#DC3545");

export function ResultView({ iv, shared = false }) {
  const [open, setOpen] = useState(null);
  const [copied, setCopied] = useState(false);
  const s = iv.scores;
  const chartData = [
    { name: "Communication", value: s.communication },
    { name: "Technical", value: s.technical },
    { name: "Confidence", value: s.confidence },
  ];

  const copyLink = async () => {
    const link = `${window.location.origin}/share/${iv.share_id}`;
    try { await navigator.clipboard.writeText(link); } catch {}
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto px-5 md:px-8 py-10 print-area">
      <motion.div {...fadeUp}>
        {shared && (
          <div className="flex items-center gap-2 mb-5 no-print">
            <div className="w-7 h-7 bg-primary text-white flex items-center justify-center rounded-sm"><Mic className="w-4 h-4" /></div>
            <span className="font-heading font-bold">Interview<span className="text-primary">Coach</span> · Shared report</span>
          </div>
        )}

        <Card className="p-8 md:p-10 mb-6 text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1" style={{ background: color(s.overall) }} />
          {iv.candidate_name && <div className="text-sm text-muted mb-1">{iv.candidate_name}</div>}
          <div className="overline mb-2">{iv.pack_title || iv.role} · {iv.industry}</div>
          <div className="flex items-center justify-center gap-2 mb-1">
            <Trophy className="w-6 h-6" style={{ color: color(s.overall) }} />
            <span className="overline !text-muted">Overall score</span>
          </div>
          <div data-testid="overall-score" className="font-heading font-extrabold text-7xl tracking-tight" style={{ color: color(s.overall) }}>
            {s.overall}
          </div>
          <p className="text-muted mt-3 max-w-2xl mx-auto" data-testid="summary-text">{iv.summary}</p>
        </Card>

        <Card className="p-6 mb-6">
          <h3 className="font-heading font-bold text-lg mb-4">Score breakdown</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 40 }}>
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis type="category" dataKey="name" width={110} tick={{ fill: "#111", fontSize: 13 }} axisLine={false} tickLine={false} />
              <Bar dataKey="value" radius={[0, 2, 2, 0]} barSize={26}>
                {chartData.map((e, i) => <Cell key={i} fill={color(e.value)} />)}
                <LabelList dataKey="value" position="right" fill="#111" fontSize={13} fontWeight={600} />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-6 mb-6">
          <h3 className="font-heading font-bold text-lg mb-4">Question by question</h3>
          <div className="space-y-2">
            {iv.items.map((it, i) => (
              <div key={i} className="border border-line rounded-sm" data-testid={`qa-${i}`}>
                <button onClick={() => setOpen(open === i ? null : i)} className="w-full flex items-center justify-between gap-4 p-4 text-left hover:bg-surface transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="w-7 h-7 shrink-0 rounded-sm bg-surface flex items-center justify-center text-xs font-semibold">{i + 1}</span>
                    <span className="text-sm font-medium truncate">{it.question}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="font-heading font-bold" style={{ color: color(it.evaluation.overall) }}>{it.evaluation.overall}</span>
                    <ChevronDown className={`w-4 h-4 text-muted transition-transform ${open === i ? "rotate-180" : ""}`} />
                  </div>
                </button>
                {open === i && (
                  <div className="px-4 pb-4 pt-1 border-t border-line space-y-3">
                    <div className="text-sm text-muted bg-surface rounded-sm p-3"><span className="font-medium text-ink">Your answer: </span>{it.answer || <em>No answer</em>}</div>
                    <div className="grid grid-cols-3 gap-3 text-center text-xs">
                      <Metric label="Comm" v={it.evaluation.communication} />
                      <Metric label="Tech" v={it.evaluation.technical} />
                      <Metric label="Conf" v={it.evaluation.confidence} />
                    </div>
                    {it.evaluation.strengths?.length > 0 && <MiniList icon={ThumbsUp} c="text-success" items={it.evaluation.strengths} />}
                    {it.evaluation.weaknesses?.length > 0 && <MiniList icon={AlertTriangle} c="text-warn" items={it.evaluation.weaknesses} />}
                    {it.evaluation.tips?.length > 0 && <MiniList icon={Lightbulb} c="text-primary" items={it.evaluation.tips} />}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        {iv.resources?.length > 0 && (
          <Card className="p-6 mb-6">
            <h3 className="font-heading font-bold text-lg mb-4 flex items-center gap-2"><BookOpen className="w-5 h-5 text-primary" /> Suggested resources</h3>
            <ul className="space-y-2">
              {iv.resources.map((r, i) => <li key={i} className="text-sm flex items-center gap-2"><span className="w-1.5 h-1.5 bg-primary rounded-full" /> {r}</li>)}
            </ul>
          </Card>
        )}

        <div className="flex flex-wrap gap-3 no-print">
          {!shared && (
            <>
              <Button variant="outline" className="!px-5 !py-3" onClick={copyLink} data-testid="share-link-btn">
                {copied ? <><Check className="w-4 h-4 text-success" /> Link copied!</> : <><Share2 className="w-4 h-4" /> Copy share link</>}
              </Button>
              <Button variant="outline" className="!px-5 !py-3" onClick={() => window.print()} data-testid="download-pdf-btn">
                <Download className="w-4 h-4" /> Download PDF
              </Button>
              <Link to="/start"><Button variant="primary" className="!px-5 !py-3" data-testid="practice-again-btn"><RotateCcw className="w-4 h-4" /> Practice again</Button></Link>
              <Link to="/dashboard"><Button variant="ghost" className="!px-5 !py-3" data-testid="back-dashboard-btn"><LayoutDashboard className="w-4 h-4" /> Dashboard</Button></Link>
            </>
          )}
          {shared && (
            <>
              <Button variant="outline" className="!px-5 !py-3" onClick={() => window.print()} data-testid="download-pdf-btn"><Download className="w-4 h-4" /> Download PDF</Button>
              <Link to="/auth?mode=register"><Button variant="primary" className="!px-5 !py-3" data-testid="share-signup-btn">Practice your own interview <RotateCcw className="w-4 h-4" /></Button></Link>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [iv, setIv] = useState(null);

  useEffect(() => {
    api.get(`/interviews/${id}`).then((r) => {
      if (r.data.status !== "completed") { navigate(`/interview/${id}`, { replace: true }); return; }
      setIv(r.data);
    }).catch(() => setIv(false));
  }, [id, navigate]);

  if (iv === null) return <div className="flex justify-center py-24"><Spinner className="w-7 h-7 text-primary" /></div>;
  if (iv === false) return <div className="text-center py-20 text-danger">Results not found.</div>;
  return <ResultView iv={iv} />;
}

function Metric({ label, v }) {
  return (
    <div className="border border-line rounded-sm py-2">
      <div className="font-heading font-bold text-lg" style={{ color: color(v) }}>{v}</div>
      <div className="text-muted">{label}</div>
    </div>
  );
}

function MiniList({ icon: Icon, c, items }) {
  return (
    <div>
      <div className={`flex items-center gap-1.5 text-xs font-semibold mb-1 ${c}`}><Icon className="w-3.5 h-3.5" /></div>
      <ul className="space-y-1">{items.map((it, i) => <li key={i} className="text-sm text-ink flex gap-2"><span className="text-muted">·</span> {it}</li>)}</ul>
    </div>
  );
}
