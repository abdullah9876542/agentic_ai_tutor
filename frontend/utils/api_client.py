"""
frontend/utils/api_client.py — All Streamlit → FastAPI calls.
Returns {"success": bool, "data": dict|None, "error": str|None}. Never raises.
"""

import os, httpx
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("FASTAPI_HOST","http://localhost:8000")
TIMEOUT  = 60


class APIClient:

    def __init__(self):
        self.base    = BASE_URL
        self.headers = {"Content-Type":"application/json"}

    def _safe_error(self, r: httpx.Response) -> str:
        try:
            body = r.json()
            if isinstance(body, dict):
                return body.get("detail") or body.get("message") or f"HTTP {r.status_code}"
            return str(body)
        except Exception:
            text = r.text.strip()
            if "<html" in text.lower() or len(text) > 300:
                return f"Server error (HTTP {r.status_code}). Check FastAPI terminal."
            return text or f"HTTP {r.status_code}"

    def _post(self, endpoint, payload, timeout=None):
        try:
            r = httpx.post(f"{self.base}{endpoint}", json=payload,
                           headers=self.headers, timeout=timeout or TIMEOUT)
            if r.status_code in (200,201): return {"success":True,"data":r.json(),"error":None}
            return {"success":False,"data":None,"error":self._safe_error(r)}
        except httpx.ConnectError:
            return {"success":False,"data":None,"error":"Cannot connect to backend. Is FastAPI running on port 8000?"}
        except httpx.TimeoutException:
            return {"success":False,"data":None,"error":"Request timed out."}
        except Exception as e:
            return {"success":False,"data":None,"error":str(e)}

    def _post_params(self, endpoint, params=None, timeout=None):
        try:
            r = httpx.post(f"{self.base}{endpoint}", params=params or {},
                           headers=self.headers, timeout=timeout or TIMEOUT)
            if r.status_code in (200,201): return {"success":True,"data":r.json(),"error":None}
            return {"success":False,"data":None,"error":self._safe_error(r)}
        except httpx.ConnectError:
            return {"success":False,"data":None,"error":"Cannot connect to backend. Is FastAPI running on port 8000?"}
        except httpx.TimeoutException:
            return {"success":False,"data":None,"error":"Request timed out."}
        except Exception as e:
            return {"success":False,"data":None,"error":str(e)}

    def _get(self, endpoint):
        try:
            r = httpx.get(f"{self.base}{endpoint}", headers=self.headers, timeout=TIMEOUT)
            if r.status_code == 200: return {"success":True,"data":r.json(),"error":None}
            return {"success":False,"data":None,"error":self._safe_error(r)}
        except httpx.ConnectError:
            return {"success":False,"data":None,"error":"Cannot connect to backend. Is FastAPI running on port 8000?"}
        except httpx.TimeoutException:
            return {"success":False,"data":None,"error":"Request timed out."}
        except Exception as e:
            return {"success":False,"data":None,"error":str(e)}

    def _post_file(self, endpoint, file_bytes, filename):
        try:
            r = httpx.post(f"{self.base}{endpoint}",
                           files={"file":(filename,file_bytes,self._guess_mime(filename))},
                           timeout=TIMEOUT)
            if r.status_code in (200,201): return {"success":True,"data":r.json(),"error":None}
            return {"success":False,"data":None,"error":self._safe_error(r)}
        except httpx.ConnectError:
            return {"success":False,"data":None,"error":"Cannot connect to backend. Is FastAPI running on port 8000?"}
        except httpx.TimeoutException:
            return {"success":False,"data":None,"error":"Upload timed out."}
        except Exception as e:
            return {"success":False,"data":None,"error":str(e)}

    @staticmethod
    def _guess_mime(filename):
        ext = filename.lower().rsplit(".",1)[-1]
        return {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png",
                "webp":"image/webp","pdf":"application/pdf"}.get(ext,"application/octet-stream")

    # ── Health ────────────────────────────────────────────────────
    def health_check(self): return self._get("/health")["success"]

    # ── Auth ──────────────────────────────────────────────────────
    def register(self, username, email, password, full_name="", role="student"):
        return self._post("/auth/register",{"username":username,"email":email,
                          "password":password,"full_name":full_name or None,"role":role})
    def login(self, username, password):
        return self._post("/auth/login",{"username":username,"password":password})
    def get_user(self, user_id):
        return self._get(f"/auth/me/{user_id}")

    # ── OCR ───────────────────────────────────────────────────────
    def upload_marksheet(self, user_id, file_bytes, filename):
        return self._post_file(f"/ocr/upload/{user_id}", file_bytes, filename)
    def get_marksheets(self, user_id):
        return self._get(f"/ocr/marksheets/{user_id}")
    def get_marksheet(self, marksheet_id):
        return self._get(f"/ocr/marksheet/{marksheet_id}")

    # ── Analyzer ──────────────────────────────────────────────────
    def run_analysis(self, user_id, marksheet_id=None):
        params = {}
        if marksheet_id is not None: params["marksheet_id"] = marksheet_id
        return self._post_params(f"/analyzer/run/{user_id}", params=params, timeout=90)
    def get_latest_analysis(self, user_id):
        return self._get(f"/analyzer/result/{user_id}")
    def get_analysis_by_marksheet(self, marksheet_id):
        return self._get(f"/analyzer/result/by-marksheet/{marksheet_id}")

    # ── Career ────────────────────────────────────────────────────
    def run_career(self, user_id):
        return self._post_params(f"/career/run/{user_id}", timeout=90)
    def get_career_result(self, user_id):
        return self._get(f"/career/result/{user_id}")

    # ── Tutor ─────────────────────────────────────────────────────
    def start_tutor_session(self, user_id, subject="General"):
        return self._post(f"/tutor/start/{user_id}", {"subject": subject}, timeout=60)
    def send_tutor_message(self, session_id, user_id, message):
        return self._post(f"/tutor/chat/{session_id}", {"user_id":user_id,"message":message}, timeout=60)
    def get_tutor_sessions(self, user_id):
        return self._get(f"/tutor/sessions/{user_id}")
    def get_tutor_session(self, session_id):
        return self._get(f"/tutor/session/{session_id}")
    def get_weak_subjects(self, user_id):
        return self._get(f"/tutor/weak-subjects/{user_id}")

    # ── Quiz ──────────────────────────────────────────────────────
    def generate_quiz(self, user_id, subject, difficulty="Medium", grade_level="school"):
        return self._post(f"/quiz/generate/{user_id}",
                          {"subject":subject,"difficulty":difficulty,"grade_level":grade_level},
                          timeout=60)
    def submit_quiz(self, user_id, attempt_id, answers):
        return self._post(f"/quiz/submit/{user_id}", {"attempt_id":attempt_id,"answers":answers})
    def get_quiz_history(self, user_id):
        return self._get(f"/quiz/history/{user_id}")

    # ── Dashboard ─────────────────────────────────────────────────
    def get_dashboard(self, user_id):
        return self._get(f"/dashboard/{user_id}")

    # ── Notifications ─────────────────────────────────────────────
    def get_email_status(self) -> dict:
        """GET /notify/status — check if email is configured."""
        return self._get("/notify/status")

    def send_progress_report(self, user_id: int) -> dict:
        """POST /notify/send-report/{user_id}"""
        return self._post_params(f"/notify/send-report/{user_id}", timeout=30)

    # ── Notifications ──────────────────────────────────────────────
    def send_report_email(self, user_id: int) -> dict:
        """POST /notify/send-report/{user_id} — send full report to registered email."""
        return self._post_params(f"/notify/send-report/{user_id}", timeout=30)

    def get_report_preview(self, user_id: int) -> dict:
        """GET /notify/preview/{user_id} — preview report data before sending."""
        return self._get(f"/notify/preview/{user_id}")
