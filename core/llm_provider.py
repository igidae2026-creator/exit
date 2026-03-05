import os, json, urllib.request, urllib.error

# Strategy schema expected by daemon:
# {"quality":0-1, "novelty":0-1, "diversity":0-1, "efficiency":0-1, "cost":0-1}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")  # 빠른 모델 추천
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def _clamp01(x):
    try:
        x = float(x)
    except Exception:
        return 0.5
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def _normalize(d):
    return {
        "quality": _clamp01(d.get("quality", 0.5)),
        "novelty": _clamp01(d.get("novelty", 0.5)),
        "diversity": _clamp01(d.get("diversity", 0.5)),
        "efficiency": _clamp01(d.get("efficiency", 0.5)),
        "cost": _clamp01(d.get("cost", 0.5)),
    }

def _openai_strategy(domain_name, context):
    if not OPENAI_API_KEY:
        return None

    prompt = {
        "domain": domain_name,
        "context": context or {},
        "task": "Propose a strategy as JSON with keys quality, novelty, diversity, efficiency, cost in [0,1]. Output JSON only."
    }

    body = {
        "model": OPENAI_MODEL,
        "input": [
            {"role":"system","content":"You output ONLY valid JSON. No prose."},
            {"role":"user","content":json.dumps(prompt)}
        ],
        "response_format": {"type":"json_object"}
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return None
    except Exception:
        return None

    # responses API 형태 대응: output_text or structured output
    text = None
    try:
        # best-effort parse
        if "output_text" in data and data["output_text"]:
            text = data["output_text"]
        else:
            # some variants store content in output[0].content[0].text
            out = data.get("output", [])
            if out:
                c = out[0].get("content", [])
                if c and "text" in c[0]:
                    text = c[0]["text"]
    except Exception:
        text = None

    if not text:
        return None

    try:
        obj = json.loads(text)
    except Exception:
        return None

    return _normalize(obj)

def generate_llm_strategy(domain_name, context=None):
    # Priority: OpenAI -> (Gemini later) -> None (fallback to domain.generate)
    s = _openai_strategy(domain_name, context)
    if s is not None:
        return s
    return None
