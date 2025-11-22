# modules/heuristics.py

"""
Heuristics System for Query and Result Validation
Filters and validates user inputs and agent outputs before processing/returning.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class HeuristicResult(BaseModel):
    """Result of heuristic validation"""
    passed: bool
    rule_id: str
    rule_name: str
    message: str
    severity: str  # "block", "warn", "info"
    original_text: str
    sanitized_text: Optional[str] = None


class HeuristicsEngine:
    """
    Applies 10+ heuristic rules to queries and results.
    Can block, warn, or sanitize content based on rules.
    """
    
    def __init__(self):
        self.blocked_patterns = [
            r'\b(system|sudo|rm -rf|drop table|delete from|exec\(|eval\()\b',
            r'\b(password|api_key|secret|token|credential)\b',
        ]
        
        self.banned_words = [
            "hack", "exploit", "bypass", "inject", "malicious",
            "virus", "malware", "ransomware", "phishing",
            "illegal", "pirate", "crack", "keygen"
        ]
        
        self.max_query_length = 2000
        self.max_result_length = 50000
        self.max_tool_calls_per_query = 5
        
    
    # ==================== HEURISTIC RULES ====================
    
    def heuristic_1_banned_words(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 1: Remove or block banned words (harmful, malicious, illegal content)
        Examples: hack, exploit, malware, illegal, pirate
        """
        text_lower = text.lower()
        found_words = [word for word in self.banned_words if word in text_lower]
        
        if found_words:
            return HeuristicResult(
                passed=False,
                rule_id="H001",
                rule_name="Banned Words Filter",
                message=f"Detected banned words: {', '.join(found_words)}",
                severity="block",
                original_text=text,
                sanitized_text=None
            )
        
        return HeuristicResult(
            passed=True,
            rule_id="H001",
            rule_name="Banned Words Filter",
            message="No banned words detected",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_2_dangerous_commands(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 2: Block dangerous system commands and code execution patterns
        Examples: rm -rf, drop table, exec(), eval()
        """
        for pattern in self.blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return HeuristicResult(
                    passed=False,
                    rule_id="H002",
                    rule_name="Dangerous Command Filter",
                    message=f"Detected potentially dangerous pattern: {pattern}",
                    severity="block",
                    original_text=text
                )
        
        return HeuristicResult(
            passed=True,
            rule_id="H002",
            rule_name="Dangerous Command Filter",
            message="No dangerous commands detected",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_3_length_validation(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 3: Enforce maximum length limits for queries and results
        Prevents excessive token usage and processing time
        """
        max_length = self.max_query_length if context == "query" else self.max_result_length
        
        if len(text) > max_length:
            truncated = text[:max_length] + "... [TRUNCATED]"
            return HeuristicResult(
                passed=False,
                rule_id="H003",
                rule_name="Length Validation",
                message=f"Text exceeds max length ({len(text)} > {max_length})",
                severity="warn",
                original_text=text,
                sanitized_text=truncated
            )
        
        return HeuristicResult(
            passed=True,
            rule_id="H003",
            rule_name="Length Validation",
            message=f"Length OK ({len(text)} chars)",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_4_pii_detection(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 4: Detect and mask Personal Identifiable Information (PII)
        Examples: emails, phone numbers, SSN, credit cards
        """
        pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        }
        
        sanitized = text
        detected = []
        
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected.append(f"{pii_type}: {len(matches)} occurrences")
                sanitized = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", sanitized)
        
        if detected:
            return HeuristicResult(
                passed=False,
                rule_id="H004",
                rule_name="PII Detection",
                message=f"Detected PII: {', '.join(detected)}",
                severity="warn",
                original_text=text,
                sanitized_text=sanitized
            )
        
        return HeuristicResult(
            passed=True,
            rule_id="H004",
            rule_name="PII Detection",
            message="No PII detected",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_5_empty_or_whitespace(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 5: Reject empty or whitespace-only queries
        """
        if not text or not text.strip():
            return HeuristicResult(
                passed=False,
                rule_id="H005",
                rule_name="Empty Input Check",
                message="Query cannot be empty or whitespace-only",
                severity="block",
                original_text=text
            )
        
        return HeuristicResult(
            passed=True,
            rule_id="H005",
            rule_name="Empty Input Check",
            message="Input contains valid content",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_6_repetitive_content(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 6: Detect and block repetitive/spammy content
        Example: "aaaaaaaa...", "test test test test..."
        """
        # Check for repeated characters
        repeated_char = re.search(r'(.)\1{20,}', text)
        if repeated_char:
            return HeuristicResult(
                passed=False,
                rule_id="H006",
                rule_name="Repetitive Content Filter",
                message="Detected excessive character repetition",
                severity="block",
                original_text=text
            )
        
        # Check for repeated words
        words = text.split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            max_repetition = max(word_counts.values())
            if max_repetition > len(words) * 0.3:  # If any word is >30% of total
                return HeuristicResult(
                    passed=False,
                    rule_id="H006",
                    rule_name="Repetitive Content Filter",
                    message="Detected excessive word repetition",
                    severity="warn",
                    original_text=text
                )
        
        return HeuristicResult(
            passed=True,
            rule_id="H006",
            rule_name="Repetitive Content Filter",
            message="No excessive repetition detected",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_7_special_characters(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 7: Limit excessive special characters (potential injection attempts)
        """
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?]', text)) / max(len(text), 1)
        
        if special_char_ratio > 0.3:  # More than 30% special characters
            return HeuristicResult(
                passed=False,
                rule_id="H007",
                rule_name="Special Character Limit",
                message=f"Excessive special characters ({special_char_ratio:.1%})",
                severity="warn",
                original_text=text
            )
        
        return HeuristicResult(
            passed=True,
            rule_id="H007",
            rule_name="Special Character Limit",
            message="Special character usage within limits",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_8_valid_urls(self, text: str, context: str = "query") -> HeuristicResult:
        """
        RULE 8: Validate URLs and block suspicious/malicious domains
        """
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        blocked_domains = [
            "bit.ly", "tinyurl.com", "goo.gl",  # URL shorteners (can hide malicious sites)
            "suspicious.com", "malware.com"  # Example blocked domains
        ]
        
        for url in urls:
            for domain in blocked_domains:
                if domain in url.lower():
                    return HeuristicResult(
                        passed=False,
                        rule_id="H008",
                        rule_name="URL Validation",
                        message=f"Blocked suspicious domain in URL: {domain}",
                        severity="block",
                        original_text=text
                    )
        
        if urls:
            return HeuristicResult(
                passed=True,
                rule_id="H008",
                rule_name="URL Validation",
                message=f"Found {len(urls)} valid URL(s)",
                severity="info",
                original_text=text
            )
        
        return HeuristicResult(
            passed=True,
            rule_id="H008",
            rule_name="URL Validation",
            message="No URLs detected",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_9_code_injection(self, text: str, context: str = "result") -> HeuristicResult:
        """
        RULE 9: Detect potential code injection in results
        Check for unexpected Python/JavaScript code in tool outputs
        """
        injection_patterns = [
            r'<script[^>]*>.*?</script>',  # JavaScript
            r'__import__\(',  # Python import
            r'subprocess\.',  # Python subprocess
            r'os\.system\(',  # OS commands
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                sanitized = re.sub(pattern, '[REMOVED_CODE]', text, flags=re.IGNORECASE | re.DOTALL)
                return HeuristicResult(
                    passed=False,
                    rule_id="H009",
                    rule_name="Code Injection Filter",
                    message=f"Detected potential code injection: {pattern}",
                    severity="warn",
                    original_text=text,
                    sanitized_text=sanitized
                )
        
        return HeuristicResult(
            passed=True,
            rule_id="H009",
            rule_name="Code Injection Filter",
            message="No code injection detected",
            severity="info",
            original_text=text
        )
    
    
    def heuristic_10_json_structure(self, text: str, context: str = "result") -> HeuristicResult:
        """
        RULE 10: Validate JSON structure in results (if expected)
        Ensures proper formatting for downstream parsing
        """
        import json
        
        # Only check if text looks like JSON
        if text.strip().startswith('{') or text.strip().startswith('['):
            try:
                json.loads(text)
                return HeuristicResult(
                    passed=True,
                    rule_id="H010",
                    rule_name="JSON Structure Validation",
                    message="Valid JSON structure",
                    severity="info",
                    original_text=text
                )
            except json.JSONDecodeError as e:
                return HeuristicResult(
                    passed=False,
                    rule_id="H010",
                    rule_name="JSON Structure Validation",
                    message=f"Invalid JSON: {str(e)}",
                    severity="warn",
                    original_text=text
                )
        
        return HeuristicResult(
            passed=True,
            rule_id="H010",
            rule_name="JSON Structure Validation",
            message="Not a JSON structure (OK)",
            severity="info",
            original_text=text
        )
    
    
    # ==================== MAIN VALIDATION METHODS ====================
    
    def validate_query(self, query: str) -> List[HeuristicResult]:
        """
        Run all query heuristics and return results
        """
        results = [
            self.heuristic_1_banned_words(query, "query"),
            self.heuristic_2_dangerous_commands(query, "query"),
            self.heuristic_3_length_validation(query, "query"),
            self.heuristic_4_pii_detection(query, "query"),
            self.heuristic_5_empty_or_whitespace(query, "query"),
            self.heuristic_6_repetitive_content(query, "query"),
            self.heuristic_7_special_characters(query, "query"),
            self.heuristic_8_valid_urls(query, "query"),
        ]
        return results
    
    
    def validate_result(self, result: str) -> List[HeuristicResult]:
        """
        Run all result heuristics and return results
        """
        results = [
            self.heuristic_1_banned_words(result, "result"),
            self.heuristic_3_length_validation(result, "result"),
            self.heuristic_4_pii_detection(result, "result"),
            self.heuristic_9_code_injection(result, "result"),
            self.heuristic_10_json_structure(result, "result"),
        ]
        return results
    
    
    def apply_heuristics(self, text: str, context: str = "query") -> Dict[str, Any]:
        """
        Apply heuristics and return summary with sanitized text
        """
        if context == "query":
            results = self.validate_query(text)
        else:
            results = self.validate_result(text)
        
        blocked = [r for r in results if not r.passed and r.severity == "block"]
        warnings = [r for r in results if not r.passed and r.severity == "warn"]
        
        # Use sanitized text if available
        final_text = text
        for result in results:
            if result.sanitized_text:
                final_text = result.sanitized_text
        
        return {
            "allowed": len(blocked) == 0,
            "text": final_text,
            "original_text": text,
            "blocked_rules": [r.dict() for r in blocked],
            "warnings": [r.dict() for r in warnings],
            "all_results": [r.dict() for r in results]
        }


# ==================== USAGE EXAMPLE ====================

if __name__ == "__main__":
    engine = HeuristicsEngine()
    
    # Test queries
    test_queries = [
        "What is the capital of France?",  # Normal query
        "hack the system and steal data",  # Banned words
        "rm -rf / --no-preserve-root",  # Dangerous command
        "My email is john@example.com",  # PII
        "",  # Empty
        "test " * 100,  # Repetitive
        "https://bit.ly/malware",  # Suspicious URL
    ]
    
    print("🔍 HEURISTICS ENGINE TEST\n")
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: {query[:50]}...")
        result = engine.apply_heuristics(query, "query")
        print(f"  Allowed: {result['allowed']}")
        if result['blocked_rules']:
            print(f"  Blocked: {[r['rule_name'] for r in result['blocked_rules']]}")
        if result['warnings']:
            print(f"  Warnings: {[r['rule_name'] for r in result['warnings']]}")
        print()

