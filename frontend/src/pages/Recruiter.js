import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import api, { formatApiError } from "../lib/api";
import { Button, Card, Input, Textarea, Select, Spinner, Pill, fadeUp } from "../components/ui";
import { Plus, Trash2, Pencil, Package, X, Save } from "lucide-react";

const DIFFICULTIES = ["easy", "medium", "hard"];
const blankQ = () => ({ question: "", category: "technical", difficulty: "medium" });
const blankPack = () => ({ title: "", role: "", industry: "Technology", description: "", difficulty: "medium", questions: [blankQ()] });

export default function Recruiter() {
  const [packs, setPacks] = useState(null);
  const [editing, setEditing] = useState(null); // null | pack object (with optional pack_id)
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = () => api.get("/packs/mine").then((r) => setPacks(r.data.packs)).catch(() => setPacks([]));
  useEffect(() => { load(); }, []);

  const save = async () => {
    setError("");
    if (!editing.title.trim() || !editing.role.trim()) { setError("Title and role are required."); return; }
    const valid = editing.questions.filter((q) => q.question.trim());
    if (valid.length === 0) { setError("Add at least one question."); return; }
    setBusy(true);
    try {
      const payload = { ...editing, questions: valid };
      if (editing.pack_id) await api.put(`/packs/${editing.pack_id}`, payload);
      else await api.post("/packs", payload);
      setEditing(null);
      load();
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (pid) => {
    await api.delete(`/packs/${pid}`);
    load();
  };

  const setQ = (i, k, v) => {
    const qs = [...editing.questions];
    qs[i] = { ...qs[i], [k]: v };
    setEditing({ ...editing, questions: qs });
  };

  return (
    <div className="max-w-4xl mx-auto px-5 md:px-8 py-10">
      <motion.div {...fadeUp} className="flex items-end justify-between gap-4 mb-8">
        <div>
          <div className="overline mb-1">Recruiter studio</div>
          <h1 className="font-heading font-extrabold text-3xl sm:text-4xl tracking-tight">Custom interview packs</h1>
          <p className="text-muted mt-1">Design question sets that candidates can practice against.</p>
        </div>
        {!editing && (
          <Button variant="primary" className="!px-5 !py-3 shrink-0" onClick={() => { setEditing(blankPack()); setError(""); }} data-testid="new-pack-btn">
            <Plus className="w-4 h-4" /> New pack
          </Button>
        )}
      </motion.div>

      {editing ? (
        <Card className="p-6 md:p-8" data-testid="pack-editor">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-heading font-bold text-xl">{editing.pack_id ? "Edit pack" : "Create pack"}</h2>
            <button onClick={() => setEditing(null)} className="text-muted hover:text-ink" data-testid="cancel-edit-btn"><X className="w-5 h-5" /></button>
          </div>

          <div className="space-y-5">
            <Input label="Pack title" testid="pack-title" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} placeholder="Senior Backend Engineer Screen" />
            <div className="grid sm:grid-cols-2 gap-5">
              <Input label="Target role" testid="pack-role" value={editing.role} onChange={(e) => setEditing({ ...editing, role: e.target.value })} placeholder="Backend Developer" />
              <Input label="Industry" testid="pack-industry" value={editing.industry} onChange={(e) => setEditing({ ...editing, industry: e.target.value })} placeholder="Technology" />
            </div>
            <Select label="Difficulty" testid="pack-difficulty" value={editing.difficulty} onChange={(e) => setEditing({ ...editing, difficulty: e.target.value })}>
              {DIFFICULTIES.map((d) => <option key={d} value={d} className="capitalize">{d}</option>)}
            </Select>
            <Textarea label="Description" testid="pack-description" rows={2} value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} placeholder="Short summary candidates will see" />

            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Questions</span>
                <Button variant="outline" className="!px-3 !py-1.5" onClick={() => setEditing({ ...editing, questions: [...editing.questions, blankQ()] })} data-testid="add-question-btn">
                  <Plus className="w-4 h-4" /> Add question
                </Button>
              </div>
              <div className="space-y-3">
                {editing.questions.map((qq, i) => (
                  <div key={i} className="border border-line rounded-sm p-4" data-testid={`question-row-${i}`}>
                    <div className="flex items-start gap-3">
                      <span className="w-7 h-7 shrink-0 rounded-sm bg-surface flex items-center justify-center text-xs font-semibold mt-0.5">{i + 1}</span>
                      <div className="flex-1 space-y-3">
                        <Textarea testid={`question-text-${i}`} rows={2} value={qq.question} onChange={(e) => setQ(i, "question", e.target.value)} placeholder="Type the interview question..." />
                        <div className="flex gap-3">
                          <Select testid={`question-difficulty-${i}`} value={qq.difficulty} onChange={(e) => setQ(i, "difficulty", e.target.value)} className="max-w-[140px]">
                            {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
                          </Select>
                          <Select testid={`question-category-${i}`} value={qq.category} onChange={(e) => setQ(i, "category", e.target.value)} className="max-w-[160px]">
                            <option value="technical">technical</option>
                            <option value="behavioural">behavioural</option>
                            <option value="hr">hr</option>
                          </Select>
                        </div>
                      </div>
                      {editing.questions.length > 1 && (
                        <button onClick={() => setEditing({ ...editing, questions: editing.questions.filter((_, j) => j !== i) })} className="text-muted hover:text-danger mt-1" data-testid={`remove-question-${i}`}>
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {error && <div data-testid="pack-error" className="text-sm text-danger bg-danger/5 border border-danger/30 rounded-sm px-3 py-2">{error}</div>}

            <div className="flex gap-3">
              <Button variant="primary" className="!px-5 !py-3" onClick={save} disabled={busy} data-testid="save-pack-btn">
                {busy ? <Spinner className="w-4 h-4" /> : <><Save className="w-4 h-4" /> Save pack</>}
              </Button>
              <Button variant="outline" className="!px-5 !py-3" onClick={() => setEditing(null)}>Cancel</Button>
            </div>
          </div>
        </Card>
      ) : packs === null ? (
        <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-primary" /></div>
      ) : packs.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="w-12 h-12 bg-primary/10 text-primary rounded-sm flex items-center justify-center mx-auto mb-4"><Package className="w-6 h-6" /></div>
          <h2 className="font-heading font-bold text-xl mb-1">No packs yet</h2>
          <p className="text-muted mb-5">Create your first custom interview pack for candidates.</p>
          <Button variant="primary" className="!px-5 !py-3" onClick={() => setEditing(blankPack())} data-testid="empty-new-pack-btn"><Plus className="w-4 h-4" /> New pack</Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {packs.map((p) => (
            <Card key={p.pack_id} className="p-5 flex items-center justify-between gap-4" data-testid={`mypack-${p.pack_id}`}>
              <div className="min-w-0">
                <div className="font-heading font-bold text-lg">{p.title}</div>
                <div className="text-sm text-muted truncate">{p.description || `${p.role} · ${p.industry}`}</div>
                <div className="flex items-center gap-2 mt-2">
                  <Pill className="border-line text-muted">{p.role}</Pill>
                  <Pill className="border-line text-muted capitalize">{p.difficulty}</Pill>
                  <Pill className="border-line text-muted">{p.questions?.length} Q</Pill>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button variant="outline" className="!px-3 !py-2" onClick={() => { setEditing({ ...p }); setError(""); }} data-testid={`edit-pack-${p.pack_id}`}><Pencil className="w-4 h-4" /></Button>
                <Button variant="outline" className="!px-3 !py-2 hover:!border-danger hover:!text-danger" onClick={() => remove(p.pack_id)} data-testid={`delete-pack-${p.pack_id}`}><Trash2 className="w-4 h-4" /></Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
