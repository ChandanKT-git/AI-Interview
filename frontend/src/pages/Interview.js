import React, { useEffect, useRef, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import api, { formatApiError, getToken } from "../lib/api";
import { Button, Card, Textarea, Spinner, Pill, ScoreBar } from "../components/ui";
import {
  Volume2, VolumeX, Mic, MicOff, Send, ArrowRight, CheckCircle2,
  ThumbsUp, AlertTriangle, Lightbulb,
} from "lucide-react";

const SpeechRecognition = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);

export default function Interview() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [iv, setIv] = useState(null);
  const [q, setQ] = useState(null);
  const [answer, setAnswer] = useState("");
  const [progress, setProgress] = useState({ answered: 0, total: 0 });
  const [lastEval, setLastEval] = useState(null);
  const [nextQ, setNextQ] = useState(null);
  const [finished, setFinished] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const [speaking, setSpeaking] = useState(false);
  const [listening, setListening] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [cloudVoice, setCloudVoice] = useState(false);
  const recognitionRef = useRef(null);
  const baseAnswerRef = useRef("");
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const BACKEND = process.env.REACT_APP_BACKEND_URL;

  const speak = useCallback(async (text) => {
    if (!text) return;
    if (cloudVoice) {
      try {
        setSpeaking(true);
        const res = await fetch(`${BACKEND}/api/voice/tts`, {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
          body: JSON.stringify({ text }),
        });
        if (!res.ok) throw new Error("tts");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        if (audioRef.current) { audioRef.current.pause(); }
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => setSpeaking(false);
        audio.onerror = () => setSpeaking(false);
        await audio.play();
        return;
      } catch {
        setSpeaking(false);
        setCloudVoice(false); // OpenAI voice unavailable (e.g. no quota) — use browser voice
      }
    }
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.onend = () => setSpeaking(false);
      u.onerror = () => setSpeaking(false);
      setSpeaking(true);
      window.speechSynthesis.speak(u);
    }
  }, [cloudVoice, BACKEND]);

  const stopSpeak = useCallback(() => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    setSpeaking(false);
  }, []);

  useEffect(() => {
    api.get("/voice/status").then((r) => setCloudVoice(!!r.data.enabled)).catch(() => {});
  }, []);

  useEffect(() => {
    api.get(`/interviews/${id}`)
      .then((r) => {
        const data = r.data;
        if (data.status === "completed") {
          navigate(`/results/${id}`, { replace: true });
          return;
        }
        setIv(data);
        setQ(data.current_question);
        setProgress({ answered: data.items.length, total: data.num_questions });
        setTimeout(() => speak(data.current_question?.question), 400);
      })
      .catch(() => setError("Could not load this interview."));
    return () => stopSpeak();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const startCloudRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size === 0) { setTranscribing(false); return; }
        setTranscribing(true);
        try {
          const fd = new FormData();
          fd.append("file", blob, "answer.webm");
          const res = await fetch(`${BACKEND}/api/voice/stt`, { method: "POST", headers: { Authorization: `Bearer ${getToken()}` }, body: fd });
          const data = await res.json();
          if (data.text) setAnswer((prev) => (prev ? prev + " " : "") + data.text);
        } catch {
          setError("Could not transcribe audio. Please type your answer.");
        } finally {
          setTranscribing(false);
        }
      };
      mediaRecorderRef.current = mr;
      mr.start();
      setListening(true);
    } catch {
      setError("Microphone access was denied. You can type your answer instead.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    } else if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setListening(false);
  };

  const toggleListen = () => {
    if (listening) { stopRecording(); return; }
    setError("");
    // Prefer the free browser speech recognition (works instantly). Fall back to
    // OpenAI Whisper (cloud) only for browsers that don't support it.
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = "en-US";
      baseAnswerRef.current = answer ? answer + " " : "";
      rec.onresult = (e) => {
        let transcript = "";
        for (let i = 0; i < e.results.length; i++) transcript += e.results[i][0].transcript;
        setAnswer(baseAnswerRef.current + transcript);
      };
      rec.onend = () => setListening(false);
      rec.onerror = () => setListening(false);
      recognitionRef.current = rec;
      rec.start();
      setListening(true);
      return;
    }
    if (cloudVoice && navigator.mediaDevices?.getUserMedia) {
      startCloudRecording();
      return;
    }
    setError("Voice input isn't supported in this browser. You can type your answer instead.");
  };

  const submit = async () => {
    if (!answer.trim()) { setError("Please provide an answer (type or use the mic)."); return; }
    setSubmitting(true); setError("");
    stopSpeak();
    if (listening) stopRecording();
    try {
      const { data } = await api.post(`/interviews/${id}/answer`, { answer });
      setLastEval(data.evaluation);
      setProgress(data.progress);
      if (data.finished) setFinished(true);
      else setNextQ(data.next_question);
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const cont = () => {
    if (finished) { navigate(`/results/${id}`); return; }
    setQ(nextQ); setNextQ(null); setLastEval(null); setAnswer("");
    setTimeout(() => speak(nextQ?.question), 300);
  };

  if (error && !iv) return <div className="max-w-2xl mx-auto px-5 py-20 text-center text-danger">{error}</div>;
  if (!iv) return <div className="flex justify-center py-24"><Spinner className="w-7 h-7 text-primary" /></div>;

  const pct = progress.total ? Math.round((progress.answered / progress.total) * 100) : 0;

  return (
    <div className="max-w-3xl mx-auto px-5 md:px-8 py-8">
      {/* header */}
      <div className="flex items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          <Pill className="border-primary/30 text-primary bg-primary/5">{iv.pack_title || iv.role}</Pill>
          {q && <Pill className="border-line text-muted capitalize">{q.difficulty}</Pill>}
        </div>
        <span className="text-sm text-muted shrink-0" data-testid="progress-text">
          {Math.min(progress.answered + (lastEval ? 0 : 1), progress.total)} / {progress.total}
        </span>
      </div>
      <div className="h-1.5 w-full bg-surface rounded-sm overflow-hidden mb-8">
        <motion.div className="h-full bg-primary" animate={{ width: `${pct}%` }} transition={{ duration: 0.5 }} />
      </div>

      <AnimatePresence mode="wait">
        {!lastEval ? (
          <motion.div key="question" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }} transition={{ duration: 0.35 }}>
            <Card className="p-7 md:p-9 mb-5">
              <div className="flex items-start justify-between gap-4 mb-5">
                <span className="overline">Interviewer asks</span>
                <button
                  data-testid="speak-btn"
                  onClick={() => (speaking ? stopSpeak() : speak(q?.question))}
                  className="flex items-center gap-1.5 text-sm text-primary hover:text-primary-hover transition-colors"
                >
                  {speaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  {speaking ? "Stop" : "Read aloud"}
                </button>
              </div>
              <h2 data-testid="question-text" className="font-heading font-bold text-2xl md:text-3xl leading-snug tracking-tight">
                {q?.question}
              </h2>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium">Your answer</span>
                <button
                  data-testid="mic-btn"
                  onClick={toggleListen}
                  disabled={transcribing}
                  className={`relative flex items-center gap-2 text-sm font-medium px-3 py-1.5 rounded-sm border transition-colors disabled:opacity-60 ${
                    listening ? "border-danger text-danger bg-danger/5" : "border-line text-ink hover:border-primary"
                  }`}
                >
                  {listening && <span className="absolute -left-1 -top-1 w-3 h-3 bg-danger rounded-full animate-pulsering" />}
                  {transcribing ? <Spinner className="w-4 h-4" /> : listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  {transcribing ? "Transcribing..." : listening ? "Stop recording" : "Record answer"}
                </button>
              </div>
              <Textarea
                testid="answer-input"
                rows={6}
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Speak using the mic, or type your answer here..."
              />
              {error && <div data-testid="interview-error" className="text-sm text-danger mt-3">{error}</div>}
              <Button variant="primary" className="w-full !py-3 mt-4" onClick={submit} disabled={submitting} data-testid="submit-answer-btn">
                {submitting ? <Spinner className="w-4 h-4" /> : <>Submit answer <Send className="w-4 h-4" /></>}
              </Button>
            </Card>
          </motion.div>
        ) : (
          <motion.div key="feedback" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
            <Card className="p-7 md:p-9" data-testid="answer-feedback">
              <div className="flex items-center gap-2 text-success mb-5">
                <CheckCircle2 className="w-5 h-5" />
                <span className="font-heading font-bold text-lg">Answer recorded</span>
              </div>

              <div className="grid sm:grid-cols-3 gap-5 mb-6">
                <ScoreBar label="Communication" score={lastEval.communication} testid="score-communication" />
                <ScoreBar label="Technical" score={lastEval.technical} testid="score-technical" />
                <ScoreBar label="Confidence" score={lastEval.confidence} testid="score-confidence" />
              </div>

              <div className="space-y-4">
                {lastEval.strengths?.length > 0 && (
                  <Feedback icon={ThumbsUp} color="text-success" title="Strengths" items={lastEval.strengths} />
                )}
                {lastEval.weaknesses?.length > 0 && (
                  <Feedback icon={AlertTriangle} color="text-warn" title="To improve" items={lastEval.weaknesses} />
                )}
                {lastEval.tips?.length > 0 && (
                  <Feedback icon={Lightbulb} color="text-primary" title="Tips" items={lastEval.tips} />
                )}
              </div>

              <Button variant="primary" className="w-full !py-3 mt-7" onClick={cont} data-testid="continue-btn">
                {finished ? <>See full results <ArrowRight className="w-4 h-4" /></> : <>Next question <ArrowRight className="w-4 h-4" /></>}
              </Button>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Feedback({ icon: Icon, color, title, items }) {
  return (
    <div className="border border-line rounded-sm p-4">
      <div className={`flex items-center gap-2 font-medium mb-2 ${color}`}>
        <Icon className="w-4 h-4" /> {title}
      </div>
      <ul className="space-y-1.5">
        {items.map((it, i) => (
          <li key={i} className="text-sm text-ink flex gap-2">
            <span className="text-muted">·</span> {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
