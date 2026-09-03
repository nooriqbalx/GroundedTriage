"""
SecuriCopilot -- FastAPI service
Wraps the evidence-based malware triage pipeline as a deployable API.
Uses the best-performing model from evaluation (gpt-oss-120b) by default.
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")

app = FastAPI(
    title="SecuriCopilot",
    description="LLM-based malware triage API, built on evidence-grounded evaluation research.",
    version="1.0.0",
)

DEFAULT_MODEL = "openai/gpt-oss-120b"  # best-performing model from our evaluation
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_TOKENS = 4096
REQUEST_TIMEOUT = 90

PROMPT_TEMPLATE = """You are a malware analyst assistant. Based ONLY on the evidence below, provide your analysis in EXACTLY this format:

FAMILY: <your single best guess at the malware family name>
CONFIDENCE: <low, medium, or high>
JUSTIFICATION: <2-3 sentences citing SPECIFIC evidence from the text below. Do not invent evidence that isn't present. If the evidence is insufficient to make a confident call, say so explicitly.>

EVIDENCE:
{evidence}
"""


class AnalyzeRequest(BaseModel):
    evidence: str
    model: str = DEFAULT_MODEL


class AnalyzeResponse(BaseModel):
    family: str | None
    confidence: str | None
    justification: str | None
    model_used: str
    raw_response: str


def extract_final_answer(raw_text: str) -> str:
    if "</think>" in raw_text:
        return raw_text.split("</think>")[-1].strip()
    if "FAMILY:" in raw_text:
        return raw_text[raw_text.index("FAMILY:"):].strip()
    return raw_text.strip()


def parse_fields(text: str):
    import re
    family_match = re.search(r"FAMILY:\s*(.+)", text)
    confidence_match = re.search(r"CONFIDENCE:\s*(low|medium|high)", text, re.IGNORECASE)
    justification_match = re.search(r"JUSTIFICATION:\s*(.+)", text, re.DOTALL)

    family = family_match.group(1).strip().strip("*") if family_match else None
    confidence = confidence_match.group(1).lower() if confidence_match else None
    justification = justification_match.group(1).strip() if justification_match else None
    return family, confidence, justification


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    if not GROQ_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured on server.")

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": request.model,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(evidence=request.evidence)}],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
    }

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e}")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Groq API error {resp.status_code}: {resp.text[:300]}")

    try:
        raw_content = resp.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected response format from Groq API.")

    final_answer = extract_final_answer(raw_content)
    family, confidence, justification = parse_fields(final_answer)

    return AnalyzeResponse(
        family=family,
        confidence=confidence,
        justification=justification,
        model_used=request.model,
        raw_response=raw_content,
    )