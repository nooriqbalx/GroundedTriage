"""
GroundedTriage -- Academic project-page styled Streamlit demo
"""

import os
import re
import requests
import streamlit as st

GROQ_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOKENS = 4096

GITHUB_USER = "nooriqbalx"
GITHUB_REPO = "GroundedTriage"
GITHUB_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
GROUNDING_CHART_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/figures/fig3_grounding.png"
ACCURACY_CHART_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/figures/fig1_accuracy.png"

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
    "high": {"color": "#C97064"},
    "medium": {"color": "#C9A664"},
    "low": {"color": "#6B9BC9"},
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


st.set_page_config(page_title="GroundedTriage -- Research Demo", page_icon=None, layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .block-container { padding-top: 2.5rem; max-width: 1100px; }

    .byline {
        font-family: 'Inter', sans-serif;
        color: #6B7280;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
        letter-spacing: 0.02em;
    }
    .paper-header {
        font-family: 'Source Serif 4', serif;
        font-size: 2.4rem;
        font-weight: 700;
        color: #F0F0F0;
        margin-bottom: 0.3rem;
        letter-spacing: -0.015em;
        line-height: 1.15;
    }
    .paper-subtitle {
        font-family: 'Source Serif 4', serif;
        font-style: italic;
        color: #9CA3AF;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    .link-row { margin-bottom: 1.8rem; }
    .link-pill {
        display: inline-block;
        border: 1px solid #3A3F48;
        border-radius: 20px;
        padding: 5px 16px;
        margin-right: 10px;
        font-size: 0.82rem;
        color: #C4C8CE !important;
        text-decoration: none !important;
        font-weight: 500;
    }
    .link-pill:hover { border-color: #6B7280; background-color: #1A1D22; }

    .stat-row { display: flex; gap: 1.2rem; margin-bottom: 2rem; }
    .stat-card {
        flex: 1;
        background-color: #14161A;
        border: 1px solid #2D3138;
        border-top: 2px solid #6B7280;
        border-radius: 4px;
        padding: 1.1rem 1.3rem;
    }
    .stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        color: #F0F0F0;
        line-height: 1.2;
    }
    .stat-label {
        color: #8B8F96;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.4rem;
        line-height: 1.4;
    }

    .abstract-box {
        background-color: #14161A;
        border: 1px solid #2D3138;
        border-left: 3px solid #6B7280;
        padding: 1.4rem 1.7rem;
        border-radius: 4px;
        margin-bottom: 2.5rem;
        font-size: 0.95rem;
        line-height: 1.75;
        color: #C4C8CE;
    }
    .abstract-label {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #E8E8E8;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-size: 0.72rem;
        margin-bottom: 0.7rem;
        display: block;
    }

    .section-label {
        font-family: 'Source Serif 4', serif;
        font-weight: 700;
        font-size: 1.2rem;
        color: #E8E8E8;
        border-bottom: 1px solid #2D3138;
        padding-bottom: 0.5rem;
        margin-bottom: 1.1rem;
        margin-top: 0.5rem;
    }

    .result-card {
        background-color: #14161A;
        border: 1px solid #2D3138;
        border-radius: 4px;
        padding: 1.7rem;
    }
    .family-label {
        color: #8B8F96;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.3rem;
    }
    .family-name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0;
    }
    .confidence-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .justification-text {
        color: #A8ADB4;
        line-height: 1.75;
        font-size: 0.92rem;
        margin-top: 1.3rem;
        border-top: 1px solid #2D3138;
        padding-top: 1.1rem;
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
        background-color: #1F2937;
        color: #E8E8E8;
        font-weight: 500;
        border: 1px solid #4A4F58;
        border-radius: 4px;
        letter-spacing: 0.02em;
    }
    .stButton>button:hover { background-color: #2D3138; border: 1px solid #6B7280; }

    div[data-testid="stTextArea"] textarea {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }

    .footer-text {
        color: #5B5F68;
        font-size: 0.8rem;
        border-top: 1px solid #2D3138;
        padding-top: 1.2rem;
        margin-top: 2.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="byline">Noor-ul-ain Iqbal &middot; Beaconhouse National University &middot; 2026</p>',
            unsafe_allow_html=True)
st.markdown('<p class="paper-header">GroundedTriage</p>', unsafe_allow_html=True)
st.markdown('<p class="paper-subtitle">Evidence-Dependent Hallucination in LLM-Based Malware Triage</p>',
            unsafe_allow_html=True)

st.markdown(f"""
<div class="link-row">
    <a href="{GITHUB_URL}" target="_blank" class="link-pill">Code</a>
    <a href="{GITHUB_URL}/tree/main/data" target="_blank" class="link-pill">Dataset (N=56)</a>
    <a href="{GITHUB_URL}/tree/main/figures" target="_blank" class="link-pill">Figures</a>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="stat-row">
    <div class="stat-card">
        <div class="stat-value">2.4% &rarr; 4.2%</div>
        <div class="stat-label">Accuracy, static vs. combined evidence<br>(not significant, p = 0.49)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">59.5% &rarr; 12.5%</div>
        <div class="stat-label">Abstention rate collapse<br>(p &lt; 0.0001, Cramer's V = 0.515)</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">73.3% &rarr; 6.7%</div>
        <div class="stat-label">Justification grounding rate<br>(human-verified, p &lt; 0.001)</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="abstract-box">
<span class="abstract-label">Abstract</span>
I evaluate three large language models (GPT-OSS-20B, GPT-OSS-120B, Qwen3.6-27B) on malware family
classification across 56 real-world samples, varying the evidence provided from static file metadata
to full dynamic behavioral analysis. Classification accuracy remains statistically flat across this
progression (&chi;&sup2; not significant, p = 0.49), while models abstain far less often as evidence
richness increases (59.5% to 12.5%, p &lt; 0.0001). A stratified human review of 45 model justifications
finds that this growing confidence is largely unearned: the proportion of justifications actually
grounded in the evidence shown collapses from 73.3% to 6.7% (Fisher's exact test, p &lt; 0.001). I
interpret this as evidence that richer context does not improve reasoning in this setting; it increases
the surface area for models to construct plausible-sounding but unsupported narratives.
</div>
""", unsafe_allow_html=True)

col_input, col_result = st.columns([1, 1], gap="large")

with col_input:
    st.markdown('<p class="section-label">Try It: Input Evidence</p>', unsafe_allow_html=True)
    evidence_input = st.text_area(
        "Static/dynamic analysis output",
        value=EXAMPLE_EVIDENCE, height=230, label_visibility="collapsed",
    )
    model_choice = st.selectbox(
        "Model under evaluation",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"],
        help="GPT-OSS-120B was the most accurate and best-calibrated model in the full evaluation.",
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
                color = CONFIDENCE_STYLE.get(confidence, CONFIDENCE_STYLE["low"])["color"]

                st.markdown(f"""
                <div class="result-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                        <div>
                            <div class="family-label">Predicted Family</div>
                            <p class="family-name">{family}</p>
                        </div>
                        <div style="text-align:right;">
                            <div class="family-label">Confidence</div>
                            <span class="confidence-value" style="color:{color};">{confidence}</span>
                        </div>
                    </div>
                    <p class="justification-text">{justification}</p>
                </div>
                <div class="caveat-box">
                    Note -- per this project's findings, verify each claim above against the evidence
                    shown. Justifications frequently cite real evidence in support of an unsupported
                    or fabricated attribution; treat this output as a hypothesis, not a verdict.
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<p style="color:#5B5F68; font-style:italic; padding-top:1rem;">Awaiting input.</p>',
                    unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<p class="section-label">Empirical Basis</p>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Grounding Collapse", "Accuracy by Condition"])
with tab1:
    st.caption("Human-reviewed grounding rate across a stratified sample of 45 model responses.")
    try:
        st.image(GROUNDING_CHART_URL, use_container_width=True)
    except Exception:
        st.caption("(Figure will render once pushed to the repository.)")
with tab2:
    st.caption("Classification accuracy across all 504 evaluated responses.")
    try:
        st.image(ACCURACY_CHART_URL, use_container_width=True)
    except Exception:
        st.caption("(Figure will render once pushed to the repository.)")

st.markdown(
    '<p class="footer-text">Iqbal, N. (2026). <i>GroundedTriage: Evaluating Evidence-Dependent '
    'Hallucination in LLM-Based Malware Triage.</i> Beaconhouse National University. '
    f'<a href="{GITHUB_URL}" style="color:#5B5F68;">Source and data available on GitHub.</a></p>',
    unsafe_allow_html=True,
)