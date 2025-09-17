import os, logging
from openai import OpenAI
import anthropic, requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

def _ask_claude(prompt, max_tokens=512):
    if not ANTHROPIC_API_KEY: return {"model":"claude","error":"no_key"}
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        resp = client.messages.create(model="claude-3-haiku-20240307",max_tokens=max_tokens,
                                      messages=[{"role":"user","content":prompt}])
        return {"model":"claude","text":resp.content[0].text}
    except Exception as e: return {"model":"claude","error":str(e)}

def _ask_openai(prompt, max_tokens=512):
    if not OPENAI_API_KEY: return {"model":"openai","error":"no_key"}
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],max_tokens=max_tokens)
        return {"model":"openai","text":resp.choices[0].message.content}
    except Exception as e: return {"model":"openai","error":str(e)}

def _ask_ollama(prompt, max_tokens=512):
    try:
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model":OLLAMA_MODEL,"prompt":prompt,"stream":False})
        if r.ok:
            return {"model":"ollama","text":r.json().get("response","")}
        return {"model":"ollama","error":r.text}
    except Exception as e: return {"model":"ollama","error":str(e)}

def consult_council(role, bundle):
    prompt = f"You are the {role}. Inputs:\n{bundle}\nGive final decree JSON with keys: decision, rationale."
    results = []
    results.append(_ask_claude(prompt))
    results.append(_ask_openai(prompt))
    results.append(_ask_ollama(prompt))
    decree = {"council":results}
    votes = [r.get("text","") for r in results if "text" in r]
    decree["decree"] = votes[0] if votes else "no consensus"
    return decree
