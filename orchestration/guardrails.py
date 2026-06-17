import re
import json
from llm.llm_client import LLMClient

class GuardrailSystem:
    def __init__(self):
        self.llm = LLMClient()
        
        # Pre-compiled regex patterns for PII detection/masking
        self.pii_patterns = {
            "EMAIL": re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
            "PHONE": re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
            "SSN": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
            "CREDIT_CARD": re.compile(r'\b(?:\d[ -]*?){13,16}\b')
        }

    def sanitize_pii(self, text: str) -> tuple[str, bool]:
        """
        Scans text for sensitive Personally Identifiable Information (PII)
        and replaces it with redaction placeholders.
        Returns a tuple of (sanitized_text, was_redacted).
        """
        if not text:
            return text, False
            
        sanitized = text
        was_redacted = False
        
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(sanitized):
                sanitized = pattern.sub(f"[REDACTED_{pii_type}]", sanitized)
                was_redacted = True
                
        return sanitized, was_redacted

    def check_input_safety(self, query: str) -> tuple[bool, str]:
        """
        Validates user queries for Personally Identifiable Information (PII).
        Returns (is_safe, refusal_reason_or_empty).
        """
        # First check: Sanitization of query PII
        sanitized_query, contains_pii = self.sanitize_pii(query)
        if contains_pii:
            # We block input queries containing sensitive credentials/SSN/CC/etc. for safety
            return False, "Query contains sensitive personal information (PII) which is not permitted for safety reasons."
        
        return True, ""


