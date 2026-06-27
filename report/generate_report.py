import json, os
from anthropic import Anthropic
from knowledge.pack_loader import load_pack

# Synthetic demo patient. Edit freely — only the persona is invented; the
# measurements in results.json are real.
PERSONA = (
    "Maya, 28, woman. Mild recurring bloating and occasional afternoon fatigue. "
    "Mostly plant-forward diet, moderate exercise. Wants to understand whether her "
    "gut is okay and what to gently nudge. SYNTHETIC demo patient."
)

MODEL = os.environ.get("REPORT_MODEL", "claude-opus-4-8")


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
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=system,
        messages=[{"role": "user", "content": build_prompt(results, pack)}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].removeprefix("json").strip()
    report = json.loads(text)
    with open("data/results/report.json", "w") as fh:
        json.dump(report, fh, indent=2)
    print(f"wrote report.json: {len(report['findings'])} findings")


if __name__ == "__main__":
    main()
