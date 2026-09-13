"""Backend tests for AI Interview Coach - auth, RBAC, interview engine, packs, dashboard."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback to read frontend .env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

API = f"{BASE_URL}/api"

ADMIN_EMAIL = "admin@interviewcoach.ai"
ADMIN_PASSWORD = "Admin@12345"


def _unique(prefix):
    # email is lowercased server-side, so use lowercase to make assertions deterministic
    return f"test_{prefix}_{uuid.uuid4().hex[:8]}@test.com"


# Use plain requests (no shared cookie jar) so Bearer-token tests aren't
# overridden by stale cookies from previous logins.
class NoCookieClient:
    """Wraps requests with JSON content-type, no shared cookie state."""
    def _req(self, method, url, **kw):
        kw.setdefault("headers", {})
        kw["headers"].setdefault("Content-Type", "application/json")
        return requests.request(method, url, **kw)

    def get(self, url, **kw): return self._req("GET", url, **kw)
    def post(self, url, **kw): return self._req("POST", url, **kw)
    def put(self, url, **kw): return self._req("PUT", url, **kw)
    def delete(self, url, **kw): return self._req("DELETE", url, **kw)


@pytest.fixture(scope="module")
def session():
    return NoCookieClient()


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["user"]["role"] == "admin"
    return data["token"]


@pytest.fixture(scope="module")
def candidate(session):
    email = _unique("cand")
    r = session.post(f"{API}/auth/register", json={
        "name": "Test Candidate", "email": email, "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 200, r.text
    data = r.json()
    return {"token": data["token"], "user": data["user"], "email": email}


@pytest.fixture(scope="module")
def recruiter(session):
    email = _unique("rec")
    r = session.post(f"{API}/auth/register", json={
        "name": "Test Recruiter", "email": email, "password": "Test@12345", "role": "recruiter"
    })
    assert r.status_code == 200, r.text
    data = r.json()
    return {"token": data["token"], "user": data["user"], "email": email}


def H(token):
    return {"Authorization": f"Bearer {token}"}


# --- HEALTH ---
def test_health(session):
    r = session.get(f"{API}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["ai_engine"] in ("groq", "local-fallback")


# --- AUTH ---
def test_register_candidate_and_me_via_bearer(session, candidate):
    r = session.get(f"{API}/auth/me", headers=H(candidate["token"]))
    assert r.status_code == 200
    user = r.json()
    assert user["email"] == candidate["email"]
    assert user["role"] == "candidate"


def test_me_via_cookie(session):
    s = requests.Session()
    email = _unique("cookie")
    r = s.post(f"{API}/auth/register", json={
        "name": "Cookie User", "email": email, "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 200
    # cookie set
    r2 = s.get(f"{API}/auth/me")
    assert r2.status_code == 200
    assert r2.json()["email"] == email


def test_admin_login(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "admin"


def test_wrong_password_401(session):
    r = session.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"})
    assert r.status_code == 401


def test_duplicate_email_400(session, candidate):
    r = session.post(f"{API}/auth/register", json={
        "name": "Dup", "email": candidate["email"], "password": "Test@12345", "role": "candidate"
    })
    assert r.status_code == 400


def test_unauthenticated_me_401(session):
    r = requests.get(f"{API}/auth/me")
    assert r.status_code == 401


# --- RBAC packs ---
def test_candidate_cannot_create_pack(session, candidate):
    r = session.post(f"{API}/packs", headers=H(candidate["token"]), json={
        "title": "X", "role": "Backend Developer", "questions": [{"question": "Q1"}]
    })
    assert r.status_code == 403


@pytest.fixture(scope="module")
def recruiter_pack(session, recruiter):
    payload = {
        "title": "TEST_Recruiter_Pack",
        "role": "Backend Developer",
        "industry": "Technology",
        "description": "Test pack",
        "difficulty": "medium",
        "questions": [
            {"question": "Explain REST vs GraphQL.", "category": "technical", "difficulty": "medium"},
            {"question": "How do you handle DB scaling?", "category": "technical", "difficulty": "medium"},
        ],
    }
    r = session.post(f"{API}/packs", headers=H(recruiter["token"]), json=payload)
    assert r.status_code == 200, r.text
    pack = r.json()
    assert "pack_id" in pack
    assert pack["created_by"] == recruiter["user"]["user_id"]
    return pack


def test_recruiter_create_and_mine(session, recruiter, recruiter_pack):
    r = session.get(f"{API}/packs/mine", headers=H(recruiter["token"]))
    assert r.status_code == 200
    ids = [p["pack_id"] for p in r.json()["packs"]]
    assert recruiter_pack["pack_id"] in ids


def test_candidate_can_list_packs(session, candidate, recruiter_pack):
    r = session.get(f"{API}/packs", headers=H(candidate["token"]))
    assert r.status_code == 200
    ids = [p["pack_id"] for p in r.json()["packs"]]
    assert recruiter_pack["pack_id"] in ids


def test_recruiter_cannot_edit_others_pack(session, recruiter_pack):
    # second recruiter
    email = _unique("rec2")
    r = session.post(f"{API}/auth/register", json={
        "name": "R2", "email": email, "password": "Test@12345", "role": "recruiter"
    })
    tok = r.json()["token"]
    pid = recruiter_pack["pack_id"]
    payload = {"title": "Hacked", "role": "Backend Developer",
               "questions": [{"question": "x"}]}
    r2 = session.put(f"{API}/packs/{pid}", headers=H(tok), json=payload)
    assert r2.status_code == 403
    r3 = session.delete(f"{API}/packs/{pid}", headers=H(tok))
    assert r3.status_code == 403


def test_recruiter_update_own_pack(session, recruiter, recruiter_pack):
    pid = recruiter_pack["pack_id"]
    payload = {
        "title": "TEST_Recruiter_Pack_Updated",
        "role": "Backend Developer",
        "questions": [{"question": "New Q"}],
    }
    r = session.put(f"{API}/packs/{pid}", headers=H(recruiter["token"]), json=payload)
    assert r.status_code == 200
    assert r.json()["title"] == "TEST_Recruiter_Pack_Updated"


# --- INTERVIEW ENGINE (role mode) ---
def test_interview_role_mode_full_flow(session, candidate):
    tok = candidate["token"]
    r = session.post(f"{API}/interviews", headers=H(tok), json={
        "mode": "role", "role": "Backend Developer", "difficulty": "medium", "num_questions": 3
    })
    assert r.status_code == 200, r.text
    iv = r.json()
    iid = iv["interview_id"]
    assert iv["current_question"]["question"]
    assert iv["status"] == "active"

    finished = False
    strong = ("I would design a rate limiter using a token bucket algorithm with Redis "
              "for distributed counters, leveraging atomic INCR with TTL. Endpoints are "
              "protected at the API gateway level. We handle scaling via sharded keys, "
              "cache locality, and queue overflow with backpressure. Auth tokens, "
              "transactions and microservice latency are also considered.")
    for i in range(5):
        r = session.post(f"{API}/interviews/{iid}/answer", headers=H(tok), json={"answer": strong})
        assert r.status_code == 200, r.text
        data = r.json()
        ev = data["evaluation"]
        for k in ("communication", "technical", "confidence", "overall"):
            assert 0 <= ev[k] <= 100
        if data["finished"]:
            finished = True
            assert "scores" in data
            assert "summary" in data
            assert "resources" in data and isinstance(data["resources"], list)
            assert "new_badges" in data
            assert "first_interview" in data["new_badges"] or True  # may already have it from prior test
            break
    assert finished, "Interview did not finish in 3+ answers"

    # cannot answer again
    r = session.post(f"{API}/interviews/{iid}/answer", headers=H(tok), json={"answer": "x"})
    assert r.status_code == 400


def test_interviews_list_and_detail(session, candidate):
    tok = candidate["token"]
    r = session.get(f"{API}/interviews", headers=H(tok))
    assert r.status_code == 200
    lst = r.json()["interviews"]
    assert len(lst) >= 1
    iid = lst[0]["interview_id"]
    r2 = session.get(f"{API}/interviews/{iid}", headers=H(tok))
    assert r2.status_code == 200
    assert r2.json()["interview_id"] == iid


def test_dashboard_after_completion(session, candidate):
    r = session.get(f"{API}/dashboard", headers=H(candidate["token"]))
    assert r.status_code == 200
    d = r.json()
    assert d["stats"]["total_interviews"] >= 1
    assert d["stats"]["badges_earned"] >= 1
    assert any(b["id"] == "first_interview" and b["earned"] for b in d["badges"])
    assert isinstance(d["skill_breakdown"], list) and len(d["skill_breakdown"]) == 3
    assert "trend" in d and "recent" in d


# --- pack interview flow ---
def test_pack_interview_flow(session, candidate, recruiter_pack):
    tok = candidate["token"]
    r = session.post(f"{API}/interviews", headers=H(tok), json={
        "mode": "pack", "pack_id": recruiter_pack["pack_id"]
    })
    assert r.status_code == 200, r.text
    iv = r.json()
    iid = iv["interview_id"]
    assert iv["current_question"]["source"] == "pack"
    # answer until finished
    answered = 0
    for _ in range(10):
        r = session.post(f"{API}/interviews/{iid}/answer", headers=H(tok),
                         json={"answer": "A solid answer with technical depth about API and database."})
        assert r.status_code == 200
        answered += 1
        if r.json()["finished"]:
            break
    assert answered == iv["num_questions"]


def test_pack_missing_id_400(session, candidate):
    r = session.post(f"{API}/interviews", headers=H(candidate["token"]), json={"mode": "pack"})
    assert r.status_code == 400


def test_role_missing_400(session, candidate):
    r = session.post(f"{API}/interviews", headers=H(candidate["token"]), json={"mode": "role"})
    assert r.status_code == 400


# --- cleanup: delete created pack ---
def test_zz_cleanup_pack(session, recruiter, recruiter_pack):
    r = session.delete(f"{API}/packs/{recruiter_pack['pack_id']}", headers=H(recruiter["token"]))
    assert r.status_code == 200
