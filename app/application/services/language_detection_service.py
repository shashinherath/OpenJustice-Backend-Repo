import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

class LanguageDetectionService:
    """Detect language of user input through native Unicode bounds."""

    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'si': 'Sinhala',
        'ta': 'Tamil'
    }

    DEFAULT_LANGUAGE = 'English'

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Determines the primary language spoken based on the most prevalent unicode block."""
        if not text or len(text.strip()) < 2:
            return cls.DEFAULT_LANGUAGE

        try:
            language_code = cls._detect_by_unicode(text)
            if language_code:
                detected = cls.SUPPORTED_LANGUAGES.get(language_code, cls.DEFAULT_LANGUAGE)
                logger.info(f"Detected language context: {detected} (code: {language_code})")
                return detected

            return cls.DEFAULT_LANGUAGE
        except Exception as e:
            logger.error(f"Language detection malfunction: {e}")
            return cls.DEFAULT_LANGUAGE

    @staticmethod
    def _detect_by_unicode(text: str) -> Optional[str]:
        """Physically map String boundaries determining structural dominance of language."""
        
        # Sinhala: 0D80–0DFF
        sinhala_chars = len(re.findall(r'[\u0D80-\u0DFF]', text))
        # Tamil: 0B80–0BFF
        tamil_chars = len(re.findall(r'[\u0B80-\u0BFF]', text))
        # Latin/English: a-zA-Z
        latin_chars = len(re.findall(r'[a-zA-Z]', text))

        total_chars = sinhala_chars + tamil_chars + latin_chars

        if total_chars == 0:
            return None

        sinhala_pct = sinhala_chars / total_chars
        tamil_pct = tamil_chars / total_chars
        latin_pct = latin_chars / total_chars

        # Determine threshold dominance
        if sinhala_pct > 0.3:
            return 'si'
        elif tamil_pct > 0.3:
            return 'ta'
        elif latin_pct > 0.5:
            return 'en'

        # Can't reliably identify
        return None
