import os
import uuid
import httpx
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from db import db, serialize
from models import StartInterviewRequest, AnswerRequest, PackRequest
import auth
from auth import get_current_user, require_role
import llm
from question_bank import ROLES, get_resources

app = FastAPI(title="AI Interview Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000"), "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
api = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# Badges
# ---------------------------------------------------------------------------
BADGES = {
    "first_interview": {"name": "First Steps", "description": "Completed your first interview", "icon": "footprints"},
    "five_interviews": {"name": "Committed", "description": "Completed 5 interviews", "icon": "flame"},
    "ten_interviews": {"name": "Dedicated", "description": "Completed 10 interviews", "icon": "trophy"},
    "high_scorer": {"name": "High Scorer", "description": "Scored 85+ in an interview", "icon": "star"},
    "perfectionist": {"name": "Perfectionist", "description": "Scored 95+ in an interview", "icon": "crown"},
    "communicator": {"name": "Great Communicator", "description": "Averaged 80+ communication", "icon": "messages-square"},
    "all_rounder": {"name": "All-Rounder", "description": "Practiced 3 different roles", "icon": "layers"},
}


async def award_badges(user: dict, session_overall: int, session_comm: int):
    user_id = user["user_id"]
    earned = set(user.get("badges", []))
    completed = await db.interviews.count_documents({"user_id": user_id, "status": "completed"})
    distinct_roles = len(await db.interviews.distinct("role", {"user_id": user_id, "status": "completed"}))

    if completed >= 1:
        earned.add("first_interview")
    if completed >= 5:
        earned.add("five_interviews")
    if completed >= 10:
        earned.add("ten_interviews")
    if session_overall >= 85:
        earned.add("high_scorer")
    if session_overall >= 95:
        earned.add("perfectionist")
    if session_comm >= 80:
        earned.add("communicator")
    if distinct_roles >= 3:
        earned.add("all_rounder")

    new_badges = list(earned - set(user.get("badges", [])))
    if new_badges:
        await db.users.update_one({"user_id": user_id}, {"$set": {"badges": list(earned)}})
    return list(earned), new_badges


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------
@api.get("/health")
async def health():
    return {"status": "ok", "ai_engine": "groq" if llm.groq_enabled() else "local-fallback"}


@api.get("/meta/roles")
async def get_roles():
    return {"roles": ROLES, "ai_engine": "groq" if llm.groq_enabled() else "local-fallback"}


# ---------------------------------------------------------------------------
# Interview engine
# ---------------------------------------------------------------------------
def _next_difficulty(items, base):
    if not items:
        return base
    recent = items[-2:]
    avg = sum(i["evaluation"]["overall"] for i in recent) / len(recent)
    order = ["easy", "medium", "hard"]
    cur = items[-1].get("difficulty", base)
    idx = order.index(cur) if cur in order else 1
    if avg >= 78 and idx < 2:
        idx += 1
    elif avg < 50 and idx > 0:
        idx -= 1
    return order[idx]


def _interview_public(s: dict) -> dict:
    s = serialize(s)
    return s


