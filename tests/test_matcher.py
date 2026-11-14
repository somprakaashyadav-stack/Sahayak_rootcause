"""
Unit and Integration Tests for Sahayak Rules Engine and Persona Matching.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


def test_sunita_student_persona():
    """Tests the primary demo persona: 21-year-old female undergraduate student from UP."""
    sunita = UserProfile(
        name="Sunita Yadav",
        age=21,
        state="Uttar Pradesh",
        gender=Gender.FEMALE.value,
        category=SocialCategory.OBC.value,
        occupation=Occupation.STUDENT.value,
        education_level=EducationLevel.UNDERGRADUATE.value,
        annual_family_income=150000,
        is_first_gen_student=True,
        has_disability=False,
        ration_card=RationCardType.APL.value,
        existing_documents=["aadhaar_card", "bank_passbook", "bonafide_admission_proof"]
    )

    engine = RulesEngine()
    plan = engine.generate_readiness_plan(sunita)

    # Assertions
    assert len(plan.matched_schemes) >= 3, f"Expected at least 3 matches, got {len(plan.matched_schemes)}"

    matched_ids = [m.scheme.id for m in plan.matched_schemes]
    print("\n[Test Result] Matched Schemes for Sunita:")
    for m in plan.matched_schemes:
        print(f" - {m.scheme.name} (Readiness: {m.readiness_score}%)")
        print(f"   Reasons: {m.eligibility_reasons[0]}")
        if m.documents_missing:
            print(f"   Missing Docs: {m.documents_missing}")

    assert "up_post_matric_scholarship" in matched_ids, "Should match UP Post-Matric Scholarship"
    assert "up_digishakti_smartphone_tablet" in matched_ids, "Should match DigiShakti Free Smartphone/Tablet"
    assert "up_kanya_sumangala_yojana" in matched_ids, "Should match UP Kanya Sumangala Yojana"

    # Verify Document Cascade for missing Income Certificate
    scholarship_match = next(m for m in plan.matched_schemes if m.scheme.id == "up_post_matric_scholarship")
    assert "income_certificate" in scholarship_match.documents_missing
    prereq_ids = [p.doc_id for p in scholarship_match.prerequisite_action_plans]
    assert "income_certificate" in prereq_ids, "Document cascade must provide resolution for Income Certificate"

    # Verify AI plain language & WhatsApp generator
    explainer = SahayakExplainer()
    enhanced_plan = explainer.enhance_plan(plan)
    assert "Sunita Yadav" in enhanced_plan.whatsapp_summary_text
    assert "edistrict.up.gov.in" in str(enhanced_plan.urgent_next_actions) or "Income Certificate" in str(enhanced_plan.urgent_next_actions)

    print("\n[Test Result] Generated WhatsApp Card Preview:")
    print(enhanced_plan.whatsapp_summary_text)
    print("\n✓ ALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_sunita_student_persona()
