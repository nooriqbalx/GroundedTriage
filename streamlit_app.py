"""
SecuriCopilot -- Polished Streamlit demo
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

CONFIDENCE_COLORS = {"high": "#E63946", "medium": "#F4A261", "low": "#2A9D8F"}
CONFIDENCE_LABELS = {"high": "⚠️ HIGH", "medium": "◐ MEDIUM", "low": "○ LOW"}


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


st.set_page_config(page_title="SecuriCopilot", page_icon="🛡️", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(90deg, #E63946, #F4A261);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #9CA3AF;
        font-size: 1.05rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    .finding-badge {
        background-color: #1C1F26;
        border-left: 4px solid #E63946;
        padding: 0.9rem 1.2rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
    }
    .result-card {
        background-color: #1C1F26;
        border-radius: 10px;
        padding: 1.5rem;
        margin-top: 1rem;
        border: 1px solid #2D3138;
    }
    .stButton>button {
        background: linear-gradient(90deg, #E63946, #D62839);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 2rem;
    }
    .skepticism-note {
        background-color: #2D2418;
        border-left: 4px solid #F4A261;
        padding: 0.8rem 1.1rem;
        border-radius: 6px;
        font-size: 0.9rem;
        color: #D4C4A8;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<p class="main-header">🛡️ SecuriCopilot</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">An LLM-based malware triage assistant — and a live demonstration of why '
            'you shouldn\'t trust it blindly.</p>', unsafe_allow_html=True)

st.markdown(f"""
<div class="finding-badge">
<b>Research finding:</b> richer evidence increases model <i>confidence</i> without improving <i>accuracy</i>.
Human-verified grounding of model justifications collapses from <b>73.3%</b> (sparse evidence) to
<b>6.7%</b> (rich evidence) as more data is provided — models get more confident, not more correct.
<br><br>
📊 <a href="{GITHUB_URL}" target="_blank">Full project, dataset, code, and figures on GitHub →</a>
</div>
""", unsafe_allow_html=True)

col_input, col_result = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("Input Evidence")
    evidence_input = st.text_area(
        "Paste static/dynamic analysis output",
        value=EXAMPLE_EVIDENCE, height=240, label_visibility="collapsed",
    )
    model_choice = st.selectbox(
        "Model",
        ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"],
        help="gpt-oss-120b was the most accurate and best-calibrated model in our evaluation.",
    )
    analyze_clicked = st.button("🔍 Analyze Evidence", type="primary", use_container_width=True)

with col_result:
    st.subheader("Triage Result")

    if analyze_clicked:
        if not GROQ_KEY:
            st.error("Server not configured (missing API key).")
        elif not evidence_input.strip():
            st.warning("Please paste some evidence first.")
        else:
            with st.spinner("Analyzing..."):
                try:
                    final = analyze(evidence_input, model_choice)
                except Exception as e:
                    st.error(f"Error calling model: {e}")
                    final = None

            if final:
                family_match = re.search(r"FAMILY:\s*(.+)", final)
                confidence_match = re.search(r"CONFIDENCE:\s*(low|medium|high)", final, re.IGNORECASE)
                justification_match = re.search(r"JUSTIFICATION:\s*(.+)", final, re.DOTALL)

                family = family_match.group(1).strip() if family_match else "N/A"
                confidence = confidence_match.group(1).lower() if confidence_match else "low"
                justification = justification_match.group(1).strip() if justification_match else final

                badge_color = CONFIDENCE_COLORS.get(confidence, "#9CA3AF")
                badge_label = CONFIDENCE_LABELS.get(confidence, confidence.upper())

                st.markdown(f"""
                <div class="result-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0;">{family}</h3>
                        <span style="background-color:{badge_color}; color:white; padding:4px 12px;
                                     border-radius:20px; font-size:0.85rem; font-weight:600;">
                            {badge_label}
                        </span>
                    </div>
                    <p style="color:#B0B5BD; margin-top:1rem; line-height:1.6;">{justification}</p>
                </div>
                <div class="skepticism-note">
                    🧐 <b>Per our findings:</b> don't take this justification at face value —
                    check whether each claim above actually traces back to the evidence you pasted,
                    or whether the model is confidently narrating something it can't actually support.
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("← Paste evidence and click Analyze to see a live triage result.")

st.divider()
st.subheader("Why grounding collapses as evidence increases")
st.caption("Human-reviewed grounding rate across 45 stratified sample responses (see full methodology on GitHub)")
try:
    st.image(GROUNDING_CHART_URL, use_container_width=True)
except Exception:
    st.caption("(Chart loads once figures are pushed to the GitHub repo)")

st.divider()
st.caption("Built by Noor-ul-ain Iqbal · Beaconhouse National University")