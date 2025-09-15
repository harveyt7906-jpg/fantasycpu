import os, json, subprocess, openai, anthropic

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def ask_claude(role, logic):
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = f"As {role}, analyze this fantasy football JSON and give strategy: {json.dumps(logic)[:2000]}"
        r = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text.strip()
    except Exception as e:
        return f"Claude failed: {e}"


def ask_gpt(role, logic):
    try:
        openai.api_key = OPENAI_API_KEY
        prompt = f"As {role}, analyze this fantasy football JSON and give strategy: {json.dumps(logic)[:2000]}"
        r = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        return r["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"GPT-4o failed: {e}"


def ask_ollama(role, logic):
    try:
        prompt = f"As {role}, analyze this fantasy football JSON and give strategy: {json.dumps(logic)[:2000]}"
        r = subprocess.run(
            ["ollama", "run", "llama3.1", prompt],
            capture_output=True,
            text=True,
            timeout=45,
        )
        return r.stdout.strip()[:600]
    except Exception as e:
        return f"Ollama failed: {e}"


def consensus_text(responses):
    base = responses.get("claude", "")
    gpt = responses.get("gpt4o", "")
    oll = responses.get("ollama", "")
    consensus = "Claude verdict: " + base
    if gpt and not gpt.lower().startswith("gpt-4o failed"):
        consensus += " | GPT adds: " + gpt
    if oll and not oll.lower().startswith("ollama failed"):
        consensus += " | Ollama adds: " + oll
    return consensus[:1500]


def consult_council(role, logic):
    claude = ask_claude(role, logic)
    gpt = ask_gpt(role, logic)
    ollama = ask_ollama(role, logic)
    return {
        "claude": claude,
        "gpt4o": gpt,
        "ollama": ollama,
        "consensus": consensus_text({"claude": claude, "gpt4o": gpt, "ollama": ollama}),
    }
