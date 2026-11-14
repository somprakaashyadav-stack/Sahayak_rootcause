"""
Sahayak Interactive CLI
Allows citizens, NGO workers, or hackathon judges to interactively run scheme matching,
test realistic personas, and view instant WhatsApp action plans.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

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


PERSONAS = {
    "1": {
        "title": "Sunita (21, Undergraduate Female Student, UP, Low Income)",
        "profile": UserProfile(
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
    },
    "2": {
        "title": "Ramesh (42, Smallholder Farmer, UP, PM-KISAN & Ayushman target)",
        "profile": UserProfile(
            name="Ramesh Kumar",
            age=42,
            state="Uttar Pradesh",
            gender=Gender.MALE.value,
            category=SocialCategory.SC.value,
            occupation=Occupation.FARMER.value,
            education_level=EducationLevel.PRIMARY.value,
            annual_family_income=90000,
            is_first_gen_student=False,
            has_disability=False,
            landholding_acres=2.0,
            ration_card=RationCardType.BPL.value,
            existing_documents=["aadhaar_card", "bank_passbook", "land_khatauni", "ration_card"]
        )
    },
    "3": {
        "title": "Munni Devi (35, Daily Wage Construction Worker, BOCW / Ujjwala target)",
        "profile": UserProfile(
            name="Munni Devi",
            age=35,
            state="Uttar Pradesh",
            gender=Gender.FEMALE.value,
            category=SocialCategory.OBC.value,
            occupation=Occupation.DAILY_WAGE_LABORER.value,
            education_level=EducationLevel.NONE.value,
            annual_family_income=80000,
            is_construction_worker=True,
            ration_card=RationCardType.BPL.value,
            existing_documents=["aadhaar_card", "bank_passbook", "bocw_labor_card", "ration_card"]
        )
    },
    "4": {
        "title": "Mohan (28, Urban Street Vendor, PM SVANidhi target)",
        "profile": UserProfile(
            name="Mohan Lal",
            age=28,
            state="Uttar Pradesh",
            gender=Gender.MALE.value,
            category=SocialCategory.GENERAL.value,
            occupation=Occupation.STREET_VENDOR.value,
            education_level=EducationLevel.SECONDARY.value,
            annual_family_income=120000,
            ration_card=RationCardType.APL.value,
            existing_documents=["aadhaar_card", "bank_passbook"]
        )
    }
}


def print_banner():
    print("=" * 65)
    print("      🇮🇳  SAHAYAK (सहायक) - CITIZEN WELFARE COPILOT  🇮🇳")
    print("    Personalized Scheme Discovery & Application-Readiness")
    print("=" * 65)


def run_evaluation(profile: UserProfile):
    engine = RulesEngine()
    explainer = SahayakExplainer()

    print(f"\n🔍 Evaluating {len(engine.schemes)} schemes against {profile.name}'s profile...")
    plan = engine.generate_readiness_plan(profile)
    plan = explainer.enhance_plan(plan)

    print("\n" + "=" * 65)
    print(f"🎯 MATCH RESULTS: {len(plan.matched_schemes)} Eligible Schemes Found!")
    print("=" * 65)

    for i, match in enumerate(plan.matched_schemes, 1):
        s = match.scheme
        readiness_badge = "🟢 READY TO APPLY" if match.readiness_score >= 80 else f"🟡 DOCS NEEDED ({match.readiness_score}%)"
        print(f"\n[{i}] {s.name} ({s.hindi_name})")
        print(f"    Category: {s.category_tag} | Level: {s.level}")
        print(f"    Benefit: {s.benefit_summary}")
        print(f"    Status: {readiness_badge}")
        print(f"    Official Link: {s.official_url}")
        print("    Why You Qualify:")
        for reason in match.eligibility_reasons[:3]:
            print(f"      ✓ {reason}")

        if match.documents_missing:
            print("    Missing Documents & How to Procure:")
            for prereq in match.prerequisite_action_plans[:2]:
                print(f"      ⚠️  {prereq.doc_name} -> Apply at {prereq.official_portal_url} (~{prereq.processing_time_days} days)")

    print("\n" + "=" * 65)
    print("📱 WHATSAPP ACTION PACKET (Ready to Share with Citizen/CSC):")
    print("=" * 65)
    print(plan.whatsapp_summary_text)


def interactive_mode():
    print_banner()
    print("\nSelect an option:")
    print("  [1] Sunita (21, Undergraduate Female Student, UP - Demo Persona)")
    print("  [2] Ramesh (42, Smallholder Farmer, UP)")
    print("  [3] Munni Devi (35, Daily Wage Construction Worker, UP)")
    print("  [4] Mohan (28, Urban Street Vendor, UP)")
    print("  [5] Custom Interactive Questionnaire (Enter your own profile)")
    print("  [Q] Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice in PERSONAS:
        selected = PERSONAS[choice]
        print(f"\nLoaded Persona: {selected['title']}")
        run_evaluation(selected["profile"])
    elif choice == "5":
        name = input("Enter Name [Citizen]: ").strip() or "Citizen"
        age = int(input("Enter Age [21]: ").strip() or 21)
        gender = input("Gender (female/male/other) [female]: ").strip() or "female"
        state = input("State [Uttar Pradesh]: ").strip() or "Uttar Pradesh"
        occupation = input("Occupation (student/farmer/daily_wage_laborer/street_vendor/unemployed) [student]: ").strip() or "student"
        income = int(input("Annual Family Income in INR [150000]: ").strip() or 150000)
        category = input("Category (general/obc/sc/st/ews) [obc]: ").strip() or "obc"
        education = input("Education Level (none/secondary/higher_secondary/undergraduate/postgraduate) [undergraduate]: ").strip() or "undergraduate"

        profile = UserProfile(
            name=name,
            age=age,
            gender=gender,
            state=state,
            occupation=occupation,
            annual_family_income=income,
            category=category,
            education_level=education,
            existing_documents=["aadhaar_card", "bank_passbook"]
        )
        run_evaluation(profile)
    else:
        print("Exiting.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in PERSONAS:
        run_evaluation(PERSONAS[sys.argv[1]]["profile"])
    else:
        interactive_mode()
