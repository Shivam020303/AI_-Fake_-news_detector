import streamlit as st
from typing import Dict, Any, List
from PIL import Image
import traceback

from gemini_client import GeminiClient
from result_parser import ResultParser

st.set_page_config(
    page_title="AI Fake News Detector 2.5",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# Styles (trim/keep as needed)
# =========================
st.markdown("""
<style>
.main-header { text-align:center; padding:1rem 0; margin-bottom:1.2rem;
  background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.4rem; font-weight:700; }
.result-real{ border:3px solid #28a745; background:linear-gradient(135deg,#d4edda 0%,#c3e6cb 100%);
  padding:1.2rem; border-radius:14px; margin:1rem 0; text-align:center; }
.result-fake{ border:3px solid #dc3545; background:linear-gradient(135deg,#f8d7da 0%,#f5c6cb 100%);
  padding:1.2rem; border-radius:14px; margin:1rem 0; text-align:center; }
.result-manipulated{ border:3px solid #ffc107; background:linear-gradient(135deg,#fff3cd 0%,#ffeaa7 100%);
  padding:1.2rem; border-radius:14px; margin:1rem 0; text-align:center; }
.result-title{ font-size:2rem; font-weight:800; margin:0 0 .5rem 0; letter-spacing:1px; }
.result-subtitle{ font-size:1rem; margin:0 0 .8rem 0; opacity:.85; }
.confidence-display{ font-size:2.2rem; font-weight:800; margin:.6rem 0; }
.quick-summary{ background:#fff; padding:1rem; border-radius:10px; margin:1rem 0; border:1px solid #eee; }
.factor-analysis{ background:#fff; border:1px solid #e9ecef; border-radius:10px; padding:1rem; margin:1rem 0; }
.factor-title{ font-size:1.1rem; font-weight:700; color:#444; margin-bottom:.6rem; border-bottom:2px solid #eee; padding-bottom:.4rem; }
.factor-item{ background:#f8f9fa; border-left:4px solid #007bff; padding:.75rem; margin:.45rem 0; border-radius:6px; }
</style>
""", unsafe_allow_html=True)

# =========================
# Helper: Clear Categorization
# =========================
def get_clear_categorization(classification: str, score: int) -> Dict[str, str]:
    if classification == "AUTHENTIC" and score >= 80:
        return {"category": "REAL", "css_class": "result-real", "icon": "✅",
                "title": "Content is REAL",
                "subtitle": "This content appears to be authentic and trustworthy",
                "color": "#28a745"}
    elif classification == "FAKE" or score < 30:
        return {"category": "FAKE", "css_class": "result-fake", "icon": "❌",
                "title": "Content is FAKE",
                "subtitle": "This content appears to be false or fabricated",
                "color": "#dc3545"}
    else:
        return {"category": "PARTIALLY MANIPULATED", "css_class": "result-manipulated", "icon": "⚠️",
                "title": "Content is PARTIALLY MANIPULATED",
                "subtitle": "This content may contain manipulation or requires verification",
                "color": "#ffc107"}

# =========================
# UI: Result + Expander (reliable)
# =========================
def display_clear_result(result_data: Dict[str, Any], analysis_type: str):
    classification = result_data.get("classification", "UNCERTAIN")
    score = result_data.get("score", 0)
    category_info = get_clear_categorization(classification, score)

    st.markdown(f"""
    <div class="{category_info['css_class']}">
      <div class="result-title" style="color:{category_info['color']};">
        {category_info['icon']} {category_info['title']}
      </div>
      <div class="result-subtitle">{category_info['subtitle']}</div>
      <div class="confidence-display" style="color:{category_info['color']};">{score}% Confidence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="quick-summary">
      <h4>📋 Quick Summary</h4>
      <p><strong>Analysis Type:</strong> {analysis_type}</p>
      <p><strong>Result:</strong> {category_info['category']}</p>
      <p><strong>Confidence Level:</strong> {ResultParser.get_confidence_level(score)}</p>
      <p><strong>Risk Level:</strong> {ResultParser.get_risk_level(classification, score)}</p>
    </div>
    """, unsafe_allow_html=True)

    # Always-available expander (replaces flaky st.button flow)
    with st.expander(f"🔍 Detailed Analysis — Why this is {category_info['category']}?"):
        show_detailed_factor_analysis(result_data, category_info)

def show_detailed_factor_analysis(result_data: Dict[str, Any], category_info: Dict[str, str]):
    st.markdown("---")
    st.markdown(f"## 🔬 Detailed Factor Analysis: Why is this content {category_info['category']}?")

    findings = result_data.get("key_findings", [])
    if findings:
        st.markdown('<div class="factor-analysis"><div class="factor-title">🎯 Key Detection Factors</div></div>', unsafe_allow_html=True)
        for i, f in enumerate(findings, 1):
            st.markdown(f'<div class="factor-item"><strong>Factor {i}:</strong> {f}</div>', unsafe_allow_html=True)

    evidence = result_data.get("evidence", [])
    if evidence:
        st.markdown('<div class="factor-analysis"><div class="factor-title">📊 Evidence Supporting Classification</div></div>', unsafe_allow_html=True)
        for i, e in enumerate(evidence, 1):
            st.markdown(f'<div class="factor-item"><strong>Evidence {i}:</strong> {e}</div>', unsafe_allow_html=True)

    red_flags = result_data.get("red_flags", [])
    if red_flags:
        st.markdown('<div class="factor-analysis"><div class="factor-title">🚩 Warning Indicators</div></div>', unsafe_allow_html=True)
        for i, rf in enumerate(red_flags, 1):
            st.markdown(f'<div class="factor-item"><strong>Red Flag {i}:</strong> {rf}</div>', unsafe_allow_html=True)

    reasoning = result_data.get("reasoning_chain", "")
    if reasoning:
        st.markdown('<div class="factor-analysis"><div class="factor-title">🧠 AI Reasoning Process</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="factor-item"><strong>Analysis Logic:</strong> {reasoning}</div>', unsafe_allow_html=True)

    consistency = result_data.get("cross_modal_consistency", "")
    if consistency and consistency != "Not Assessed":
        st.markdown('<div class="factor-analysis"><div class="factor-title">🔗 Text-Image Consistency Analysis</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="factor-item"><strong>Consistency Assessment:</strong> {consistency}</div>', unsafe_allow_html=True)

    recommendation = result_data.get("recommendation", "")
    if recommendation:
        st.markdown('<div class="factor-analysis"><div class="factor-title">💡 Expert Recommendation</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="factor-item"><strong>Recommended Action:</strong> {recommendation}</div>', unsafe_allow_html=True)

    with st.expander("📋 Complete Technical Analysis Report"):
        st.text_area("Full AI Analysis", result_data.get("raw_analysis", ""), height=380, disabled=True)

# =========================
# Main
# =========================
def main():
    st.markdown('<h1 class="main-header">🔍 AI Fake News Detector</h1>', unsafe_allow_html=True)

    with st.sidebar:
        st.header("🔧 Configuration")
        api_key = st.text_input("🔑 Google Gemini API Key", type="password")
        use_grounding = st.checkbox("🌐 Enable Google Search Grounding", value=True)
        analysis_mode = st.radio("📊 Analysis Mode",
                                 ["Text Analysis", "Image Analysis", "Multimodal Analysis"])
        st.markdown("---")
        st.caption("Result categories: ✅ REAL | ❌ FAKE | ⚠️ PARTIALLY MANIPULATED")

    if not api_key:
        st.info("Enter your Gemini API key in the sidebar to begin.")
        return

    try:
        client = GeminiClient(api_key)
        st.success("✅ Gemini 2.5 Flash initialized")
    except Exception as e:
        st.error(f"Initialization failed: {e}")
        return

    text_input = ""
    uploaded_image = None

    if analysis_mode in ["Text Analysis", "Multimodal Analysis"]:
        text_input = st.text_area("📝 Enter text to analyze:", height=180)

    if analysis_mode in ["Image Analysis", "Multimodal Analysis"]:
        uploaded_image = st.file_uploader("🖼️ Upload image:", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_image:
            st.image(Image.open(uploaded_image), use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Analysis Results")

    try:
        if analysis_mode == "Text Analysis":
            if st.button("🚀 Analyze Text", disabled=not text_input.strip(), use_container_width=True):
                raw = client.analyze_text(text_input, use_grounding)
                parsed = ResultParser.parse_analysis(raw)
                display_clear_result(parsed, "Text Content Analysis")

        elif analysis_mode == "Image Analysis":
            if st.button("🔬 Analyze Image", disabled=uploaded_image is None, use_container_width=True):
                img = Image.open(uploaded_image)
                raw = client.analyze_image(img, text_input or "")
                parsed = ResultParser.parse_analysis(raw)
                display_clear_result(parsed, "Image Content Analysis")

        else:
            if st.button("🔄 Analyze Both", disabled=(not text_input.strip() or uploaded_image is None), use_container_width=True):
                img = Image.open(uploaded_image)
                raw = client.multimodal_analysis(text_input, img, use_grounding)
                parsed = ResultParser.parse_analysis(raw)
                display_clear_result(parsed, "Multimodal Analysis")

    except Exception as e:
        st.error(f"Analysis failed: {e}")
        with st.expander("Error details"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
