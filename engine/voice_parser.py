"""
Sahayak Voice & Speech NLP Entity Extractor
Parses voice transcripts in Hindi, Hinglish, and English into structured UserProfile objects.
Designed for rural citizens, students, and low-literacy users speaking naturally.
"""

import re
from typing import Dict, Any, List, Tuple
from engine.models import (
    UserProfile,
    Gender,
    SocialCategory,
    EducationLevel,
    Occupation,
    RationCardType
)


class VoiceProfileParser:
    """Extracts citizen demographic & economic attributes from spoken audio transcripts."""

    HINDI_NUMBERS = {
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5,
        "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
        "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15,
        "सोलह": 16, "सत्रह": 17, "अट्ठारह": 18, "उन्नीस": 19, "बीस": 20,
        "इक्कीस": 21, "बाईस": 22, "तेईस": 23, "चौबीस": 24, "पच्चीस": 25,
        "छब्बीस": 26, "सत्ताईस": 27, "अट्ठाइस": 28, "उनतीस": 29, "तीस": 30,
        "पैंतीस": 35, "चालीस": 40, "पैंतालीस": 45, "पचास": 50, "पचपन": 55,
        "साठ": 60, "पैंसठ": 65, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
    }

    def parse_transcript(self, text: str) -> Tuple[UserProfile, List[str]]:
        """Parses speech text and returns a populated UserProfile along with list of extracted fields."""
        if not text:
            return UserProfile(), []

        extracted_fields = []
        raw_lower = text.lower()
        profile = UserProfile()

        # 1. Extract Name
        # e.g., "मेरा नाम सुनीता यादव है", "my name is Sunita", "I am Ramesh Kumar"
        name_patterns = [
            r"(?:मेरा नाम|नाम है|नाम)\s+([A-Za-z\u0900-\u097F]+(?:\s+[A-Za-z\u0900-\u097F]+)?)(?:\s+है|\s+हूँ|\s+hu|\s+hai|\s+ji|\s+जी)?",
            r"(?:my name is|i am|this is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)"
        ]
        for pat in name_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                extracted_name = m.group(1).strip()
                # Clean trailing words if any leaked
                for stop_word in [" है", " हूँ", " hai", " hu"]:
                    if extracted_name.endswith(stop_word):
                        extracted_name = extracted_name[:-len(stop_word)].strip()
                # Filter out stop words that could be captured
                if extracted_name.lower() not in ["एक", "a", "an", "the", "hai", "है", "हूं", "हूँ"]:
                    profile.name = extracted_name.title()
                    extracted_fields.append(f"Name: {profile.name}")
                    break

        # 2. Extract Age
        # e.g., "21 साल", "उम्र 21", "21 years old", "age is 25", "इक्कीस वर्ष"
        age_patterns = [
            r"(\d{1,2})\s*(?:साल|वर्ष|years|year|yr)",
            r"(?:उम्र|age|आयु)\s*(?:is|है)?\s*(\d{1,2})",
            r"(\d{1,2})\s*(?:की हूँ|का हूँ|ki hu|ka hu)"
        ]
        found_age = False
        for pat in age_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    profile.age = int(m.group(1))
                    found_age = True
                    extracted_fields.append(f"Age: {profile.age} years")
                    break
                except ValueError:
                    pass

        if not found_age:
            for word, val in self.HINDI_NUMBERS.items():
                if f"{word} साल" in text or f"{word} वर्ष" in text or f"उम्र {word}" in text:
                    profile.age = val
                    extracted_fields.append(f"Age: {profile.age} years")
                    break

        # 3. Extract State
        # e.g., "उत्तर प्रदेश", "यूपी", "UP", "बिहार", "मध्य प्रदेश"
        if any(k in text for k in ["उत्तर प्रदेश", "उत्तरप्रदेश", "यूपी", "UP", "Uttar Pradesh", "up"]):
            profile.state = "Uttar Pradesh"
            extracted_fields.append("State: Uttar Pradesh")
        elif any(k in text for k in ["बिहार", "Bihar", "bihar"]):
            profile.state = "Bihar"
            extracted_fields.append("State: Bihar")
        elif any(k in text for k in ["मध्य प्रदेश", "मध्यप्रदेश", "MP", "Madhya Pradesh"]):
            profile.state = "Madhya Pradesh"
            extracted_fields.append("State: Madhya Pradesh")
        elif any(k in text for k in ["राजस्थान", "Rajasthan"]):
            profile.state = "Rajasthan"
            extracted_fields.append("State: Rajasthan")

        # 4. Extract Gender
        # e.g., "महिला", "लड़की", "छात्रा", "woman", "female" vs "पुरुष", "लड़का", "छात्र", "male"
        female_keywords = ["महिला", "लड़की", "छात्रा", "औरत", "female", "woman", "girl", "daughter", "बेटी"]
        male_keywords = ["पुरुष", "लड़का", "छात्र", "आदमी", "male", "man", "boy", "son", "बेटा"]

        if any(k in raw_lower for k in female_keywords):
            profile.gender = Gender.FEMALE.value
            extracted_fields.append("Gender: Female (महिला)")
        elif any(k in raw_lower for k in male_keywords):
            profile.gender = Gender.MALE.value
            extracted_fields.append("Gender: Male (पुरुष)")

        # 5. Extract Social Category
        # e.g., "ओबीसी", "obc", "पिछड़ा", "एससी", "sc", "एसटी", "st", "सामान्य", "general"
        if any(k in raw_lower for k in ["ओबीसी", "obc", "पिछड़ा वर्ग", "other backward"]):
            profile.category = SocialCategory.OBC.value
            extracted_fields.append("Category: OBC (अन्य पिछड़ा वर्ग)")
        elif any(k in raw_lower for k in ["एससी", "sc", "अनुसूचित जाति", "dalit", "scheduled caste"]):
            profile.category = SocialCategory.SC.value
            extracted_fields.append("Category: SC (अनुसूचित जाति)")
        elif any(k in raw_lower for k in ["एसटी", "st", "अनुसूचित जनजाति", "adivasi", "scheduled tribe"]):
            profile.category = SocialCategory.ST.value
            extracted_fields.append("Category: ST (अनुसूचित जनजाति)")
        elif any(k in raw_lower for k in ["ईडब्ल्यूएस", "ews", "economically weaker"]):
            profile.category = SocialCategory.EWS.value
            extracted_fields.append("Category: EWS")
        elif any(k in raw_lower for k in ["सामान्य", "general", "unreserved"]):
            profile.category = SocialCategory.GENERAL.value
            extracted_fields.append("Category: General")

        # 6. Extract Occupation
        # e.g., "छात्रा", "विद्यार्थी", "student", "किसान", "farmer", "मजदूर", "laborer", "रेहड़ी", "vendor"
        if any(k in raw_lower for k in ["छात्र", "छात्रा", "विद्यार्थी", "कॉलेज", "student", "study", "पढ़ाई", "b.a", "b.sc", "b.com"]):
            profile.occupation = Occupation.STUDENT.value
            extracted_fields.append("Occupation: Student (विद्यार्थी)")
        elif any(k in raw_lower for k in ["किसान", "खेती", "कृषि", "farmer", "farming", "agriculture"]):
            profile.occupation = Occupation.FARMER.value
            extracted_fields.append("Occupation: Farmer (किसान)")
        elif any(k in raw_lower for k in ["मजदूर", "श्रमिक", "दिहाड़ी", "labor", "labourer", "worker", "construction", "bocw", "मिस्त्री"]):
            profile.occupation = Occupation.DAILY_WAGE_LABORER.value
            profile.is_construction_worker = True
            extracted_fields.append("Occupation: Daily-Wage Laborer (श्रमिक)")
        elif any(k in raw_lower for k in ["रेहड़ी", "पटरी", "ठेला", "फेरीवाला", "वेंडर", "street vendor", "vendor", "stall"]):
            profile.occupation = Occupation.STREET_VENDOR.value
            extracted_fields.append("Occupation: Street Vendor (रेहड़ी पटरी)")
        elif any(k in raw_lower for k in ["दुकान", "व्यवसाय", "व्यापार", "self employed", "business"]):
            profile.occupation = Occupation.SELF_EMPLOYED.value
            extracted_fields.append("Occupation: Self-Employed")
        elif any(k in raw_lower for k in ["बेरोजगार", "unemployed", "jobless", "काम की तलाश"]):
            profile.occupation = Occupation.UNEMPLOYED.value
            extracted_fields.append("Occupation: Unemployed")
        elif any(k in raw_lower for k in ["वृद्ध", "बुजुर्ग", "पेंशन", "retired", "senior citizen"]):
            profile.occupation = Occupation.RETIRED.value
            extracted_fields.append("Occupation: Senior Citizen")

        # 7. Extract Education Level
        if any(k in raw_lower for k in ["बीए", "बीएससी", "बीकॉम", "ग्रेजुएट", "स्नातक", "डिग्री", "college", "undergraduate", "b.a", "b.sc"]):
            profile.education_level = EducationLevel.UNDERGRADUATE.value
            extracted_fields.append("Education: Undergraduate (Degree)")
        elif any(k in raw_lower for k in ["एमए", "एमएससी", "पोस्ट ग्रेजुएट", "postgraduate", "m.a", "m.sc", "masters"]):
            profile.education_level = EducationLevel.POSTGRADUATE.value
            extracted_fields.append("Education: Postgraduate")
        elif any(k in raw_lower for k in ["12वीं", "बारहवीं", "इंटर", "12th", "higher secondary"]):
            profile.education_level = EducationLevel.HIGHER_SECONDARY.value
            extracted_fields.append("Education: Class 12th Pass")
        elif any(k in raw_lower for k in ["10वीं", "दसवीं", "हाईस्कूल", "10th", "matric"]):
            profile.education_level = EducationLevel.SECONDARY.value
            extracted_fields.append("Education: Class 10th Pass")
        elif any(k in raw_lower for k in ["डिप्लोमा", "आईटीआई", "iti", "diploma", "polytechnic"]):
            profile.education_level = EducationLevel.DIPLOMA.value
            extracted_fields.append("Education: Diploma / ITI")
        elif any(k in raw_lower for k in ["पढ़ा लिखा नहीं", "अशिक्षित", "no schooling", "illiterate"]):
            profile.education_level = EducationLevel.NONE.value
            extracted_fields.append("Education: No Formal Schooling")

        # 8. Extract Annual Income
        # Common Indian spoken income phrases:
        # "डेढ़ लाख" -> 150000, "ढाई लाख" -> 250000, "दो लाख" -> 200000, "एक लाख" -> 100000
        # "80 हजार", "90,000", "1.5 lakh"
        income_patterns = [
            (r"डेढ़\s*लाख|1\.5\s*(?:लाख|lakh)", 150000),
            (r"ढाई\s*लाख|2\.5\s*(?:लाख|lakh)", 250000),
            (r"साढ़े\s*तीन\s*लाख|3\.5\s*(?:लाख|lakh)", 350000),
            (r"सवा\s*लाख|1\.25\s*(?:लाख|lakh)", 125000),
            (r"एक\s*लाख|1\s*(?:लाख|lakh)", 100000),
            (r"दो\s*लाख|2\s*(?:लाख|lakh)", 200000),
            (r"तीन\s*लाख|3\s*(?:लाख|lakh)", 300000),
            (r"चार\s*लाख|4\s*(?:लाख|lakh)", 400000),
            (r"पांच\s*लाख|5\s*(?:लाख|lakh)", 500000),
            (r"(?:अस्सी|80)\s*(?:हजार|हज़ार|thousand)", 80000),
            (r"(?:नब्बे|90)\s*(?:हजार|हज़ार|thousand)", 90000),
            (r"(?:सत्तर|70)\s*(?:हजार|हज़ार|thousand)", 70000),
            (r"(?:साठ|60)\s*(?:हजार|हज़ार|thousand)", 60000),
            (r"(?:पचास|50)\s*(?:हजार|हज़ार|thousand)", 50000),
            (r"(?:₹|rs\.?|inr)?\s*(\d{5,7})", None)  # Numeric e.g., 150000 or 90000
        ]
        for pat, val in income_patterns:
            if val is not None:
                if re.search(pat, text, re.IGNORECASE):
                    profile.annual_family_income = val
                    extracted_fields.append(f"Annual Income: ₹{val:,}")
                    break
            else:
                m = re.search(pat, text, re.IGNORECASE)
                if m:
                    try:
                        num = int(m.group(1))
                        if 10000 <= num <= 2000000:
                            profile.annual_family_income = num
                            extracted_fields.append(f"Annual Income: ₹{num:,}")
                            break
                    except ValueError:
                        pass

        # 9. Extract Ration Card Status
        if any(k in raw_lower for k in ["बीपीएल", "bpl", "पीला राशन कार्ड", "yellow card"]):
            profile.ration_card = RationCardType.BPL.value
            extracted_fields.append("Ration Card: BPL")
        elif any(k in raw_lower for k in ["अंत्योदय", "antyodaya", "aay", "लाल राशन कार्ड", "red card"]):
            profile.ration_card = RationCardType.AAY.value
            extracted_fields.append("Ration Card: Antyodaya (AAY)")

        # 9.5 Extract Landholding (Acres)
        land_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:एकड़|एकड|acre|acres|बीघा|bigha)", text, re.IGNORECASE)
        if land_match:
            try:
                acres = float(land_match.group(1))
                if "बीघा" in text or "bigha" in text.lower():
                    acres = acres * 0.625  # Standard UP bigha to acre approx
                profile.landholding_acres = round(acres, 1)
                extracted_fields.append(f"Land: {profile.landholding_acres} Acres")
            except ValueError:
                pass

        # 10. Extract Document Mentions
        docs = ["aadhaar_card", "bank_passbook"]
        if any(k in raw_lower for k in ["आय प्रमाण", "income cert", "aay praman"]):
            docs.append("income_certificate")
        if any(k in raw_lower for k in ["जाति प्रमाण", "caste cert", "jati praman"]):
            docs.append("caste_certificate")
        if any(k in raw_lower for k in ["निवास प्रमाण", "domicile", "niwas praman"]):
            docs.append("domicile_certificate")
        if profile.occupation == Occupation.STUDENT.value:
            docs.append("bonafide_admission_proof")
        if profile.is_construction_worker:
            docs.append("bocw_labor_card")

        profile.existing_documents = list(set(docs))

        return profile, extracted_fields
