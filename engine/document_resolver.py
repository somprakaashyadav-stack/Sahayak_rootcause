"""
Sahayak Document Procurement Cascade Resolver
Maps missing documents to concrete, state-specific step-by-step procurement guides,
fees, timelines, and issuing authorities so citizens know HOW to obtain what they lack.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from engine.models import DocumentPrerequisite


class DocumentResolver:
    """Manages the catalog of documents and resolves procurement prerequisites."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            # Default to data/documents.json relative to repository root
            base_dir = Path(__file__).resolve().parent.parent
            data_path = str(base_dir / "data" / "documents.json")

        self.documents_catalog: Dict[str, DocumentPrerequisite] = {}
        self._load_catalog(data_path)

    def _load_catalog(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_docs = json.load(f)
                for item in raw_docs:
                    prereq = DocumentPrerequisite(
                        doc_id=item["doc_id"],
                        doc_name=item["doc_name"],
                        issuing_authority=item["issuing_authority"],
                        official_portal_url=item["official_portal_url"],
                        required_proofs=item["required_proofs"],
                        processing_time_days=item["processing_time_days"],
                        estimated_cost_inr=item["estimated_cost_inr"],
                        step_by_step_process=item["step_by_step_process"],
                        online_available=item.get("online_available", True),
                    )
                    self.documents_catalog[prereq.doc_id] = prereq
        except Exception as e:
            print(f"[Warning] Failed to load documents catalog from {path}: {e}")

    def get_document(self, doc_id: str) -> Optional[DocumentPrerequisite]:
        return self.documents_catalog.get(doc_id)

    def resolve_missing_documents(self, missing_doc_ids: List[str]) -> List[DocumentPrerequisite]:
        """Returns step-by-step resolution plans for each missing document."""
        plans = []
        for doc_id in missing_doc_ids:
            doc = self.get_document(doc_id)
            if doc:
                plans.append(doc)
            else:
                # Generic fallback if a doc_id is not in catalog
                plans.append(
                    DocumentPrerequisite(
                        doc_id=doc_id,
                        doc_name=doc_id.replace("_", " ").title(),
                        issuing_authority="Competent State / Central Authority",
                        official_portal_url="https://www.myscheme.gov.in/",
                        required_proofs=["Identity Proof", "Address Proof"],
                        processing_time_days=14,
                        estimated_cost_inr=50,
                        step_by_step_process=[
                            "Visit nearest Common Service Center (CSC / Jan Seva Kendra).",
                            "Inquire with Village Secretary (Gram Pradhan) or Lekhpal."
                        ],
                        online_available=False
                    )
                )
        return plans
