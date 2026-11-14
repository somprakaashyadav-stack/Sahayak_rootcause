"""
In-memory unit and integration tests for Sahayak HTTP Request Handler.
Tests GET /api/health, GET /api/schemes, GET /api/documents, POST /api/match,
and static HTML serving directly via io.BytesIO without network socket dependencies.
"""

import sys
import json
import io
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from api.server import SahayakHandler


class MockSocket:
    def __init__(self, request_bytes):
        self.rfile = io.BytesIO(request_bytes)
        self.wfile = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        return self.wfile


def simulate_request(method: str, path: str, body: dict = None):
    raw_body = json.dumps(body).encode("utf-8") if body else b""
    content_len = len(raw_body)
    
    headers = [
        f"{method} {path} HTTP/1.1",
        "Host: localhost",
        f"Content-Length: {content_len}",
        "Content-Type: application/json",
        "",
        ""
    ]
    request_data = "\r\n".join(headers).encode("utf-8") + raw_body
    sock = MockSocket(request_data)

    class TestHandler(SahayakHandler):
        def __init__(self, request_sock):
            self.rfile = request_sock.rfile
            self.wfile = request_sock.wfile
            self.client_address = ("127.0.0.1", 12345)
            self.headers = {}
            self.raw_requestline = self.rfile.readline()
            self.parse_request()

    handler = TestHandler(sock)
    
    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()

    sock.wfile.seek(0)
    response_bytes = sock.wfile.read()
    
    # Split headers and body
    parts = response_bytes.split(b"\r\n\r\n", 1)
    header_part = parts[0].decode("utf-8")
    body_part = parts[1] if len(parts) > 1 else b""
    
    return header_part, body_part


def test_in_memory_api():
    print("Testing In-Memory Sahayak API Server...")

    # 1. Health check
    h, b = simulate_request("GET", "/api/health")
    assert "200 OK" in h
    data = json.loads(b.decode("utf-8"))
    assert data["status"] == "healthy"
    print("✓ GET /api/health passed")

    # 2. Schemes list
    h, b = simulate_request("GET", "/api/schemes")
    assert "200 OK" in h
    data = json.loads(b.decode("utf-8"))
    assert data["total"] >= 15
    print(f"✓ GET /api/schemes passed ({data['total']} schemes loaded)")

    # 3. Documents list
    h, b = simulate_request("GET", "/api/documents")
    assert "200 OK" in h
    data = json.loads(b.decode("utf-8"))
    assert data["total"] >= 10
    print(f"✓ GET /api/documents passed ({data['total']} documents loaded)")

    # 4. POST /api/match
    h, b = simulate_request("POST", "/api/match", {
        "name": "Sunita Yadav",
        "age": 21,
        "state": "Uttar Pradesh",
        "gender": "female",
        "category": "obc",
        "occupation": "student",
        "education_level": "undergraduate",
        "annual_family_income": 150000,
        "existing_documents": ["aadhaar_card", "bank_passbook", "bonafide_admission_proof"]
    })
    assert "200 OK" in h
    data = json.loads(b.decode("utf-8"))
    assert data["status"] == "success"
    assert data["matched_count"] >= 3
    assert "whatsapp_card" in data
    print(f"✓ POST /api/match passed ({data['matched_count']} schemes matched)")

    # 4.5 POST /api/voice/parse
    h, b = simulate_request("POST", "/api/voice/parse", {
        "transcript": "मेरा नाम सुनीता है, मैं 21 साल की हूँ, उत्तर प्रदेश से हूँ, ओबीसी वर्ग है, कॉलेज छात्रा हूँ और परिवार की आय 150000 रुपये है"
    })
    assert "200 OK" in h
    voice_data = json.loads(b.decode("utf-8"))
    assert voice_data["status"] == "success"
    assert len(voice_data["extracted_fields"]) >= 5
    assert voice_data["profile"]["age"] == 21
    print(f"✓ POST /api/voice/parse passed ({len(voice_data['extracted_fields'])} fields extracted from Hindi speech)")

    # 4.6 POST /api/auth/send-otp
    h, b = simulate_request("POST", "/api/auth/send-otp", {"phone_number": "9876543210"})
    assert "200 OK" in h
    otp_res = json.loads(b.decode("utf-8"))
    assert otp_res["status"] == "success"
    demo_otp = otp_res["demo_otp"]
    print(f"✓ POST /api/auth/send-otp passed (Generated OTP: {demo_otp})")

    # 4.7 POST /api/auth/verify-otp
    h, b = simulate_request("POST", "/api/auth/verify-otp", {"phone_number": "9876543210", "otp": demo_otp})
    assert "200 OK" in h
    verify_res = json.loads(b.decode("utf-8"))
    assert verify_res["status"] == "success"
    assert "session_token" in verify_res
    print(f"✓ POST /api/auth/verify-otp passed (Session: {verify_res['session_token'][:18]}...)")

    # 4.8 GET /api/admin/schemes (Review Layer)
    h, b = simulate_request("GET", "/api/admin/schemes")
    assert "200 OK" in h
    admin_data = json.loads(b.decode("utf-8"))
    assert admin_data["review_layer"]["audit_compliance_pct"] == 100
    assert "last_verified_date" in admin_data["schemes"][0]
    print(f"✓ GET /api/admin/schemes passed (Audited {len(admin_data['schemes'])} schemes with last verified dates)")

    # 4.9 POST /api/admin/verify-scheme
    h, b = simulate_request("POST", "/api/admin/verify-scheme", {
        "scheme_id": "up_post_matric_scholarship",
        "verified_by": "State Scholarship Directorate Audit",
        "verified_date": "2026-11-14"
    })
    assert "200 OK" in h
    audit_res = json.loads(b.decode("utf-8"))
    assert audit_res["status"] == "success"
    assert audit_res["scheme"]["verified_by"] == "State Scholarship Directorate Audit"
    print("✓ POST /api/admin/verify-scheme passed (Audit timestamp updated)")

    # 5. Static Frontend
    h, b = simulate_request("GET", "/")
    assert "200 OK" in h
    assert b"Sahayak" in b
    print("✓ GET / (Static Web UI index.html) passed")

    print("\n🚀 ALL IN-MEMORY API TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_in_memory_api()
