"""
SecuriCopilot -- Streamlit demo
Deployed via Streamlit Community Cloud (genuinely free, no GPU-tier
restrictions, deploys directly from GitHub).
"""

import os
import re
import requests
import streamlit as st

GROQ_KEY = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOKENS = 4096

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


st.set_page_config(page_title="SecuriCopilot", page_icon="🛡️")

st.title("🛡️ SecuriCopilot: LLM Malware Triage Demo")
st.markdown(
    "Paste malware analysis evidence below and see how an LLM triages it. "
    "**This demo accompanies a research evaluation** which found that richer "
    "evidence increases model *confidence* without improving *accuracy* -- and "
    "that justifications become dramatically less grounded in real evidence as "
    "input complexity increases (73.3% -> 6.7% grounded, human-verified).\n\n"
    "[Full project, dataset, and figures on GitHub](https://github.com/YOUR_USERNAME/llm-malware-triage)"
)

evidence_input = st.text_area("Evidence (paste static/dynamic analysis output)",
                               value=EXAMPLE_EVIDENCE, height=220)
model_choice = st.selectbox(
    "Model (gpt-oss-120b was the most accurate and best-calibrated in our evaluation)",
    ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"],
)

if st.button("Analyze", type="primary"):
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
            confidence = confidence_match.group(1).lower() if confidence_match else "N/A"
            justification = justification_match.group(1).strip() if justification_match else final

            st.subheader("Result")
            col1, col2 = st.columns(2)
            col1.metric("Predicted Family", family)
            col2.metric("Confidence", confidence)
            st.text_area("Justification", justification, height=150)
            st.info(
                "Per our research findings, treat this justification with "
                "appropriate skepticism -- check whether it actually cites the "
                "evidence above, or makes claims not present in it."
            )