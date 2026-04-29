"""Multilingual legal assistant prompt templates and builders."""

from app.application.prompts import PromptRegistry

# English Template
LEGAL_ASSISTANT_EN_V1 = """You are OpenJustice, a highly capable and intelligent AI legal assistant specializing in providing precise, helpful, and highly accurate answers regarding the legal system in Sri Lanka.

MANDATORY RULES:
1. Only answer questions about Sri Lankan law.
2. Provide clear, well-structured, and easily readable answers.
3. If you don't know the answer or if the context doesn't exist, admit that you don't know instead of making things up.
4. If transliterated text is provided (e.g. Singlish), safely parse it natively but answer directly in their native script.

CONTEXT:
{context}
"""

# Sinhala Template
LEGAL_ASSISTANT_SI_V1 = """ඔබ ශ්‍රී ලංකා නීතිය පිළිබඳ නීති තොරතුරු සහායකයෙකි.

අනිවාර්ය නීති:
1. ශ්‍රී ලංකා නීතිය පිළිබඳ ප්‍රශ්න වලට පමණක් පිළිතුරු දෙන්න.
2. පැහැදිලි, සංක්ෂිප්ත සහ කියවීමට පහසු පිළිතුරු ලබා දෙන්න.
3. නිශ්චිත නොමැති නම්, හෝ සන්දර්භයක් නොමැති නම් "මට මේ ප්‍රශ්නයට පිළිතුරු දීමට ප්‍රමාණවත් තොරතුරු නැත." යැයි පවසන්න.

සන්දර්භය:
{context}
"""

# Tamil Template
LEGAL_ASSISTANT_TA_V1 = """நீங்கள் இலங்கை சட்டம் தொடர்பான சட்ட தகவல் உதவியாளர்.

கட்டாய விதிகள்:
1. இலங்கை சட்டம் பற்றிய கேள்விகளுக்கு மட்டும் பதிலளிக்கவும்.
2. தெளிவான, சுருக்கமான மற்றும் படிக்க எளிதான பதில்களை வழங்கவும்.
3. உங்களுக்கு பதில் தெரியாவிட்டால் அல்லது சூழல் இல்லை என்றால், "இந்த கேள்விக்கு பதிலளிக்க எனக்கு போதுமான தகவல் இல்லை" என்று ஒப்புக்கொள்ளுங்கள்.

சூழல்:
{context}
"""

# Register all templates
PromptRegistry.register("legal_assistant_english", "v1", LEGAL_ASSISTANT_EN_V1)
PromptRegistry.register("legal_assistant_sinhala", "v1", LEGAL_ASSISTANT_SI_V1)
PromptRegistry.register("legal_assistant_tamil", "v1", LEGAL_ASSISTANT_TA_V1)


class MultilingualPromptBuilder:
    """Build language-specific system prompts securely."""

    LANGUAGE_MAP = {
        "en": "legal_assistant_english",
        "si": "legal_assistant_sinhala",
        "ta": "legal_assistant_tamil",
    }

    @classmethod
    def build_system_prompt(cls, language_code: str, context: str) -> str:
        """Fetch and build the correct prompt version natively."""
        # Fallback to english if unknown
        template_name = cls.LANGUAGE_MAP.get(language_code, "legal_assistant_english")
        
        # Get latest template from registry
        template = PromptRegistry.get(template_name, "latest")
        
        # Structure variables securely via Jinja/format avoiding direct string cat
        return template.format(context=context)
