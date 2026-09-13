"""LLM layer. Uses Groq (OpenAI-compatible API) when GROQ_API_KEY is set,
otherwise falls back to a built-in question bank + heuristic evaluation so the
app is fully functional without any API key."""
import os
import re
import json
import httpx

from question_bank import fallback_question, get_resources, ROLE_KEYWORDS

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _groq_key() -> str:
    return (os.environ.get("GROQ_API_KEY") or "").strip()


def _groq_model() -> str:
    return os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")


def groq_enabled() -> bool:
    return bool(_groq_key())


async def _groq_chat(messages, temperature=0.7, json_mode=False):
    key = _groq_key()
    if not key:
        return None
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {"model": _groq_model(), "messages": messages, "temperature": temperature}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(GROQ_URL, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[llm] Groq call failed, falling back to local engine: {e}")
        return None


def _clamp(v):
    return max(0, min(100, int(round(v))))


# ---------------------------------------------------------------------------
# Question generation
# ---------------------------------------------------------------------------
async def generate_question(role, industry, difficulty, asked, pack=None, resume=None):
    if pack:
        # pack-driven: serve next question in the pack order
        idx = len(asked)
        questions = pack.get("questions", [])
        if idx < len(questions):
            q = questions[idx]
            return {"question": q.get("question"), "category": q.get("category", "technical"),
                    "difficulty": q.get("difficulty", difficulty), "source": "pack"}
        return None  # pack exhausted

    if groq_enabled():
        asked_list = "\n".join(f"- {a.get('question')}" for a in asked) or "(none yet)"
        resume_block = ""
        if resume:
            skills = ", ".join((resume.get("skills") or [])[:15])
            resume_block = (
                f"\nThe candidate's resume profile:\n"
                f"- Seniority: {resume.get('seniority', 'n/a')}\n"
                f"- Key skills: {skills or 'n/a'}\n"
                f"- Summary: {(resume.get('summary') or '')[:600]}\n"
                "Tailor the question to THIS candidate's background — reference their specific skills, "
                "technologies or experience where natural. Mix role fundamentals with resume-specific probes.\n"
            )
        system = (
            "You are an expert technical interviewer. Generate ONE concise, realistic interview "
            "question. Respond ONLY in JSON: {\"question\": string, \"category\": string, \"difficulty\": string}."
        )
        user = (
            f"Role: {role}\nIndustry: {industry}\nTarget difficulty: {difficulty}\n{resume_block}"
            f"Questions already asked (do NOT repeat):\n{asked_list}\n"
            "Generate the next question matching the target difficulty."
        )
        content = await _groq_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.8, json_mode=True,
        )
        if content:
            try:
                obj = json.loads(content)
                if obj.get("question"):
                    return {"question": obj["question"], "category": obj.get("category", "technical"),
                            "difficulty": obj.get("difficulty", difficulty), "source": "groq"}
            except Exception:
                pass
    q = fallback_question(role, difficulty, asked)
    q["source"] = "local"
    return q


# ---------------------------------------------------------------------------
# Resume profile extraction
# ---------------------------------------------------------------------------
ALL_KEYWORDS = sorted({k for kws in ROLE_KEYWORDS.values() for k in kws})
COMMON_TECH = [
    "python", "java", "javascript", "typescript", "react", "node", "fastapi", "django", "flask",
    "spring", "go", "rust", "c++", "kotlin", "swift", "aws", "gcp", "azure", "docker", "kubernetes",
    "sql", "postgres", "mysql", "mongodb", "redis", "kafka", "graphql", "tensorflow", "pytorch",
    "pandas", "spark", "terraform", "ci/cd", "rest", "microservices", "machine learning", "nlp",
]


