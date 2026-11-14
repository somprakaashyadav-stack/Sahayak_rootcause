"""
Sahayak Web & API Server
Zero-dependency, production-ready lightweight HTTP server.
Serves the REST API endpoints and hosts the modern web dashboard.
"""

import sys
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from engine.models import (
    UserProfile,
    Gender,
    SocialCategory,
    EducationLevel,
    Occupation,
    RationCardType
)
from engine.matcher import RulesEngine
from ai.explainer import SahayakExplainer
from engine.voice_parser import VoiceProfileParser

# Initialize singleton instances
rules_engine = RulesEngine()
explainer = SahayakExplainer()
voice_parser = VoiceProfileParser()


class SahayakHandler(BaseHTTPRequestHandler):
    """Handles API requests and serves the frontend web application."""

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def _send_json_response(self, data: dict, status_code: int = 200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API: List schemes
        if path == "/api/schemes":
            schemes_data = [s.to_dict() for s in rules_engine.schemes]
            self._send_json_response({"status": "success", "total": len(schemes_data), "schemes": schemes_data})
            return

        # 2. API: List documents
        if path == "/api/documents":
            docs_data = [asdict_prereq(p) for p in rules_engine.resolver.documents_catalog.values()]
            self._send_json_response({"status": "success", "total": len(docs_data), "documents": docs_data})
            return

        # 3. API: Health Check
        if path == "/api/health":
            self._send_json_response({"status": "healthy", "service": "Sahayak API", "version": "1.0.0"})
            return

        # 4. Static Frontend: Serve index.html or assets
        if path == "/" or path == "/index.html":
            file_path = BASE_DIR / "frontend" / "index.html"
        else:
            relative_path = path.lstrip("/")
            file_path = BASE_DIR / "frontend" / relative_path

        if file_path.is_file():
            mime_type, _ = mimetypes.guess_type(str(file_path))
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime_type or "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_json_response({"error": "Not Found", "path": path}, status_code=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/match":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(raw_body) if raw_body else {}

                profile = UserProfile(
                    name=payload.get("name", "Citizen"),
                    age=int(payload.get("age", 21)),
                    state=payload.get("state", "Uttar Pradesh"),
                    gender=payload.get("gender", Gender.ALL.value),
                    category=payload.get("category", SocialCategory.ALL.value),
                    occupation=payload.get("occupation", Occupation.STUDENT.value),
                    education_level=payload.get("education_level", EducationLevel.NONE.value),
                    annual_family_income=int(payload.get("annual_family_income", 150000)),
                    is_first_gen_student=bool(payload.get("is_first_gen_student", False)),
                    has_disability=bool(payload.get("has_disability", False)),
                    disability_percentage=int(payload.get("disability_percentage", 0)),
                    ration_card=payload.get("ration_card", RationCardType.NONE.value),
                    landholding_acres=float(payload.get("landholding_acres", 0.0)),
                    is_construction_worker=bool(payload.get("is_construction_worker", False)),
                    has_bank_account_aadhaar_linked=bool(payload.get("has_bank_account_aadhaar_linked", True)),
                    existing_documents=payload.get("existing_documents", ["aadhaar_card", "bank_passbook"]),
                )

                plan = rules_engine.generate_readiness_plan(profile)
                plan = explainer.enhance_plan(plan)

                # Format response dictionary
                response_data = {
                    "status": "success",
                    "citizen": profile.to_dict(),
                    "total_evaluated": plan.total_schemes_evaluated,
                    "matched_count": len(plan.matched_schemes),
                    "benefits_summary": plan.total_benefits_unlocked_estimate,
                    "consolidated_checklist": plan.consolidated_document_checklist,
                    "urgent_next_actions": plan.urgent_next_actions,
                    "whatsapp_card": plan.whatsapp_summary_text,
                    "hindi_explanation": plan.hindi_explanation_summary,
                    "matches": [
                        {
                            "scheme": m.scheme.to_dict(),
                            "is_eligible": m.is_eligible,
                            "eligibility_reasons": m.eligibility_reasons,
                            "documents_ready": m.documents_ready,
                            "documents_missing": m.documents_missing,
                            "readiness_score": m.readiness_score,
                            "prerequisite_action_plans": [asdict_prereq(p) for p in m.prerequisite_action_plans]
                        }
                        for m in plan.matched_schemes
                    ]
                }
                self._send_json_response(response_data)
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status_code=400)
        elif parsed.path == "/api/voice/parse":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw_body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(raw_body) if raw_body else {}
                transcript = payload.get("transcript", "") or payload.get("text", "")

                profile, extracted_fields = voice_parser.parse_transcript(transcript)

                plan = rules_engine.generate_readiness_plan(profile)
                plan = explainer.enhance_plan(plan)

                response_data = {
                    "status": "success",
                    "transcript": transcript,
                    "extracted_fields": extracted_fields,
                    "profile": profile.to_dict(),
                    "matched_count": len(plan.matched_schemes),
                    "whatsapp_card": plan.whatsapp_summary_text,
                    "hindi_explanation": plan.hindi_explanation_summary,
                    "matches": [
                        {
                            "scheme": m.scheme.to_dict(),
                            "is_eligible": m.is_eligible,
                            "eligibility_reasons": m.eligibility_reasons,
                            "documents_ready": m.documents_ready,
                            "documents_missing": m.documents_missing,
                            "readiness_score": m.readiness_score,
                            "prerequisite_action_plans": [asdict_prereq(p) for p in m.prerequisite_action_plans]
                        }
                        for m in plan.matched_schemes
                    ]
                }
                self._send_json_response(response_data)
            except Exception as e:
                self._send_json_response({"status": "error", "message": str(e)}, status_code=400)
        else:
            self._send_json_response({"error": "Method Not Allowed on this endpoint"}, status_code=405)


def asdict_prereq(p):
    return {
        "doc_id": p.doc_id,
        "doc_name": p.doc_name,
        "issuing_authority": p.issuing_authority,
        "official_portal_url": p.official_portal_url,
        "required_proofs": p.required_proofs,
        "processing_time_days": p.processing_time_days,
        "estimated_cost_inr": p.estimated_cost_inr,
        "step_by_step_process": p.step_by_step_process,
        "online_available": p.online_available
    }


def run_server(port: int = 8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, SahayakHandler)
    print(f"🚀 Sahayak Web & API Server running at http://localhost:{port}")
    print(f"   - Web UI: http://localhost:{port}/")
    print(f"   - Match API: POST http://localhost:{port}/api/match")
    print(f"   - Schemes API: GET http://localhost:{port}/api/schemes")
    print(f"   - Documents API: GET http://localhost:{port}/api/documents")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
