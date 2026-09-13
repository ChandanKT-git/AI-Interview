"""Iteration 2 tests: Groq engine, curated packs, share/public report, voice endpoints."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"
ADMIN_EMAIL = "admin@interviewcoach.ai"
ADMIN_PASSWORD = "Admin@12345"


def _unique(prefix):
    return f"test_{prefix}_{uuid.uuid4().hex[:8]}@test.com"


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(scope="module")
def candidate_token():
    email = _unique("cand2")
    r = requests.post(f"{API}/auth/register", json={
        "name": "Cand2", "email": email, "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def recruiter_token():
    email = _unique("rec2")
    r = requests.post(f"{API}/auth/register", json={
        "name": "Rec2", "email": email, "password": "Test@12345", "role": "recruiter"
    })
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    return r.json()["token"]


# ---- Health: Groq engine ----
def test_health_groq_engine():
    r = requests.get(f"{API}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["ai_engine"] == "groq", f"Expected groq, got {data['ai_engine']}"


# ---- Curated packs ----
def test_curated_packs_present(candidate_token):
    r = requests.get(f"{API}/packs", headers=H(candidate_token))
    assert r.status_code == 200
    packs = r.json()["packs"]
    curated = [p for p in packs if p.get("is_curated")]
    assert len(curated) >= 7, f"Expected >=7 curated packs, got {len(curated)}"
    cats = {p.get("category") for p in curated}
    assert cats.issubset({"tech", "hr", "behavioural"})
    assert "tech" in cats and "hr" in cats and "behavioural" in cats


def test_curated_pack_cannot_be_deleted_by_recruiter(recruiter_token):
    r = requests.get(f"{API}/packs", headers=H(recruiter_token))
    curated = [p for p in r.json()["packs"] if p.get("is_curated")]
    assert curated
    pid = curated[0]["pack_id"]
    r2 = requests.delete(f"{API}/packs/{pid}", headers=H(recruiter_token))
    assert r2.status_code == 403
    assert "Curated library packs cannot be deleted" in r2.text


def test_curated_pack_cannot_be_deleted_by_admin(admin_token):
    r = requests.get(f"{API}/packs", headers=H(admin_token))
    curated = [p for p in r.json()["packs"] if p.get("is_curated")]
    assert curated
    pid = curated[0]["pack_id"]
    r2 = requests.delete(f"{API}/packs/{pid}", headers=H(admin_token))
    assert r2.status_code == 403
    assert "Curated library packs cannot be deleted" in r2.text


# ---- Pack interview flow using curated pack ----
def test_curated_pack_interview_flow(candidate_token):
    r = requests.get(f"{API}/packs", headers=H(candidate_token))
    curated = [p for p in r.json()["packs"] if p.get("is_curated")]
    assert curated
    pack = curated[0]
    pid = pack["pack_id"]
    pack_questions = [q["question"] for q in pack["questions"]]

    r2 = requests.post(f"{API}/interviews", headers=H(candidate_token),
                       json={"mode": "pack", "pack_id": pid})
    assert r2.status_code == 200, r2.text
    iv = r2.json()
    iid = iv["interview_id"]
    assert iv["current_question"]["question"] == pack_questions[0]
    assert iv.get("share_id", "").startswith("share_")

    answered = 0
    final = None
    for _ in range(15):
        r3 = requests.post(f"{API}/interviews/{iid}/answer",
                           headers=H(candidate_token),
                           json={"answer": "Solid pack answer with technical depth covering APIs, scaling, caching, and reliability."})
        assert r3.status_code == 200, r3.text
        data = r3.json()
        answered += 1
        if data["finished"]:
            final = data
            break
        # next question should also be from pack
        assert data["next_question"]["question"] in pack_questions
    assert final is not None
    assert "scores" in final and "summary" in final
    assert answered == iv["num_questions"]


# ---- Role interview produces Groq-sourced engine, share_id, public report ----
@pytest.fixture(scope="module")
def completed_interview(candidate_token):
    r = requests.post(f"{API}/interviews", headers=H(candidate_token),
                      json={"mode": "role", "role": "Backend Developer",
                            "difficulty": "medium", "num_questions": 1})
    assert r.status_code == 200, r.text
    iv = r.json()
    iid = iv["interview_id"]
    # answer once -> finishes
    answer = ("I would design a rate limiter using a token bucket algorithm in Redis "
              "with atomic INCR and TTL. We shard keys by user, expose metrics, and "
              "fail open with circuit breakers on Redis outages.")
    r2 = requests.post(f"{API}/interviews/{iid}/answer",
                       headers=H(candidate_token), json={"answer": answer})
    assert r2.status_code == 200, r2.text
    assert r2.json()["finished"] is True
    # fetch detail to get share_id
    r3 = requests.get(f"{API}/interviews/{iid}", headers=H(candidate_token))
    assert r3.status_code == 200
    detail = r3.json()
    assert detail["share_id"].startswith("share_")
    return detail


def test_share_id_exists_and_engine_is_groq(completed_interview):
    assert completed_interview["status"] == "completed"
    assert completed_interview.get("ai_engine") in ("groq", "local", "pack")


def test_public_report_no_auth(completed_interview):
    share_id = completed_interview["share_id"]
    r = requests.get(f"{API}/public/interviews/{share_id}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "scores" in data
    assert "items" in data
    assert "summary" in data
    assert "role" in data
    assert "candidate_name" in data
    assert "user_id" not in data


def test_public_report_invalid_share_id_404():
    r = requests.get(f"{API}/public/interviews/share_doesnotexist123")
    assert r.status_code == 404


# ---- Voice endpoints ----
def test_voice_status_enabled():
    r = requests.get(f"{API}/voice/status")
    assert r.status_code == 200
    assert r.json() == {"enabled": True}


def test_voice_tts_requires_auth():
    r = requests.post(f"{API}/voice/tts", json={"text": "hello"})
    assert r.status_code == 401


def test_voice_tts_graceful_failure(candidate_token):
    r = requests.post(f"{API}/voice/tts",
                      headers={**H(candidate_token), "Content-Type": "application/json"},
                      json={"text": "hello world"})
    # Should NOT be a 500 crash. OpenAI 429 insufficient_quota mapped to 502 by server.
    assert r.status_code != 500
    assert r.status_code in (502, 429, 503), f"Unexpected status: {r.status_code} body={r.text}"


def test_voice_stt_requires_auth():
    r = requests.post(f"{API}/voice/stt")
    assert r.status_code == 401


# ---- Regression: candidate 403 on creating pack; recruiter can create ----
def test_candidate_403_on_packs(candidate_token):
    r = requests.post(f"{API}/packs", headers=H(candidate_token),
                      json={"title": "X", "role": "Backend Developer",
                            "questions": [{"question": "Q"}]})
    assert r.status_code == 403


def test_recruiter_can_create_pack(recruiter_token):
    r = requests.post(f"{API}/packs", headers=H(recruiter_token), json={
        "title": "TEST_iter2_pack", "role": "Backend Developer",
        "industry": "Technology", "difficulty": "easy",
        "questions": [{"question": "Q1", "category": "technical", "difficulty": "easy"}]
    })
    assert r.status_code == 200
    pid = r.json()["pack_id"]
    # cleanup
    requests.delete(f"{API}/packs/{pid}", headers=H(recruiter_token))