async def extract_resume_profile(text: str) -> dict:
    text = (text or "").strip()
    snippet = text[:6000]
    if groq_enabled() and len(text) > 40:
        system = (
            "You analyze resumes. Extract a concise profile. Respond ONLY in JSON: "
            "{\"role_guess\": string (best-fit job title), \"seniority\": string (e.g. Junior/Mid/Senior/Lead), "
            "\"skills\": [string] (max 15 key skills/technologies), \"domains\": [string] (industries/areas), "
            "\"summary\": string (2-3 sentence professional summary)}."
        )
        content = await _groq_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": f"Resume:\n{snippet}"}],
            temperature=0.3, json_mode=True,
        )
        if content:
            try:
                obj = json.loads(content)
                return {
                    "role_guess": obj.get("role_guess") or "Full Stack Developer",
                    "seniority": obj.get("seniority") or "Mid",
                    "skills": (obj.get("skills") or [])[:15],
                    "domains": (obj.get("domains") or [])[:6],
                    "summary": obj.get("summary") or snippet[:400],
                    "source": "groq",
                }
            except Exception:
                pass
    return _heuristic_resume_profile(text)


def _heuristic_resume_profile(text: str) -> dict:
    low = text.lower()
    skills = [k for k in COMMON_TECH if k in low][:15]
    # best-fit role by keyword hits
    best_role, best_hits = "Full Stack Developer", 0
    for role, kws in ROLE_KEYWORDS.items():
        hits = sum(1 for k in kws if k in low)
        if hits > best_hits:
            best_role, best_hits = role, hits
    seniority = "Mid"
    if any(w in low for w in ["lead", "principal", "staff", "head of"]):
        seniority = "Lead"
    elif "senior" in low or "sr." in low:
        seniority = "Senior"
    elif any(w in low for w in ["junior", "intern", "graduate", "entry"]):
        seniority = "Junior"
    summary = " ".join(text.split())[:400]
    return {"role_guess": best_role, "seniority": seniority, "skills": skills, "domains": [], "summary": summary, "source": "local"}


# ---------------------------------------------------------------------------
# Answer evaluation
# ---------------------------------------------------------------------------
def _heuristic_eval(question, answer, role):
    text = (answer or "").strip()
    words = re.findall(r"[a-zA-Z']+", text.lower())
    wc = len(words)
    if wc == 0:
        return {
            "communication": 0, "technical": 0, "confidence": 0, "overall": 0,
            "strengths": [], "weaknesses": ["No answer was provided."],
            "tips": ["Try to articulate your thoughts even if you're unsure — structure your answer with a beginning, middle and end."],
            "source": "local",
        }
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_sent = wc / sentences

    communication = 30 + min(48, wc * 0.7) + (12 if 8 <= avg_sent <= 24 else 0)
    communication = _clamp(communication)

    kws = ROLE_KEYWORDS.get(role, [])
    low = text.lower()
    hits = sum(1 for k in kws if k in low)
    technical = 32 + hits * 9 + (12 if wc > 50 else 0) + (6 if wc > 25 else 0)
    technical = _clamp(technical)

    hedges = ["maybe", "i think", "probably", "not sure", "i guess", "um", "kind of", "sort of", "i don't know"]
    hedge_count = sum(low.count(h) for h in hedges)
    confidence = 58 + (18 if wc > 40 else 0) + (8 if wc > 20 else 0) - hedge_count * 9
    confidence = _clamp(confidence)

    overall = _clamp((communication + technical + confidence) / 3)

    strengths, weaknesses, tips = [], [], []
    if wc > 40:
        strengths.append("Provided a detailed, well-developed answer.")
    if hits >= 3:
        strengths.append("Used relevant technical terminology for the role.")
    if confidence >= 70:
        strengths.append("Answer came across as confident and assured.")
    if not strengths:
        strengths.append("Attempted the question and stayed on topic.")

    if wc < 25:
        weaknesses.append("Answer was quite short — add more depth and examples.")
    if hits < 2:
        weaknesses.append("Could include more role-specific concepts and terminology.")
    if hedge_count > 1:
        weaknesses.append("Frequent hedging language reduced perceived confidence.")
    if not weaknesses:
        weaknesses.append("Minor: tighten the structure for even more clarity.")

    tips.append("Use the STAR method (Situation, Task, Action, Result) to structure your answer.")
    if hits < 3:
        tips.append(f"Reference concrete {role} concepts and real examples from your experience.")
    if hedge_count > 1:
        tips.append("Avoid filler/hedging words; state your points with conviction.")

    return {
        "communication": communication, "technical": technical, "confidence": confidence,
        "overall": overall, "strengths": strengths, "weaknesses": weaknesses, "tips": tips,
        "source": "local",
    }


