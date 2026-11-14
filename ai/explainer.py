"""
Sahayak AI Plain-Language Explainer & WhatsApp Card Formatter
Converts deterministic match results into simple, empathetic explanations
in Hindi and English, and produces ready-to-share WhatsApp message packets.
"""

from typing import Optional
from engine.models import ApplicationReadinessPlan, UserProfile


class SahayakExplainer:
    """Generates citizen-friendly plain language summaries and WhatsApp cards."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def format_whatsapp_message(self, plan: ApplicationReadinessPlan) -> str:
        """Formats the matched plan into a structured, readable WhatsApp message."""
        u = plan.citizen_profile
        lines = [
            f"🇮🇳 *सड़क से संसद तक - सहायक (Sahayak) योजना मित्र*",
            f"👤 *नागरिक:* {u.name} ({u.age} वर्ष | {u.state})",
            f"📋 *पेशा:* {u.occupation.replace('_', ' ').title()} | *आय:* ₹{u.annual_family_income:,}/वर्ष",
            "━━━━━━━━━━━━━━━━━━━━",
            f"🎉 *बधाई! आपके लिए {len(plan.matched_schemes)} योजनाएं उपलब्ध हैं:*",
            ""
        ]

        for i, match in enumerate(plan.matched_schemes[:4], 1):
            s = match.scheme
            score_bar = "🟢 तैयार (Ready)" if match.readiness_score >= 80 else ("🟡 कुछ दस्तावेज बाकी" if match.readiness_score >= 40 else "🔴 दस्तावेज आवश्यक")
            lines.append(f"*{i}. {s.name}*")
            if s.hindi_name:
                lines.append(f"   _{s.hindi_name}_")
            lines.append(f"   💰 *लाभ:* {s.benefit_summary}")
            lines.append(f"   📊 *स्थिति:* {score_bar} (तैयारी: {match.readiness_score}%)")
            lines.append(f"   🔗 *ऑफिशियल पोर्टल:* {s.official_url}")
            if match.documents_missing:
                missing_names = [f"• {doc_id.replace('_', ' ').title()}" for doc_id in match.documents_missing[:2]]
                lines.append(f"   ⚠️ *अधूरे दस्तावेज:* {', '.join(missing_names)}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("📌 *तुरंत करने योग्य कार्य (Next Steps):*")
        if plan.urgent_next_actions:
            for action in plan.urgent_next_actions[:3]:
                lines.append(f"👉 {action}")
        else:
            lines.append("👉 सभी आवश्यक दस्तावेज तैयार हैं। तुरंत आधिकारिक पोर्टल पर आवेदन करें।")

        lines.append("")
        lines.append("📲 *इस संदेश को अपने माता-पिता, सीएससी (जन सेवा केंद्र) संचालक या मित्र को फॉरवर्ड करें।*")
        lines.append("💡 _सहायक केवल आधिकारिक सरकारी वेबसाइटों से सत्यापित जानकारी प्रदान करता है।_")

        return "\n".join(lines)

    def generate_hindi_explanation(self, plan: ApplicationReadinessPlan) -> str:
        """Generates an empathetic, conversational explanation in simple Hindi."""
        u = plan.citizen_profile
        schemes_list = []
        for match in plan.matched_schemes[:3]:
            schemes_list.append(f"• **{match.scheme.name}**: {match.scheme.benefit_summary}")

        schemes_text = "\n".join(schemes_list) if schemes_list else "फिलहाल कोई उपयुक्त योजना नहीं मिली।"

        explanation = f"""
नमस्ते **{u.name}** जी! 

सहायक ने आपकी जानकारी का विश्लेषण किया है:
- **उम्र:** {u.age} वर्ष
- **राज्य:** {u.state}
- **शिक्षा/पेशा:** {u.education_level.replace('_', ' ').title()} / {u.occupation.replace('_', ' ').title()}
- **परिवार की वार्षिक आय:** ₹{u.annual_family_income:,}

### आपको ये लाभ क्यों मिल सकते हैं?
आपकी पारिवारिक आय और छात्र/नागरिक स्थिति के आधार पर आप निम्नलिखित मुख्य योजनाओं के लिए पात्र हैं:
{schemes_text}

### आपको अब क्या करना चाहिए?
1. **दस्तावेज़ की तैयारी:** जिन योजनाओं में आपके दस्तावेज़ पूरे हैं, उनके लिए तुरंत ऑनलाइन आवेदन करें।
2. **आय व निवास प्रमाण पत्र:** यदि आपके पास 'आय प्रमाण पत्र' (Income Certificate) नहीं है, तो अपने नज़दीकी जन सेवा केंद्र (CSC) या `edistrict.up.gov.in` से 10-15 दिनों में बनवा सकते हैं।
3. **आधार बैंक लिंकिंग:** सुनिश्चित करें कि आपका बैंक खाता आधार व NPCI/DBT से लिंक है ताकि सरकारी सहायता सीधे आपके खाते में आए।
"""
        return explanation.strip()

    def enhance_plan(self, plan: ApplicationReadinessPlan) -> ApplicationReadinessPlan:
        """Populates the text fields in the readiness plan."""
        plan.whatsapp_summary_text = self.format_whatsapp_message(plan)
        plan.hindi_explanation_summary = self.generate_hindi_explanation(plan)
        return plan
