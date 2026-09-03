"""
SecuriCopilot -- Core evaluation script (v4, full run, resumable)
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()
GROQ_KEY = os.getenv("GROQ_API_KEY")

EVIDENCE_FILE = "evidence_bundles.json"
RESULTS_FILE = "evaluation_results.json"

MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]
CONDITIONS = ["static_evidence", "dynamic_evidence", "combined_evidence"]

SAMPLE_LIMIT = None  # None = run on ALL samples now

REQUEST_TIMEOUT = 90
MAX_RETRIES = 5
DELAY_BETWEEN_CALLS = 2.5
MAX_TOKENS = 4096

PROMPT_TEMPLATE = """You are a malware analyst assistant. Based ONLY on the evidence below, provide your analysis in EXACTLY this format:

FAMILY: <your single best guess at the malware family name>
CONFIDENCE: <low, medium, or high>
JUSTIFICATION: <2-3 sentences citing SPECIFIC evidence from the text below. Do not invent evidence that isn't present. If the evidence is insufficient to make a confident call, say so explicitly.>

EVIDENCE:
{evidence}
"""


def extract_final_answer(raw_text):
    if "</think>" in raw_text:
        return raw_text.split("</think>")[-1].strip()
    if "FAMILY:" in raw_text:
        return raw_text[raw_text.index("FAMILY:"):].strip()
    return raw_text.strip()


def call_model(model_name, evidence_text):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(evidence=evidence_text)}],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"      (network issue, attempt {attempt}/{MAX_RETRIES}: {type(e).__name__})")
            if attempt == MAX_RETRIES:
                return {"error": "network_failure_after_retries"}
            time.sleep(3 * attempt)
            continue

        if resp.status_code == 429:
            wait_time = 5 * attempt
            print(f"      (rate limited, waiting {wait_time}s, attempt {attempt}/{MAX_RETRIES})")
            if attempt == MAX_RETRIES:
                return {"error": "rate_limited_after_retries"}
            time.sleep(wait_time)
            continue

        if resp.status_code != 200:
            return {"error": f"http_{resp.status_code}", "body": resp.text[:300]}

        try:
            raw_content = resp.json()["choices"][0]["message"]["content"]
            final_answer = extract_final_answer(raw_content)
            return {"raw_response": raw_content, "final_answer": final_answer}
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return {"error": f"parse_failure: {e}", "body": resp.text[:300]}

    return {"error": "exhausted_retries"}


def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_results(results):
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)


def already_done(done_set, sha256, condition, model):
    return (sha256, condition, model) in done_set


if __name__ == "__main__":
    with open(EVIDENCE_FILE, "r") as f:
        bundles = json.load(f)

    bundles_to_run = bundles if SAMPLE_LIMIT is None else bundles[:SAMPLE_LIMIT]
    total_calls = len(bundles_to_run) * len(CONDITIONS) * len(MODELS)

    results = load_results()
    done_set = {(r["sha256_hash"], r["condition"], r["model"]) for r in results}

    print("=" * 60)
    print("SecuriCopilot -- running FULL evaluation")
    print(f"Samples: {len(bundles_to_run)}")
    print(f"Total calls needed: {total_calls}")
    print(f"Already done (resuming): {len(results)}")
    print("=" * 60)

    call_num = 0

    for bundle in bundles_to_run:
        sha256 = bundle["sha256_hash"]
        family = bundle["family_label"]

        for condition in CONDITIONS:
            evidence_text = bundle[condition]

            for model in MODELS:
                call_num += 1

                if already_done(done_set, sha256, condition, model):
                    print(f"[{call_num}/{total_calls}] {sha256[:12]}... "
                          f"| {condition} | {model} -> already done, skipping")
                    continue

                print(f"[{call_num}/{total_calls}] {sha256[:12]}... "
                      f"({family}) | {condition} | {model}...", end=" ")

                response = call_model(model, evidence_text)
                time.sleep(DELAY_BETWEEN_CALLS)

                if "error" in response:
                    print(f"ERROR: {response['error']}")
                else:
                    print("OK")

                results.append({
                    "sha256_hash": sha256,
                    "true_family": family,
                    "condition": condition,
                    "model": model,
                    "response": response,
                })
                done_set.add((sha256, condition, model))
                save_results(results)

    print("\n" + "=" * 60)
    print(f"Done. {len(results)} total results saved to {RESULTS_FILE}.")
    print("=" * 60)