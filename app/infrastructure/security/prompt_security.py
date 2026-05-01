"""Prompt Security and Validation Utilities."""
import re
from typing import Tuple, List, Dict, Any


class PromptSecurityValidator:
    """Detect and prevent prompt injection attacks, and validate neutrality."""

    # Injection patterns (excluding basic conversational like "hello")
    INJECTION_PATTERNS = [
        r'ignore\s+(previous|above|all)\s+instructions',
        r'disregard\s+(previous|above|instructions)',
        r'new\s+instructions?:',
        r'system\s*:',
        r'assistant\s*:',
        r'<\|.*?\|>',  # Special tokens
        r'\[INST\].*?\[/INST\]',  # Instruction tags
    ]

    PROHIBITED_LEGAL_PHRASES = [
        "you should",
        "you must",
        "i recommend",
        "my advice is",
        "definitely",
        "certainly will",
        "guaranteed",
        "obviously",
        "clearly wrong",
    ]

    @classmethod
    def is_safe(cls, text: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Check if user text contains injection attempts."""
        violations = []
        text_lower = text.lower()

        for pattern in cls.INJECTION_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                violations.append({
                    "pattern": pattern,
                    "matches": matches,
                    "severity": "high"
                })

        return len(violations) == 0, violations

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Remove potentially dangerous patterns."""
        # Remove control characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())

        # Remove injection patterns
        for pattern in cls.INJECTION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()

    @classmethod
    def validate_neutral_language(cls, response: str) -> Tuple[bool, List[str]]:
        """Check if AI response maintains neutral language."""
        violations = []
        response_lower = response.lower()
        
        for phrase in cls.PROHIBITED_LEGAL_PHRASES:
            if phrase in response_lower:
                violations.append(phrase)

        return len(violations) == 0, violations
