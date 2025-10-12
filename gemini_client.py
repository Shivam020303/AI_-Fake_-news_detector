"""
Gemini 2.5 API Client — final
Reverse-image reasoning, OCR fallback, text/article analysis, multimodal, batch, and get_model_info.
"""
import google.generativeai as genai
from PIL import Image
from typing import Optional, Dict, Any, List

class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.api_key = api_key

    def create_grounding_tool(self) -> List[Any]:
        return [genai.protos.Tool(google_search_retrieval=genai.protos.GoogleSearchRetrieval())]

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": "gemini-2.0-flash-exp",
            "version": "2.5",
            "capabilities": [
                "Advanced text analysis","Enhanced image forensics","Multimodal reasoning",
                "Real-time grounding","Batch processing","Reverse image analysis","OCR"
            ],
            "max_tokens": 3500, "supports_grounding": True, "supports_multimodal": True
        }

    def reverse_image_search_analysis(self, image: Image.Image, context: str = "") -> str:
        prompt = f"""
        You are an image verification expert. Perform a reverse-image style reasoning:
        - Identify if the image seems recycled or manipulated
        - Evaluate context consistency w.r.t. the provided context
        - List supporting vs contradicting clues
        Provide: REVERSE SEARCH ASSESSMENT, AUTHENTICITY SCORE, MANIPULATION DETECTED,
        VISUAL EVIDENCE (bullets), CONTEXTUAL ANALYSIS (bullets), RED FLAGS (bullets),
        VERIFICATION STEPS (bullets), RECOMMENDATION (1-2 lines).
        Context: {context}
        """
        try:
            resp = self.model.generate_content([prompt, image],
                generation_config=genai.types.GenerationConfig(temperature=0.05, max_output_tokens=2000))
            return resp.text
        except Exception as e:
            return f"Error in reverse analysis: {e}"

    def extract_text_from_image(self, image: Image.Image) -> Dict[str, Any]:
        prompt = """
        Extract all visible text from the image (OCR). Then list KEY_TOPICS, IMPORTANT_KEYWORDS, ENTITIES_DETECTED,
        and SEARCH_QUERIES for fact-checking. Include ANALYSIS_PRIORITY line.
        """
        try:
            resp = self.model.generate_content([prompt, image],
                generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=1500))
            return {"success": True, "analysis": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def analyze_text(self, text: str, use_grounding: bool = True) -> str:
        prompt = f"""
        Analyze the content for misinformation:
        - Extract topics/entities/claims
        - Check credibility with reputable sources (grounding if enabled)
        - Compile FACT_CHECK_RESULTS and SUPPORTING_EVIDENCE (bullets)
        - Identify RED_FLAGS_DETECTED (bullets)
        - Provide AUTHENTICITY SCORE, CLASSIFICATION, CONFIDENCE LEVEL
        - Provide REASONING_CHAIN and VERIFICATION_STEPS (bullets), RECOMMENDATION
        CONTENT:
        {text}
        """
        try:
            tools = self.create_grounding_tool() if use_grounding else []
            resp = self.model.generate_content(prompt,
                tools=tools if use_grounding else None,
                generation_config=genai.types.GenerationConfig(temperature=0.05, max_output_tokens=2500))
            return resp.text
        except Exception as e:
            return f"Error in text analysis: {e}"

    def analyze_image(self, image: Image.Image, context: str = "") -> str:
        reverse = self.reverse_image_search_analysis(image, context)
        ocr = self.extract_text_from_image(image)
        prompt = f"""
        Combine previous analyses for a final decision:
        IMAGE AUTHENTICITY SCORE, MANIPULATION DETECTED, CONFIDENCE LEVEL
        TECHNICAL_ANALYSIS (bullets), CONTEXTUAL_VERIFICATION (bullets),
        TEXT_CONTENT_ANALYSIS (bullets if OCR present), FINAL_ASSESSMENT,
        RECOMMENDATION and VERIFICATION_STEPS.
        PREVIOUS:
        REVERSE SEARCH -> {reverse}
        OCR -> {ocr.get('analysis','No text')}
        """
        try:
            resp = self.model.generate_content([prompt, image])
            return resp.text
        except Exception as e:
            return f"Error in image analysis: {e}"

    def multimodal_analysis(self, text: str, image: Image.Image, use_grounding: bool = True) -> str:
        img_res = self.analyze_image(image, text)
        ocr_res = self.extract_text_from_image(image)
        extracted = ocr_res.get("analysis", "") if ocr_res.get("success") else ""
        prompt = f"""
        Perform multimodal authenticity assessment:
        OVERALL AUTHENTICITY SCORE, FINAL CLASSIFICATION, CONFIDENCE LEVEL,
        CROSS_MODAL_CONSISTENCY, TEXT_ANALYSIS_SUMMARY (bullets),
        IMAGE_ANALYSIS_SUMMARY (bullets), CROSS_MODAL_VERIFICATION (bullets),
        EVIDENCE_COMPILATION (bullets), COMPREHENSIVE_REASONING,
        RED_FLAGS_IDENTIFIED (bullets), VERIFICATION_STRATEGY, FINAL_RECOMMENDATION.
        INPUTS:
        TEXT: {text}
        IMAGE_ANALYSIS: {img_res}
        OCR_TEXT: {extracted}
        """
        try:
            tools = self.create_grounding_tool() if use_grounding else []
            resp = self.model.generate_content([prompt, image],
                tools=tools if use_grounding else None,
                generation_config=genai.types.GenerationConfig(temperature=0.05, max_output_tokens=3500))
            return resp.text
        except Exception as e:
            return f"Error in multimodal analysis: {e}"

    def batch_analyze(self, items: List[Dict[str, Any]], use_grounding: bool = True) -> List[str]:
        out = []
        for item in items:
            try:
                if item["type"] == "text":
                    out.append(self.analyze_text(item["content"], use_grounding))
                elif item["type"] == "image":
                    out.append(self.analyze_image(item["image"], item.get("context","")))
                elif item["type"] == "multimodal":
                    out.append(self.multimodal_analysis(item["content"], item["image"], use_grounding))
                else:
                    out.append(f"Unsupported item type: {item['type']}")
            except Exception as e:
                out.append(f"Error analyzing item: {e}")
        return out
