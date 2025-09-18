import os, httpx
from anthropic import Anthropic
from openai import OpenAI

claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def llm_generate(prompt: str, max_tokens: int = 250) -> str:
    try:
        r = claude.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=max_tokens,
            messages=[{"role":"user","content":prompt}]
        )
        return r.content[0].text.strip()
    except Exception:
        try:
            r = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                max_tokens=max_tokens
            )
            return r.choices[0].message.content.strip()
        except Exception:
            try:
                r = httpx.post(
                    f"{ollama_host}/api/generate",
                    json={"model":"llama3.1","prompt":prompt,"stream":False},
                    timeout=60
                )
                return r.json().get("response","").strip()
            except Exception as e:
                return f"LLM error: {e}"
