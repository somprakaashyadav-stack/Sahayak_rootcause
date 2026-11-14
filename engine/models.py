"""
Sahayak Core Data Models
Provides structured schemas for User Profiles, Scheme Rules, Document Requirements,
and Application Readiness Plans. Built with Python dataclasses for zero-dependency portability.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum


class Gender(str, Enum):
    ALL = "all"
    MALE = "male"
    FEMALE = "female"
    TRANSGENDER = "transgender"


class SocialCategory(str, Enum):
    ALL = "all"
    GENERAL = "general"
    OBC = "obc"
    SC = "sc"
    ST = "st"
    EWS = "ews"


class EducationLevel(str, Enum):
    NONE = "none"
    PRIMARY = "primary"
    SECONDARY = "secondary"        # up to 10th
    HIGHER_SECONDARY = "higher_secondary"  # 12th
    UNDERGRADUATE = "undergraduate"
    POSTGRADUATE = "postgraduate"
    DIPLOMA = "diploma"
    ITI = "iti"


class Occupation(str, Enum):
    STUDENT = "student"
    FARMER = "farmer"
    DAILY_WAGE_LABORER = "daily_wage_laborer"
    SELF_EMPLOYED = "self_employed"
    STREET_VENDOR = "street_vendor"
    UNEMPLOYED = "unemployed"
    HOMEMAKER = "homemaker"
    SALARIED = "salaried"
    RETIRED = "retired"


class RationCardType(str, Enum):
    NONE = "none"
    APL = "apl"                  # Above Poverty Line
    BPL = "bpl"                  # Below Poverty Line
    AAY = "aay"                  # Antyodaya Anna Yojana (Poorest of poor)


@dataclass
class UserProfile:
    """Represents a citizen's 8-10 question input profile."""
    name: str = "Citizen"
    age: int = 18
    state: str = "Uttar Pradesh"
    district: Optional[str] = None
    gender: str = Gender.ALL.value
    category: str = SocialCategory.ALL.value
    occupation: str = Occupation.UNEMPLOYED.value
    education_level: str = EducationLevel.NONE.value
    annual_family_income: int = 150000
    is_first_gen_student: bool = False
    has_disability: bool = False
    disability_percentage: int = 0
    ration_card: str = RationCardType.NONE.value
    landholding_acres: float = 0.0
    is_construction_worker: bool = False
    has_bank_account_aadhaar_linked: bool = True
    existing_documents: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentPrerequisite:
    """Explains how to obtain a document if the citizen doesn't have it."""
    doc_id: str
    doc_name: str
    issuing_authority: str
    official_portal_url: str
    required_proofs: List[str]
    processing_time_days: int
    estimated_cost_inr: int
    step_by_step_process: List[str]
    online_available: bool = True


@dataclass
class EligibilityRules:
    """Deterministic eligibility conditions for a scheme."""
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    applicable_states: List[str] = field(default_factory=lambda: ["All India"])
    applicable_genders: List[str] = field(default_factory=lambda: [Gender.ALL.value])
    applicable_categories: List[str] = field(default_factory=lambda: [SocialCategory.ALL.value])
    applicable_occupations: List[str] = field(default_factory=list)
    applicable_education_levels: List[str] = field(default_factory=list)
    max_annual_income: Optional[int] = None
    requires_first_gen_student: Optional[bool] = None
    requires_disability: Optional[bool] = None
    min_disability_percentage: Optional[int] = None
    allowed_ration_cards: List[str] = field(default_factory=list)
    max_landholding_acres: Optional[float] = None
    requires_construction_worker: Optional[bool] = None


@dataclass
class Scheme:
    """Full definition of a central or state welfare scheme."""
    id: str
    name: str
    hindi_name: str
    ministry_or_dept: str
    level: str  # "Central" or "State"
    state: Optional[str] = None
    category_tag: str = "General"  # e.g., Education, Agriculture, Social Security, Health
    benefit_summary: str = ""
    benefit_amount_inr: Optional[str] = None
    official_url: str = ""
    rules: EligibilityRules = field(default_factory=EligibilityRules)
    required_document_ids: List[str] = field(default_factory=list)
    application_deadline: Optional[str] = "Open throughout the year"
    next_action_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchResult:
    """Result of evaluating a citizen against a scheme."""
    scheme: Scheme
    is_eligible: bool
    eligibility_reasons: List[str] = field(default_factory=list)
    missing_criteria: List[str] = field(default_factory=list)
    documents_ready: List[str] = field(default_factory=list)
    documents_missing: List[str] = field(default_factory=list)
    prerequisite_action_plans: List[DocumentPrerequisite] = field(default_factory=list)
    readiness_score: int = 0  # 0 to 100 based on eligibility and document availability


@dataclass
class ApplicationReadinessPlan:
    """Comprehensive personalized welfare roadmap for a citizen."""
    citizen_profile: UserProfile
    matched_schemes: List[MatchResult] = field(default_factory=list)
    total_schemes_evaluated: int = 0
    total_benefits_unlocked_estimate: str = ""
    consolidated_document_checklist: Dict[str, bool] = field(default_factory=dict)
    urgent_next_actions: List[str] = field(default_factory=list)
    whatsapp_summary_text: str = ""
    hindi_explanation_summary: str = ""
