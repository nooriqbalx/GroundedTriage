"""
SecuriCopilot -- Academic-styled Streamlit demo
"""

import os
import re
import requests
import streamlit as st

GROQ_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOKENS = 4096

GITHUB_USER = "nooriqbalx"
GITHUB_REPO = "llm-malware-triage"
GITHUB_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
GROUNDING_CHART_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/figures/fig3_grounding.png"

PROMPT_TEMPLATE = """You are a malware analyst assistant. Based ONLY on the evidence below, provide your analysis in EXACTLY this format:

FAMILY: <your single best guess at the malware family name>
CONFIDENCE: <low, medium, or high>
JUSTIFICATION: <2-3 sentences citing SPECIFIC evidence from the text below. Do not invent evidence that isn't present. If the evidence is insufficient to make a confident call, say so explicitly.>

EVIDENCE:
{evidence}
"""

EXAMPLE_EVIDENCE = """File type: PE32+ executable for MS Windows, x86-64
Submitted filename: Setup.exe
Domains contacted: gaz.138sportlogin.org, telegram.me
IP addresses contacted: 149.154.167.99
Behavioral signatures: process injection, token impersonation, registry modification, anti-debugging checks
MITRE ATT&CK techniques: T1055 (Process Injection), T1134.001 (Token Impersonation), T1112 (Modify Registry)"""

CONFIDENCE_STYLE = {
    "high": {"border": "#8B3A3A", "text": "#D4A5A5"},
    "medium": {"border": "#8B7A3A", "text": "#D4C4A5"},
    "low": {"border": "#3A5A6B", "text": "#A5C4D4"},
}


def extract_final_answer(raw_text):
    if "</think>" in raw_text:
        return raw_text.split("</think>")[-1].strip()
    if "FAMILY:" in raw_text:
        return raw_text[raw_text.index("FAMILY:"):].strip()
    return raw_text.strip()


def analyze(evidence_text, model_choice):
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model_choice,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(evidence=evidence_text)}],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
    }
    resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    return extract_final_answer(raw)


