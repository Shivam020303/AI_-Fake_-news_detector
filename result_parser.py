"""
Enhanced Result Parser — final
Maps analysis text to clear REAL/FAKE/PARTIALLY MANIPULATED with evidence, red flags, reasoning, and consistency.
"""
import re
from typing import Dict, Any, List, Optional

class ResultParser:
    @staticmethod
    def extract_score(text: str) -> int:
        patterns = [
            r'(?:AUTHENTICITY SCORE|OVERALL.*SCORE|IMAGE.*SCORE):\s*(\d{1,3})',
            r'(?:SCORE|Score):\s*(\d{1,3})', r'(\d{1,3})/100', r'(\d{1,3})%', r'(\d{1,3})\s*(?:out of 100|/ 100)'
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = int(m.group(1))
                return max(0, min(100, val))
        return 50

    @staticmethod
    def extract_classification(text: str) -> str:
        for p in [
            r'(?:CLASSIFICATION|FINAL CLASSIFICATION):\s*(AUTHENTIC|SUSPICIOUS|FAKE)',
            r'(?:ASSESSMENT|FINAL ASSESSMENT):\s*(AUTHENTIC|SUSPICIOUS|FAKE)'
        ]:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).upper()
        t = text.lower()
        auth = sum(k in t for k in ["authentic","genuine","real","credible","verified","legitimate"])
        fake = sum(k in t for k in ["fake","false","fabricated","misleading","deceptive","manipulated","forged","hoax"])
        susp = sum(k in t for k in ["suspicious","questionable","uncertain","dubious","inconclusive","partial","mixed"])
        if fake > auth and fake >= 2: return "FAKE"
        if auth > fake and auth >= 2: return "AUTHENTIC"
        return "SUSPICIOUS"

    @staticmethod
    def get_clear_category(classification: str, score: int) -> str:
        if classification == "AUTHENTIC" and score >= 75: return "REAL"
        if classification == "FAKE" or score < 25: return "FAKE"
        return "PARTIALLY MANIPULATED"

    @staticmethod
    def _bullets(text: str, region_patterns: List[str]) -> List[str]:
        out: List[str] = []
        for p in region_patterns:
            m = re.search(p, text, re.IGNORECASE | re.DOTALL)
            if m:
                region = m.group(1)
                out += [b.strip() for b in re.findall(r'[-•*]\s*([^\n]+)', region)]
        # dedupe
        seen = set(); uniq = []
        for x in out:
            key = x.lower()
            if key not in seen:
                seen.add(key); uniq.append(x)
        return uniq

    @staticmethod
    def extract_key_findings(text: str) -> List[str]:
        pats = [
            r'KEY_TOPICS_EXTRACTED:(.*?)(?=\n[A-Z_]+:|$)', r'KEY FINDINGS:(.*?)(?=\n[A-Z]+:|$)',
            r'VISUAL EVIDENCE:(.*?)(?=\n[A-Z]+:|$)', r'TECHNICAL_ANALYSIS:(.*?)(?=\n[A-Z_]+:|$)',
            r'TEXT_ANALYSIS_SUMMARY:(.*?)(?=\n[A-Z_]+:|$)', r'IMAGE_ANALYSIS_SUMMARY:(.*?)(?=\n[A-Z_]+:|$)'
        ]
        return ResultParser._bullets(text, pats)[:6]

    @staticmethod
    def extract_evidence(text: str) -> List[str]:
        pats = [
            r'SUPPORTING_EVIDENCE:(.*?)(?=\n[A-Z_]+:|$)', r'FACT_CHECK_RESULTS:(.*?)(?=\n[A-Z_]+:|$)',
            r'EVIDENCE_COMPILATION:(.*?)(?=\n[A-Z_]+:|$)', r'VERIFICATION_RESULTS:(.*?)(?=\n[A-Z_]+:|$)'
        ]
        return ResultParser._bullets(text, pats)[:5]

    @staticmethod
    def extract_red_flags(text: str) -> List[str]:
        pats = [
            r'RED_FLAGS_DETECTED:(.*?)(?=\n[A-Z_]+:|$)', r'RED FLAGS:(.*?)(?=\n[A-Z]+:|$)',
            r'WARNING_SIGNS:(.*?)(?=\n[A-Z_]+:|$)', r'MANIPULATION_INDICATORS:(.*?)(?=\n[A-Z_]+:|$)'
        ]
        return ResultParser._bullets(text, pats)[:4]

    @staticmethod
    def extract_recommendation(text: str) -> str:
        for p in [
            r'FINAL_RECOMMENDATION:(.*?)(?=\n[A-Z_]+:|$)', r'RECOMMENDATION:(.*?)(?=\n[A-Z]+:|$)',
            r'SUGGESTED_ACTION:(.*?)(?=\n[A-Z_]+:|$)', r'NEXT_STEPS:(.*?)(?=\n[A-Z_]+:|$)'
        ]:
            m = re.search(p, text, re.IGNORECASE | re.DOTALL)
            if m:
                s = m.group(1).strip()
                s = re.sub(r'\n+', ' ', s)
                s = re.sub(r'\s+', ' ', s)
                return s[:250]
        return "Verify through multiple authoritative sources before sharing."

    @staticmethod
    def extract_confidence_level(text: str) -> str:
        m = re.search(r'CONFIDENCE LEVEL:\s*(HIGH|MEDIUM|LOW)', text, re.IGNORECASE)
        return m.group(1).upper() if m else "MEDIUM"

    @staticmethod
    def extract_reasoning_chain(text: str) -> str:
        for p in [r'REASONING_CHAIN:(.*?)(?=\n[A-Z_]+:|$)', r'COMPREHENSIVE_REASONING:(.*?)(?=\n[A-Z_]+:|$)']:
            m = re.search(p, text, re.IGNORECASE | re.DOTALL)
            if m:
                s = re.sub(r'\s+', ' ', m.group(1).strip())
                return s[:500]
        return "Analysis completed using advanced AI reasoning with cross-source verification."

    @staticmethod
    def extract_cross_modal_consistency(text: str) -> str:
        m = re.search(r'CROSS_MODAL_CONSISTENCY:\s*(CONSISTENT|PARTIALLY_CONSISTENT|INCONSISTENT)', text, re.IGNORECASE)
        return m.group(1).replace('_', ' ') if m else "Not Assessed"

    @classmethod
    def parse_analysis(cls, analysis_text: str) -> Dict[str, Any]:
        score = cls.extract_score(analysis_text)
        classification = cls.extract_classification(analysis_text)
        return {
            "score": score,
            "classification": classification,
            "clear_category": cls.get_clear_category(classification, score),
            "confidence_level": cls.extract_confidence_level(analysis_text),
            "key_findings": cls.extract_key_findings(analysis_text),
            "evidence": cls.extract_evidence(analysis_text),
            "red_flags": cls.extract_red_flags(analysis_text),
            "recommendation": cls.extract_recommendation(analysis_text),
            "reasoning_chain": cls.extract_reasoning_chain(analysis_text),
            "cross_modal_consistency": cls.extract_cross_modal_consistency(analysis_text),
            "raw_analysis": analysis_text
        }

    @staticmethod
    def get_confidence_level(score: int) -> str:
        if score >= 90: return "Extremely High Confidence"
        if score >= 80: return "High Confidence"
        if score >= 65: return "Good Confidence"
        if score >= 50: return "Medium Confidence"
        if score >= 35: return "Low Confidence"
        return "Very Low Confidence"

    @staticmethod
    def get_risk_level(classification: str, score: int) -> str:
        cat = ResultParser.get_clear_category(classification, score)
        if cat == "FAKE": return "High Risk - Do Not Share"
        if cat == "PARTIALLY MANIPULATED": return "Medium Risk - Verify Before Sharing"
        if cat == "REAL" and score >= 85: return "Low Risk - Appears Reliable"
        return "Medium Risk - Additional Verification Recommended"
