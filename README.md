# Sahayak (सहायक) - Citizen Welfare Application-Readiness Copilot

> **Converting scattered government scheme information into a personalized, step-by-step action plan for every citizen.**

---

## 📌 Executive Summary

India has thousands of central and state welfare schemes (**myScheme** alone catalogs over 5,000 schemes). However, eligible citizens—especially students, rural families, daily-wage laborers, and first-generation applicants—consistently drop out during the application process.

### The Problem: The "Last-Mile Action Gap"
1. **Scattered Discovery**: Citizens struggle to find which schemes apply to their exact demographic situation.
2. **Eligibility Ambiguity**: Bureaucratic language confuses applicants about income caps, category quotas, and age cutoffs.
3. **The Document Cascade Deadlock**: A scheme requires an *Income Certificate*, but citizens do not know how to obtain an Income Certificate (issuing authority, portal, required proofs, timeline, and fee).
4. **Channel Mismatch**: Rural and daily-wage citizens do not navigate complex desktop portals with captchas; they use messaging channels like **WhatsApp**.

---

## 💡 The Sahayak Solution

Sahayak is an **Application-Readiness Copilot** (Web + WhatsApp):
- **Deterministic Rules Engine**: Completely transparent, 100% explainable matching decoupled from LLM hallucinations.
- **Document Procurement Cascade**: Doesn't just say *"You need Document X"*; provides state-specific step-by-step instructions on *how to obtain Document X* (authority, fee, portal, turnaround days).
- **AI Plain-Language & WhatsApp Layer**: Translates bureaucratic criteria into simple Hindi/English action cards that can be shared with parents, CSC operators, or NGO volunteers.

```
[Citizen Profile]
   (8-10 Questions: Age, State, Category, Income, Occupation, Docs)
         │
         ▼
[Deterministic Rules Engine] ─── evaluates ───► [Curated Schemes Database]
         │                                              │
         ├──────────────────────────────────────────────┘
         ▼
[Matched Schemes + Reasons for Qualification]
         │
         ▼
[Document Dependency Cascade Resolver] ───► [State Document Procurement DB]
         │                                   (Tehsildar / e-District / UIDAI)
         ▼
[AI Plain-Language Explainer & WhatsApp Card Generator]
         │
         ▼
[Actionable Output: Web Dashboard / Ready-to-Send WhatsApp Packet]
```

---

## 🗂️ Project Structure

```
Sahayak_rootcause/
├── data/
│   ├── schemes.json            # 15+ Central & UP Welfare schemes with deterministic rules
│   └── documents.json          # 10+ core welfare documents with procurement workflows
├── engine/
│   ├── models.py               # Zero-dependency dataclass models (UserProfile, Scheme, Plan)
│   ├── matcher.py              # Transparent deterministic rules engine & readiness scorer
│   └── document_resolver.py    # Document dependency cascade & procurement resolver
├── ai/
│   └── explainer.py            # Plain Hindi explanation & formatted WhatsApp Action Cards
├── api/
│   └── server.py               # Lightweight zero-dependency HTTP REST API & static web server
├── frontend/
│   └── index.html              # Responsive Tailwind CSS web app with preset demo personas
├── tests/
│   ├── test_matcher.py         # Unit & integration tests for Sunita (student persona)
│   └── test_api_server.py      # In-memory API integration test suite
├── cli.py                      # Interactive CLI & 1-click persona evaluator
└── README.md                   # Full documentation & project guide
```

---

## 🚀 Quick Start Guide

### Prerequisites
Python 3.10+ (Standard Library only; no mandatory external pip dependencies required).

### 1. Run the Interactive CLI
Evaluate demo personas or test your own profile directly in the terminal:
```bash
python cli.py
```
Or run a specific persona directly:
```bash
# Sunita (21, Undergraduate UP Female Student)
python cli.py 1

# Ramesh (42, Smallholder Farmer)
python cli.py 2

# Munni Devi (35, Daily Wage Construction Worker)
python cli.py 3

# Mohan (28, Urban Street Vendor)
python cli.py 4
```

### 2. Run the Web Dashboard & REST API Server
Start the local server:
```bash
python api/server.py 8000
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser to interact with the responsive web interface.

### 3. Run Automated Tests
```bash
# Test Rules Engine & Persona Matching
python tests/test_matcher.py