st.set_page_config(page_title="SecuriCopilot -- Research Demo", page_icon=None, layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .paper-header {
        font-family: 'Source Serif 4', serif;
        font-size: 2.1rem;
        font-weight: 700;
        color: #E8E8E8;
        margin-bottom: 0.2rem;
        letter-spacing: -0.01em;
    }
    .paper-subtitle {
        font-family: 'Source Serif 4', serif;
        font-style: italic;
        color: #9CA3AF;
        font-size: 1.05rem;
        margin-bottom: 1.8rem;
        border-bottom: 1px solid #2D3138;
        padding-bottom: 1.2rem;
    }
    .abstract-box {
        background-color: #14161A;
        border: 1px solid #2D3138;
        border-left: 3px solid #6B7280;
        padding: 1.3rem 1.6rem;
        border-radius: 4px;
        margin-bottom: 2rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #C4C8CE;
    }
    .abstract-label {
        font-family: 'Source Serif 4', serif;
        font-weight: 700;
        color: #E8E8E8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.75rem;
        margin-bottom: 0.6rem;
        display: block;
    }
    .section-label {
        font-family: 'Source Serif 4', serif;
        font-weight: 700;
        font-size: 1.15rem;
        color: #E8E8E8;
        border-bottom: 1px solid #2D3138;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    .result-card {
        background-color: #14161A;
        border: 1px solid #2D3138;
        border-radius: 4px;
        padding: 1.6rem;
    }
    .family-name {
        font-family: 'Source Serif 4', serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: #E8E8E8;
        margin: 0;
    }
    .confidence-tag {
        border: 1px solid;
        border-radius: 3px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .justification-text {
        color: #A8ADB4;
        line-height: 1.7;
        font-size: 0.93rem;
        margin-top: 1rem;
        border-top: 1px solid #2D3138;
        padding-top: 1rem;
    }
    .caveat-box {
        background-color: #14161A;
        border: 1px solid #2D3138;
        border-radius: 4px;
        padding: 0.9rem 1.2rem;
        font-size: 0.85rem;
        color: #8B8F96;
        margin-top: 1rem;
        font-style: italic;
    }
    .stButton>button {
        background-color: #2D3138;
        color: #E8E8E8;
        font-weight: 500;
        border: 1px solid #4A4F58;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #3A3F48;
        border: 1px solid #6B7280;
    }
    .footer-text {
        color: #6B7280;
        font-size: 0.82rem;
        border-top: 1px solid #2D3138;
        padding-top: 1rem;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="paper-header">SecuriCopilot</p>', unsafe_allow_html=True)
st.markdown('<p class="paper-subtitle">An empirical demonstration of evidence-dependent hallucination '
            'in LLM-based malware triage</p>', unsafe_allow_html=True)

st.markdown(f"""
<div class="abstract-box">
<span class="abstract-label">Summary of Findings</span>
This interactive demo accompanies an evaluation of three large language models across 56 real-world
malware samples. The central finding: classification accuracy remains statistically flat as evidence
richness increases (2.4% -> 4.8% -> 4.2%, &chi;&sup2; not significant, p = 0.49), while human-verified
grounding of model-generated justifications collapses from 73.3% to 6.7% over the same conditions
(Fisher's exact test, p &lt; 0.001). Models do not become more accurate with more evidence -- they
become more confidently unsupported.
<br><br>
<a href="{GITHUB_URL}" target="_blank" style="color:#9CA3AF;">-> Full methodology, dataset, and source code (GitHub)</a>
</div>
""", unsafe_allow_html=True)

col_input, col_result = st.columns([1, 1], gap="large")

with col_input:
    st.markdown('<p class="section-label">Input Evidence</p>', unsafe_allow_html=True)
    evidence_input = st.text_area(
        "Static/dynamic analysis output",
        value=EXAMPLE_EVIDENCE, height=230, label_visibility="collapsed",
    )
    model_choice = st.selectbox(
        "Model under evaluation",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"],
        help="gpt-oss-120b was the most accurate and best-calibrated model in the full evaluation.",
    )
    analyze_clicked = st.button("Run Triage Analysis", type="primary", use_container_width=True)

with col_result:
    st.markdown('<p class="section-label">Model Output</p>', unsafe_allow_html=True)

    if analyze_clicked:
        if not GROQ_KEY:
            st.error("Server not configured.")
        elif not evidence_input.strip():
            st.warning("Provide evidence to analyze.")
        else:
            with st.spinner("Querying model..."):
                try:
                    final = analyze(evidence_input, model_choice)
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    final = None

            if final:
                family_match = re.search(r"FAMILY:\s*(.+)", final)
                confidence_match = re.search(r"CONFIDENCE:\s*(low|medium|high)", final, re.IGNORECASE)
                justification_match = re.search(r"JUSTIFICATION:\s*(.+)", final, re.DOTALL)

                family = family_match.group(1).strip() if family_match else "N/A"
                confidence = confidence_match.group(1).lower() if confidence_match else "low"
                justification = justification_match.group(1).strip() if justification_match else final

                style = CONFIDENCE_STYLE.get(confidence, CONFIDENCE_STYLE["low"])

                st.markdown(f"""
                <div class="result-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <p class="family-name">{family}</p>
                        <span class="confidence-tag" style="border-color:{style['border']}; color:{style['text']};">
                            {confidence} confidence
                        </span>
                    </div>
                    <p class="justification-text">{justification}</p>
                </div>
                <div class="caveat-box">
                    Note: per this project's findings, verify each claim above against the evidence
                    shown. Justifications frequently cite real evidence in support of an unsupported
                    or fabricated attribution -- treat this output as a hypothesis, not a verdict.
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#6B7280; font-style:italic;">Awaiting input.</p>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p class="section-label">Empirical Basis</p>', unsafe_allow_html=True)
st.caption("Human-reviewed grounding rate across a stratified sample of 45 model responses. "
           "Full methodology available in the project repository.")
try:
    st.image(GROUNDING_CHART_URL, use_container_width=True)
except Exception:
    st.caption("(Figure will render once pushed to the repository.)")

st.markdown(
    '<p class="footer-text">Iqbal, N. (2026). <i>SecuriCopilot: Evaluating Evidence-Dependent '
    'Hallucination in LLM-Based Malware Triage.</i> Beaconhouse National University.</p>',
    unsafe_allow_html=True,
)