"""Iteration 3 tests: Resume import, resume-based interview, Bearer-auth regression."""
import os
import io
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


RESUME_TEXT = (
    "John Doe — Senior Backend Engineer\n"
    "Email: john@example.com | 8+ years experience.\n\n"
    "SUMMARY\n"
    "Senior backend engineer specializing in distributed systems, Python, FastAPI, "
    "and cloud-native microservices on AWS. Led teams of 4-6 engineers.\n\n"
    "SKILLS\n"
    "Python, FastAPI, Django, PostgreSQL, MongoDB, Redis, Kafka, Docker, "
    "Kubernetes, AWS (EC2, S3, Lambda), CI/CD, gRPC, REST APIs, system design.\n\n"
    "EXPERIENCE\n"
    "Acme Corp — Senior Backend Engineer (2020-Present)\n"
    "- Built event-driven order processing platform handling 50k req/s.\n"
    "- Migrated monolith to microservices, cut p95 latency 60%.\n"
    "- Mentored 4 engineers; ran code reviews and architecture forums.\n\n"
    "Beta Inc — Backend Engineer (2017-2020)\n"
    "- Designed REST APIs, integrated Stripe, built async workers using Celery.\n"
)


# =============================================================================
# Auth regression — Bearer token model
# =============================================================================
@pytest.fixture(scope="module")
def fresh_candidate():
    email = _unique("res")
    r = requests.post(f"{API}/auth/register", json={
        "name": "Resume Cand", "email": email, "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert "user" in data and "token" in data
    assert isinstance(data["token"], str) and len(data["token"]) > 10
    assert data["user"]["email"] == email
    return {"email": email, "token": data["token"], "user": data["user"]}


def test_register_returns_user_and_token(fresh_candidate):
    assert fresh_candidate["token"]
    assert fresh_candidate["user"]["role"] == "candidate"


def test_auth_me_with_bearer(fresh_candidate):
    r = requests.get(f"{API}/auth/me", headers=H(fresh_candidate["token"]))
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == fresh_candidate["email"]


def test_auth_me_without_bearer_401():
    r = requests.get(f"{API}/auth/me")
    assert r.status_code == 401


def test_login_wrong_password_401(fresh_candidate):
    r = requests.post(f"{API}/auth/login", json={
        "email": fresh_candidate["email"], "password": "WRONG@nope"
    })
    assert r.status_code == 401


def test_duplicate_email_400(fresh_candidate):
    r = requests.post(f"{API}/auth/register", json={
        "name": "Dup", "email": fresh_candidate["email"], "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 400


def test_admin_login_with_bearer():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    tok = r.json()["token"]
    assert tok
    r2 = requests.get(f"{API}/auth/me", headers=H(tok))
    assert r2.status_code == 200
    assert r2.json()["role"] == "admin"


# =============================================================================
# Resume text import
# =============================================================================
def test_get_resume_empty_initially(fresh_candidate):
    r = requests.get(f"{API}/resume", headers=H(fresh_candidate["token"]))
    assert r.status_code == 200
    assert r.json()["has_resume"] is False


def test_resume_text_import(fresh_candidate):
    r = requests.post(f"{API}/resume/text",
                      headers={**H(fresh_candidate["token"]), "Content-Type": "application/json"},
                      json={"text": RESUME_TEXT})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "profile" in body and "ai_engine" in body
    profile = body["profile"]
    assert "role_guess" in profile
    assert "seniority" in profile
    assert "skills" in profile and isinstance(profile["skills"], list)
    assert "summary" in profile
    assert len(profile["skills"]) >= 1


def test_get_resume_after_import(fresh_candidate):
    r = requests.get(f"{API}/resume", headers=H(fresh_candidate["token"]))
    assert r.status_code == 200
    body = r.json()
    assert body["has_resume"] is True
    assert body["profile"] is not None
    assert "role_guess" in body["profile"]


def test_resume_text_too_short_returns_400(fresh_candidate):
    r = requests.post(f"{API}/resume/text",
                      headers={**H(fresh_candidate["token"]), "Content-Type": "application/json"},
                      json={"text": "hi"})
    assert r.status_code == 400


def test_resume_text_requires_auth():
    r = requests.post(f"{API}/resume/text", json={"text": RESUME_TEXT})
    assert r.status_code == 401


# =============================================================================
# Resume upload (multipart .txt)
# =============================================================================
def test_resume_upload_txt(fresh_candidate):
    files = {"file": ("resume.txt", io.BytesIO(RESUME_TEXT.encode("utf-8")), "text/plain")}
    r = requests.post(f"{API}/resume/upload", headers=H(fresh_candidate["token"]), files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "profile" in body
    assert len(body["profile"].get("skills", [])) >= 1


def test_resume_upload_too_short_400(fresh_candidate):
    files = {"file": ("tiny.txt", io.BytesIO(b"too short"), "text/plain")}
    r = requests.post(f"{API}/resume/upload", headers=H(fresh_candidate["token"]), files=files)
    assert r.status_code == 400


def test_resume_upload_empty_400(fresh_candidate):
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    r = requests.post(f"{API}/resume/upload", headers=H(fresh_candidate["token"]), files=files)
    assert r.status_code == 400


# =============================================================================
# Resume-based interview
# =============================================================================
def test_resume_interview_without_resume_returns_400():
    """A fresh user that hasn't uploaded a resume must get 400."""
    email = _unique("noresume")
    r = requests.post(f"{API}/auth/register", json={
        "name": "NoResume", "email": email, "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 200
    tok = r.json()["token"]
    r2 = requests.post(f"{API}/interviews", headers=H(tok),
                       json={"mode": "resume", "difficulty": "medium", "num_questions": 2})
    assert r2.status_code == 400
    assert "import your resume first" in r2.text.lower()


def test_resume_interview_flow(fresh_candidate):
    # Ensure resume is imported (uses fresh_candidate already imported above)
    profile_r = requests.get(f"{API}/resume", headers=H(fresh_candidate["token"]))
    assert profile_r.json()["has_resume"] is True
    role_guess = profile_r.json()["profile"]["role_guess"]

    r = requests.post(f"{API}/interviews", headers=H(fresh_candidate["token"]),
                      json={"mode": "resume", "difficulty": "medium", "num_questions": 2})
    assert r.status_code == 200, r.text
    iv = r.json()
    assert iv["mode"] == "resume"
    assert iv["role"] == role_guess
    assert iv["current_question"] and iv["current_question"]["question"]
    iid = iv["interview_id"]

    # answer 2 -> finish
    final = None
    for _ in range(3):
        r2 = requests.post(f"{API}/interviews/{iid}/answer",
                           headers=H(fresh_candidate["token"]),
                           json={"answer": "I designed a Redis-backed rate limiter using token bucket, sharded by user, with FastAPI middleware and async metrics."})
        assert r2.status_code == 200, r2.text
        data = r2.json()
        if data["finished"]:
            final = data
            break
    assert final is not None
    assert "scores" in final and "summary" in final
    assert all(k in final["scores"] for k in ("communication", "technical", "confidence", "overall"))