# Test API Endpoints & Request Handlers
python tests/test_api_server.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check endpoint |
| `GET` | `/api/schemes` | Returns catalog of all available welfare schemes |
| `GET` | `/api/documents` | Returns catalog of documents with procurement steps |
| `POST` | `/api/match` | Takes citizen profile JSON and returns matched schemes, readiness scores, document cascade, and WhatsApp card |

### Sample `POST /api/match` Request Payload:
```json
{
  "name": "Sunita Yadav",
  "age": 21,
  "state": "Uttar Pradesh",
  "gender": "female",
  "category": "obc",
  "occupation": "student",
  "education_level": "undergraduate",
  "annual_family_income": 150000,
  "ration_card": "apl",
  "existing_documents": ["aadhaar_card", "bank_passbook", "bonafide_admission_proof"]
}
```

---

## 📱 WhatsApp Action Card Output Example

```text
🇮🇳 *सड़क से संसद तक - सहायक (Sahayak) योजना मित्र*
👤 *नागरिक:* Sunita Yadav (21 वर्ष | Uttar Pradesh)
📋 *पेशा:* Student | *आय:* ₹150,000/वर्ष
━━━━━━━━━━━━━━━━━━━━
🎉 *बधाई! आपके लिए 4 योजनाएं उपलब्ध हैं:*

*1. PM Kaushal Vikas Yojana 4.0 (PMKVY)*
   💰 *लाभ:* 100% free industry-certified skill training + ₹8,000 reward stipend
   📊 *स्थिति:* 🟢 तैयार (Ready) (तैयारी: 100%)
   🔗 *ऑफिशियल पोर्टल:* https://www.pmkvyofficial.org/

*2. Swami Vivekananda Youth Empowerment Scheme (DigiShakti)*
   💰 *लाभ:* Free 5G/4G Smartphone or Tablet with educational apps
   📊 *स्थिति:* 🟡 कुछ दस्तावेज बाकी (तैयारी: 66%)
   ⚠️ *अधूरे दस्तावेज:* • Domicile Certificate

*3. UP Mukhyamantri Kanya Sumangala Yojana*
   💰 *लाभ:* ₹25,000 phased educational assistance
   📊 *स्थिति:* 🟡 कुछ दस्तावेज बाकी (तैयारी: 60%)
   ⚠️ *अधूरे दस्तावेज:* • Income Certificate, • Domicile Certificate

*4. UP Post-Matric Scholarship & Fee Reimbursement Scheme*
   💰 *लाभ:* 100% tuition fee reimbursement up to ₹50,000
   📊 *स्थिति:* 🟡 कुछ दस्तावेज बाकी (तैयारी: 50%)
   ⚠️ *अधूरे दस्तावेज:* • Income Certificate, • Caste Certificate

━━━━━━━━━━━━━━━━━━━━
📌 *तुरंत करने योग्य कार्य (Next Steps):*
👉 Procure Domicile Certificate: Apply at https://edistrict.up.gov.in/ (~10 days).
👉 Procure Income Certificate: Apply at https://edistrict.up.gov.in/ (~15 days).
```

---

## 🏛️ Schemes Currently Curated (15 Schemes)

1. **UP Post-Matric Scholarship & Fee Reimbursement Scheme**
2. **Swami Vivekananda Youth Empowerment Scheme (DigiShakti Free Smartphone/Tablet)**
3. **PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)**
4. **Ayushman Bharat - PM Jan Arogya Yojana (PM-JAY)**
5. **UP Mukhyamantri Kanya Sumangala Yojana**
6. **UP BOCW Sant Ravidas Shiksha Protsahan Yojana (Shramik Scholarship)**
7. **PM SVANidhi (Street Vendor Loan & Cashback Scheme)**
8. **Pradhan Mantri Ujjwala Yojana 2.0 (Free LPG Connection)**
9. **Atal Pension Yojana (Guaranteed Monthly Pension)**
10. **Sukanya Samriddhi Yojana (Girl Child Savings)**
11. **UP Vridhavastha Pension Yojana (Old Age Pension)**
12. **PM Kaushal Vikas Yojana 4.0 (Skill Training & Certification)**
13. **UP Vivah Hetu Anudan Yojana (Marriage Assistance)**
14. **Pradhan Mantri Awas Yojana - Gramin (PMAY-G Housing)**
15. **UP Divyangjan Pension Scheme (Disability Assistance)**
