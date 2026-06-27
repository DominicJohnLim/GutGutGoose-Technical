import json, os, requests
from knowledge.pack_loader import load_pack

# Synthetic demo patient. Edit freely — only the persona is invented; the
# measurements in results.json are real.
PERSONA = (
    "Maya, 28, woman. Mild recurring bloating and occasional afternoon fatigue. "
    "Mostly plant-forward diet, moderate exercise. Wants to understand whether her "
    "gut is okay and what to gently nudge. SYNTHETIC demo patient."
)

# Routed through OpenRouter (OpenAI-compatible API). Override with REPORT_MODEL.
MODEL = os.environ.get("REPORT_MODEL", "anthropic/claude-opus-4.8")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def build_prompt(results, pack):
    pack_text = "\n\n".join(f"[{k}]\n{v}" for k, v in pack.items())
    return (
        f"PATIENT:\n{PERSONA}\n\n"
        f"MEASUREMENTS (results.json):\n{json.dumps(results, indent=2)}\n\n"
        f"KNOWLEDGE PACK (cite these keys only):\n{pack_text}\n\n"
        "Write her report as JSON with keys:\n"
        "  headline: one warm, plain sentence summarizing her gut overall.\n"
        "  findings: array of objects {claim, value, citation, confidence, science_underneath}.\n"
        "    - claim: plain-language, talking to her.\n"
        "    - value: the relevant number from the measurements (e.g. '4.2%'), or ''.\n"
        "    - citation: a knowledge-pack key (e.g. 'taxa:faecalibacterium_prausnitzii').\n"
        "    - confidence: copy the card's confidence.\n"
        "    - science_underneath: 1-2 sentences of the underlying science.\n"
        "  footer: note that Maya is a synthetic demo patient and this is not medical advice.\n"
        "Ground every health claim in a knowledge-pack key via the citation field. "
        "Output ONLY the JSON."
    )


def main():
    results = json.load(open("data/results/results.json"))
    pack = load_pack()
    system = open("knowledge/rules.md").read()
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY not set (add it to .env)")

    resp = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "max_tokens": 4000,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": build_prompt(results, pack)},
            ],
        },
        timeout=180,
    )
    resp.raise_for_status()
    text = resp.json()["choices"][0]["message"]["content"].strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].removeprefix("json").strip()
    report = json.loads(text)
    with open("data/results/report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"wrote report.json via {MODEL}: {len(report['findings'])} findings")


if __name__ == "__main__":
    main()