@api.post("/interviews")
async def start_interview(body: StartInterviewRequest, user: dict = Depends(get_current_user)):
    pack = None
    resume_context = None
    role = body.role
    industry = body.industry or "Technology"
    difficulty = body.difficulty or "medium"
    num_questions = max(1, min(15, body.num_questions))

    if body.mode == "pack":
        if not body.pack_id:
            raise HTTPException(status_code=400, detail="pack_id is required for pack mode.")
        pack = await db.packs.find_one({"pack_id": body.pack_id}, {"_id": 0})
        if not pack:
            raise HTTPException(status_code=404, detail="Interview pack not found.")
        role = pack["role"]
        industry = pack.get("industry", industry)
        difficulty = pack.get("difficulty", difficulty)
        num_questions = len(pack.get("questions", [])) or num_questions
    elif body.mode == "resume":
        profile = user.get("resume_profile")
        if not profile:
            raise HTTPException(status_code=400, detail="Please import your resume first.")
        role = body.role or profile.get("role_guess") or "Full Stack Developer"
        resume_context = {
            "summary": profile.get("summary"),
            "skills": profile.get("skills", []),
            "seniority": profile.get("seniority"),
            "role": role,
        }
    else:
        if not role:
            raise HTTPException(status_code=400, detail="role is required for role mode.")

    first_q = await llm.generate_question(role, industry, difficulty, [], pack, resume_context)
    if not first_q:
        raise HTTPException(status_code=400, detail="Could not generate a question.")

    interview = {
        "interview_id": f"int_{uuid.uuid4().hex[:14]}",
        "share_id": f"share_{uuid.uuid4().hex[:16]}",
        "user_id": user["user_id"],
        "mode": body.mode,
        "pack_id": body.pack_id,
        "pack_title": pack.get("title") if pack else None,
        "resume_context": resume_context,
        "role": role,
        "industry": industry,
        "base_difficulty": difficulty,
        "num_questions": num_questions,
        "status": "active",
        "current_question": first_q,
        "items": [],
        "scores": None,
        "summary": None,
        "resources": [],
        "ai_engine": first_q.get("source", "local"),
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    await db.interviews.insert_one(interview)
    return _interview_public(interview)


@api.get("/interviews")
async def list_interviews(user: dict = Depends(get_current_user)):
    docs = await db.interviews.find({"user_id": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"interviews": docs}


@api.get("/interviews/{interview_id}")
async def get_interview(interview_id: str, user: dict = Depends(get_current_user)):
    doc = await db.interviews.find_one({"interview_id": interview_id, "user_id": user["user_id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return doc


@api.post("/interviews/{interview_id}/answer")
async def submit_answer(interview_id: str, body: AnswerRequest, user: dict = Depends(get_current_user)):
    doc = await db.interviews.find_one({"interview_id": interview_id, "user_id": user["user_id"]})
    if not doc:
        raise HTTPException(status_code=404, detail="Interview not found.")
    if doc["status"] != "active":
        raise HTTPException(status_code=400, detail="This interview is already completed.")

    current = doc.get("current_question")
    if not current:
        raise HTTPException(status_code=400, detail="No active question to answer.")

    evaluation = await llm.evaluate_answer(current["question"], body.answer, doc["role"], current.get("difficulty"))
    item = {
        "question": current["question"],
        "category": current.get("category", "technical"),
        "difficulty": current.get("difficulty", doc["base_difficulty"]),
        "answer": body.answer,
        "evaluation": evaluation,
        "answered_at": datetime.now(timezone.utc),
    }
    items = doc["items"] + [item]

    pack = None
    if doc.get("pack_id"):
        pack = await db.packs.find_one({"pack_id": doc["pack_id"]}, {"_id": 0})

    finished = len(items) >= doc["num_questions"]
    next_question = None
    if not finished:
        nd = _next_difficulty(items, doc["base_difficulty"])
        next_question = await llm.generate_question(doc["role"], doc["industry"], nd, items, pack, doc.get("resume_context"))
        if next_question is None:
            finished = True

    update = {"items": items, "current_question": next_question}
    response_extra = {}

    if finished:
        comm = round(sum(i["evaluation"]["communication"] for i in items) / len(items))
        tech = round(sum(i["evaluation"]["technical"] for i in items) / len(items))
        conf = round(sum(i["evaluation"]["confidence"] for i in items) / len(items))
        overall = round((comm + tech + conf) / 3)
        scores = {"communication": comm, "technical": tech, "confidence": conf, "overall": overall}
        summary_obj = await llm.summarize_feedback(items, doc["role"])
        update.update({
            "status": "completed",
            "current_question": None,
            "scores": scores,
            "summary": summary_obj["summary"],
            "resources": summary_obj["resources"],
            "completed_at": datetime.now(timezone.utc),
        })
        await db.interviews.update_one({"interview_id": interview_id}, {"$set": update})
        all_badges, new_badges = await award_badges(user, overall, comm)
        response_extra = {"scores": scores, "summary": summary_obj["summary"],
                          "resources": summary_obj["resources"], "new_badges": new_badges}
    else:
        await db.interviews.update_one({"interview_id": interview_id}, {"$set": update})

    return {
        "evaluation": evaluation,
        "finished": finished,
        "next_question": next_question,
        "progress": {"answered": len(items), "total": doc["num_questions"]},
        **response_extra,
    }


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@api.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    completed = await db.interviews.find(
        {"user_id": user["user_id"], "status": "completed"}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)

    total = len(completed)
    if total:
        avg_overall = round(sum(c["scores"]["overall"] for c in completed) / total)
        avg_comm = round(sum(c["scores"]["communication"] for c in completed) / total)
        avg_tech = round(sum(c["scores"]["technical"] for c in completed) / total)
        avg_conf = round(sum(c["scores"]["confidence"] for c in completed) / total)
        best = max(c["scores"]["overall"] for c in completed)
    else:
        avg_overall = avg_comm = avg_tech = avg_conf = best = 0

    trend = [
        {"index": i + 1, "role": c["role"], "overall": c["scores"]["overall"],
         "date": c["completed_at"].isoformat() if isinstance(c.get("completed_at"), datetime) else c.get("completed_at")}
        for i, c in enumerate(completed[-10:])
    ]

    earned = user.get("badges", [])
    badges = [{"id": b, **BADGES[b], "earned": True} for b in earned if b in BADGES]
    badges += [{"id": k, **v, "earned": False} for k, v in BADGES.items() if k not in earned]

    recent = await db.interviews.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(5)

    return {
        "stats": {
            "total_interviews": total,
            "avg_overall": avg_overall,
            "avg_communication": avg_comm,
            "avg_technical": avg_tech,
            "avg_confidence": avg_conf,
            "best_score": best,
            "badges_earned": len(earned),
        },
        "skill_breakdown": [
            {"skill": "Communication", "score": avg_comm},
            {"skill": "Technical", "score": avg_tech},
            {"skill": "Confidence", "score": avg_conf},
        ],
        "trend": trend,
        "badges": badges,
        "recent": recent,
    }


# ---------------------------------------------------------------------------
# Packs (recruiter / admin build custom interviews)
# ---------------------------------------------------------------------------
@api.get("/packs")
async def list_packs(user: dict = Depends(get_current_user)):
    docs = await db.packs.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"packs": docs}


@api.get("/packs/mine")
async def my_packs(user: dict = Depends(require_role("recruiter", "admin"))):
    docs = await db.packs.find({"created_by": user["user_id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"packs": docs}


@api.post("/packs")
async def create_pack(body: PackRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    pack = {
        "pack_id": f"pack_{uuid.uuid4().hex[:12]}",
        "title": body.title,
        "role": body.role,
        "industry": body.industry,
        "description": body.description,
        "difficulty": body.difficulty,
        "questions": [q.model_dump() for q in body.questions],
        "created_by": user["user_id"],
        "created_by_name": user.get("name"),
        "created_at": datetime.now(timezone.utc),
    }
    await db.packs.insert_one(pack)
    return serialize(pack)


@api.put("/packs/{pack_id}")
async def update_pack(pack_id: str, body: PackRequest, user: dict = Depends(require_role("recruiter", "admin"))):
    pack = await db.packs.find_one({"pack_id": pack_id})
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found.")
    if user["role"] != "admin" and pack.get("created_by") != user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own packs.")
    await db.packs.update_one({"pack_id": pack_id}, {"$set": {
        "title": body.title, "role": body.role, "industry": body.industry,
        "description": body.description, "difficulty": body.difficulty,
        "questions": [q.model_dump() for q in body.questions],
    }})
    updated = await db.packs.find_one({"pack_id": pack_id}, {"_id": 0})
    return updated


@api.delete("/packs/{pack_id}")
async def delete_pack(pack_id: str, user: dict = Depends(require_role("recruiter", "admin"))):
    pack = await db.packs.find_one({"pack_id": pack_id})
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found.")
    if pack.get("is_curated"):
        raise HTTPException(status_code=403, detail="Curated library packs cannot be deleted.")
    if user["role"] != "admin" and pack.get("created_by") != user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own packs.")
    await db.packs.delete_one({"pack_id": pack_id})
    return {"ok": True}


# ---------------------------------------------------------------------------
# Voice (OpenAI Whisper STT + OpenAI TTS) — gracefully disabled if no key
# ---------------------------------------------------------------------------
def _openai_key():
    return (os.environ.get("OPENAI_API_KEY") or "").strip()


@api.get("/voice/status")
async def voice_status():
    return {"enabled": bool(_openai_key())}


@api.post("/voice/tts")
async def voice_tts(payload: dict, user: dict = Depends(get_current_user)):
    key = _openai_key()
    text = (payload or {}).get("text", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Cloud voice not configured.")
    if not text:
        raise HTTPException(status_code=400, detail="No text provided.")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": "tts-1", "voice": "alloy", "input": text[:4000]},
            )
            r.raise_for_status()
            return Response(content=r.content, media_type="audio/mpeg")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"TTS failed: {e.response.status_code}")
    except Exception:
        raise HTTPException(status_code=502, detail="TTS request failed.")


@api.post("/voice/stt")
async def voice_stt(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    key = _openai_key()
    if not key:
        raise HTTPException(status_code=503, detail="Cloud voice not configured.")
    try:
        content = await file.read()
        async with httpx.AsyncClient(timeout=90) as client:
            r = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {key}"},
                files={"file": (file.filename or "audio.webm", content, file.content_type or "audio/webm")},
                data={"model": "whisper-1"},
            )
            r.raise_for_status()
            return {"text": r.json().get("text", "")}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Transcription failed: {e.response.status_code}")
    except Exception:
        raise HTTPException(status_code=502, detail="Transcription request failed.")


# ---------------------------------------------------------------------------
# Resume import & resume-based interviews
# ---------------------------------------------------------------------------
@api.get("/resume")
async def get_resume(user: dict = Depends(get_current_user)):
    profile = user.get("resume_profile")
    return {
        "has_resume": bool(profile),
        "profile": profile,
        "updated_at": user.get("resume_updated_at"),
    }


async def _save_resume(user: dict, text: str):
    if len(text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Resume text is too short to analyze.")
    profile = await llm.extract_resume_profile(text)
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"resume_text": text[:12000], "resume_profile": profile,
                  "resume_updated_at": datetime.now(timezone.utc)}},
    )
    return {"profile": profile, "ai_engine": "groq" if llm.groq_enabled() else "local"}


@api.post("/resume/upload")
async def resume_upload(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    from resume_utils import extract_resume_text
    content = await file.read()
    if len(content) > 5_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 5MB).")
    text = extract_resume_text(file.filename, content, file.content_type)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from this file. Try a PDF, DOCX, or paste the text.")
    return await _save_resume(user, text)


@api.post("/resume/text")
async def resume_text(payload: dict, user: dict = Depends(get_current_user)):
    text = (payload or {}).get("text", "")
    return await _save_resume(user, text)


# ---------------------------------------------------------------------------
# Public shareable report (no auth)
# ---------------------------------------------------------------------------
@api.get("/public/interviews/{share_id}")
async def public_report(share_id: str):
    doc = await db.interviews.find_one(
        {"share_id": share_id, "status": "completed"},
        {"_id": 0, "user_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Report not found or interview not completed.")
    owner = await db.users.find_one({"user_id": (await db.interviews.find_one({"share_id": share_id})).get("user_id")}, {"_id": 0, "name": 1})
    doc["candidate_name"] = owner.get("name") if owner else "Candidate"
    return doc


app.include_router(api)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("expires_at", expireAfterSeconds=0)
    await db.interviews.create_index("user_id")
    await db.packs.create_index("pack_id", unique=True)
    await auth.seed_admin()
    from curated_packs import seed_curated_packs
    await seed_curated_packs()
    print(f"[startup] AI engine: {'groq' if llm.groq_enabled() else 'local-fallback'}")