async def evaluate_answer(question, answer, role, difficulty):
    if groq_enabled() and (answer or "").strip():
        system = (
            "You are an expert interview evaluator. Score the candidate's answer. "
            "Respond ONLY in JSON with this exact shape: "
            "{\"communication\": int 0-100, \"technical\": int 0-100, \"confidence\": int 0-100, "
            "\"overall\": int 0-100, \"strengths\": [string], \"weaknesses\": [string], \"tips\": [string]}."
        )
        user = (
            f"Role: {role}\nDifficulty: {difficulty}\nInterview question: {question}\n\n"
            f"Candidate answer: {answer}\n\nEvaluate clarity/communication, technical accuracy/depth, "
            "and confidence. Be fair but constructive."
        )
        content = await _groq_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3, json_mode=True,
        )
        if content:
            try:
                obj = json.loads(content)
                return {
                    "communication": _clamp(obj.get("communication", 0)),
                    "technical": _clamp(obj.get("technical", 0)),
                    "confidence": _clamp(obj.get("confidence", 0)),
                    "overall": _clamp(obj.get("overall", obj.get("communication", 0))),
                    "strengths": obj.get("strengths", [])[:5],
                    "weaknesses": obj.get("weaknesses", [])[:5],
                    "tips": obj.get("tips", [])[:5],
                    "source": "groq",
                }
            except Exception:
                pass
    return _heuristic_eval(question, answer, role)


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------
async def summarize_feedback(items, role):
    if not items:
        return {"summary": "No answers were recorded for this session.", "resources": get_resources(role)}

    avg_comm = sum(i["evaluation"]["communication"] for i in items) / len(items)
    avg_tech = sum(i["evaluation"]["technical"] for i in items) / len(items)
    avg_conf = sum(i["evaluation"]["confidence"] for i in items) / len(items)

    if groq_enabled():
        transcript = "\n\n".join(
            f"Q: {i['question']}\nA: {i.get('answer','')}\nScore: {i['evaluation']['overall']}" for i in items
        )
        system = (
            "You are an interview coach. Write a short, encouraging but honest 3-4 sentence summary of the "
            "candidate's overall interview performance, highlighting the single biggest area to improve. "
            "Respond ONLY in JSON: {\"summary\": string}."
        )
        content = await _groq_chat(
            [{"role": "system", "content": system},
             {"role": "user", "content": f"Role: {role}\n\nTranscript:\n{transcript}"}],
            temperature=0.6, json_mode=True,
        )
        if content:
            try:
                obj = json.loads(content)
                if obj.get("summary"):
                    return {"summary": obj["summary"], "resources": get_resources(role)}
            except Exception:
                pass

    # heuristic summary
    weakest = min([("communication", avg_comm), ("technical accuracy", avg_tech), ("confidence", avg_conf)], key=lambda x: x[1])
    overall = (avg_comm + avg_tech + avg_conf) / 3
    tone = "Strong performance overall." if overall >= 75 else ("Solid effort with clear room to grow." if overall >= 55 else "A useful practice run — keep working at it.")
    summary = (
        f"{tone} Across {len(items)} questions you averaged {round(overall)}/100. "
        f"Your relative strength balanced communication, technical depth and confidence, while your biggest "
        f"opportunity is {weakest[0]} (avg {round(weakest[1])}/100). Focus your next practice session there."
    )
    return {"summary": summary, "resources": get_resources(role)}
