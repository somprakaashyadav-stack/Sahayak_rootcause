"""
Sahayak Deterministic Eligibility Rules Engine
Matches a citizen's profile against structured government schemes.
Provides transparent, explainable predicates for why a citizen qualifies,
and integrates with the Document Resolver to build an actionable readiness plan.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from engine.models import (
    UserProfile,
    Scheme,
    EligibilityRules,
    MatchResult,
    ApplicationReadinessPlan,
    Gender,
    SocialCategory
)
from engine.document_resolver import DocumentResolver


class RulesEngine:
    """Deterministic rules-based matching engine for welfare schemes."""

    def __init__(self, schemes_path: Optional[str] = None, docs_resolver: Optional[DocumentResolver] = None):
        base_dir = Path(__file__).resolve().parent.parent
        if schemes_path is None:
            schemes_path = str(base_dir / "data" / "schemes.json")

        self.resolver = docs_resolver or DocumentResolver()
        self.schemes: List[Scheme] = []
        self._load_schemes(schemes_path)

    def _load_schemes(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                for item in raw_data:
                    rules_raw = item.get("rules", {})
                    rules = EligibilityRules(
                        min_age=rules_raw.get("min_age"),
                        max_age=rules_raw.get("max_age"),
                        applicable_states=rules_raw.get("applicable_states", ["All India"]),
                        applicable_genders=rules_raw.get("applicable_genders", ["all"]),
                        applicable_categories=rules_raw.get("applicable_categories", ["all"]),
                        applicable_occupations=rules_raw.get("applicable_occupations", []),
                        applicable_education_levels=rules_raw.get("applicable_education_levels", []),
                        max_annual_income=rules_raw.get("max_annual_income"),
                        requires_first_gen_student=rules_raw.get("requires_first_gen_student"),
                        requires_disability=rules_raw.get("requires_disability"),
                        min_disability_percentage=rules_raw.get("min_disability_percentage"),
                        allowed_ration_cards=rules_raw.get("allowed_ration_cards", []),
                        max_landholding_acres=rules_raw.get("max_landholding_acres"),
                        requires_construction_worker=rules_raw.get("requires_construction_worker"),
                    )
                    scheme = Scheme(
                        id=item["id"],
                        name=item["name"],
                        hindi_name=item.get("hindi_name", ""),
                        ministry_or_dept=item.get("ministry_or_dept", ""),
                        level=item.get("level", "Central"),
                        state=item.get("state"),
                        category_tag=item.get("category_tag", "General"),
                        benefit_summary=item.get("benefit_summary", ""),
                        benefit_amount_inr=item.get("benefit_amount_inr"),
                        official_url=item.get("official_url", ""),
                        rules=rules,
                        required_document_ids=item.get("required_document_ids", []),
                        application_deadline=item.get("application_deadline", "Open throughout the year"),
                        next_action_steps=item.get("next_action_steps", []),
                    )
                    self.schemes.append(scheme)
        except Exception as e:
            print(f"[Warning] Failed to load schemes from {path}: {e}")

    def evaluate_scheme(self, user: UserProfile, scheme: Scheme) -> MatchResult:
        """Evaluates whether a citizen is eligible for a specific scheme and why."""
        rules = scheme.rules
        reasons: List[str] = []
        missing: List[str] = []

        # 1. State check
        if "All India" in rules.applicable_states:
            reasons.append("Applicable across all Indian States & UTs.")
        elif user.state in rules.applicable_states:
            reasons.append(f"State verified: Citizen resides in {user.state}.")
        else:
            missing.append(f"Restricted to: {', '.join(rules.applicable_states)} (Citizen is in {user.state}).")

        # 2. Age check
        if rules.min_age is not None and user.age < rules.min_age:
            missing.append(f"Minimum age requirement is {rules.min_age} years (Citizen is {user.age}).")
        elif rules.max_age is not None and user.age > rules.max_age:
            missing.append(f"Maximum age ceiling is {rules.max_age} years (Citizen is {user.age}).")
        else:
            if rules.min_age is not None or rules.max_age is not None:
                reasons.append(f"Age criteria met: {user.age} years fits the eligible age band.")

        # 3. Gender check
        user_gender = user.gender.lower()
        if "all" not in rules.applicable_genders and user_gender not in rules.applicable_genders:
            missing.append(f"Scheme is designated specifically for {', '.join(rules.applicable_genders)} applicants.")
        elif "all" not in rules.applicable_genders:
            reasons.append(f"Gender verified: Matches target group ({user.gender}).")

        # 4. Social Category check (SC/ST/OBC/GEN/EWS)
        user_cat = user.category.lower()
        if "all" not in rules.applicable_categories and user_cat not in rules.applicable_categories:
            missing.append(f"Restricted to categories: {', '.join(rules.applicable_categories).upper()}.")
        elif "all" not in rules.applicable_categories:
            reasons.append(f"Category verified: Citizen belongs to eligible category ({user.category.upper()}).")

        # 5. Occupation check
        if rules.applicable_occupations:
            if user.occupation.lower() not in rules.applicable_occupations:
                missing.append(f"Requires occupation in: {', '.join(rules.applicable_occupations)}.")
            else:
                reasons.append(f"Occupation verified: Active {user.occupation.replace('_', ' ')}.")

        # 6. Education Level check
        if rules.applicable_education_levels:
            if user.education_level.lower() not in rules.applicable_education_levels:
                missing.append(f"Requires education level: {', '.join(rules.applicable_education_levels)}.")
            else:
                reasons.append(f"Education level verified: Enrolled at {user.education_level.replace('_', ' ')} level.")

        # 7. Income check
        if rules.max_annual_income is not None:
            if user.annual_family_income > rules.max_annual_income:
                missing.append(
                    f"Family annual income (₹{user.annual_family_income:,}) exceeds the maximum cap of ₹{rules.max_annual_income:,}."
                )
            else:
                reasons.append(
                    f"Income eligible: Family income ₹{user.annual_family_income:,} is within ceiling of ₹{rules.max_annual_income:,}."
                )

        # 8. Disability check
        if rules.requires_disability:
            if not user.has_disability:
                missing.append("Requires recognized disability status.")
            elif rules.min_disability_percentage and user.disability_percentage < rules.min_disability_percentage:
                missing.append(
                    f"Requires minimum {rules.min_disability_percentage}% certified disability (Citizen has {user.disability_percentage}%)."
                )
            else:
                reasons.append("Disability criteria met with valid certification.")

        # 9. Ration card check
        if rules.allowed_ration_cards:
            if user.ration_card.lower() not in rules.allowed_ration_cards:
                missing.append(f"Requires ration card of type: {', '.join(rules.allowed_ration_cards).upper()}.")
            else:
                reasons.append(f"Ration card verified: Eligible {user.ration_card.upper()} card holder.")

        # 10. Landholding check
        if rules.max_landholding_acres is not None:
            if user.landholding_acres > rules.max_landholding_acres:
                missing.append(
                    f"Landholding ({user.landholding_acres} acres) exceeds the maximum limit of {rules.max_landholding_acres} acres."
                )
            else:
                reasons.append(f"Landholding ({user.landholding_acres} acres) is within eligible farmer limits.")

        # 11. Construction worker registration check
        if rules.requires_construction_worker:
            if not user.is_construction_worker:
                missing.append("Requires active registration as a Construction/BOCW Worker.")
            else:
                reasons.append("BOCW construction worker status verified.")

        is_eligible = len(missing) == 0

        # Document readiness evaluation
        docs_ready = []
        docs_missing = []
        for doc_id in scheme.required_document_ids:
            if doc_id in user.existing_documents:
                docs_ready.append(doc_id)
            else:
                docs_missing.append(doc_id)

        prereq_plans = self.resolver.resolve_missing_documents(docs_missing)

        # Readiness Score: 0 to 100
        if not is_eligible:
            readiness_score = 0
        else:
            total_docs = len(scheme.required_document_ids)
            if total_docs == 0:
                readiness_score = 100
            else:
                readiness_score = int((len(docs_ready) / total_docs) * 100)

        return MatchResult(
            scheme=scheme,
            is_eligible=is_eligible,
            eligibility_reasons=reasons,
            missing_criteria=missing,
            documents_ready=docs_ready,
            documents_missing=docs_missing,
            prerequisite_action_plans=prereq_plans,
            readiness_score=readiness_score,
        )

    def generate_readiness_plan(self, user: UserProfile) -> ApplicationReadinessPlan:
        """Runs the complete evaluation and generates a consolidated readiness plan."""
        matched: List[MatchResult] = []
        consolidated_checklist: Dict[str, bool] = {}
        urgent_actions: List[str] = []

        for scheme in self.schemes:
            result = self.evaluate_scheme(user, scheme)
            if result.is_eligible:
                matched.append(result)
                for doc_id in scheme.required_document_ids:
                    doc_obj = self.resolver.get_document(doc_id)
                    name = doc_obj.doc_name if doc_obj else doc_id
                    has_it = doc_id in user.existing_documents
                    consolidated_checklist[name] = has_it

        # Sort matched schemes by readiness score descending
        matched.sort(key=lambda x: x.readiness_score, reverse=True)

        # Generate top urgent actions
        for res in matched:
            if res.documents_missing:
                first_missing_id = res.documents_missing[0]
                prereq = self.resolver.get_document(first_missing_id)
                if prereq:
                    urgent_actions.append(
                        f"Procure {prereq.doc_name}: Apply at {prereq.official_portal_url} (~{prereq.processing_time_days} days)."
                    )
            elif res.scheme.next_action_steps:
                urgent_actions.append(f"Apply for {res.scheme.name}: {res.scheme.next_action_steps[0]}")

        # Deduplicate urgent actions
        unique_urgent = list(dict.fromkeys(urgent_actions))[:5]

        # Calculate rough unlocked benefit estimation
        total_benefit_str = f"{len(matched)} schemes unlocked"

        return ApplicationReadinessPlan(
            citizen_profile=user,
            matched_schemes=matched,
            total_schemes_evaluated=len(self.schemes),
            total_benefits_unlocked_estimate=total_benefit_str,
            consolidated_document_checklist=consolidated_checklist,
            urgent_next_actions=unique_urgent,
        )
