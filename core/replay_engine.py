import os, json, random
from pathlib import Path

ART="artifact_store"
PARAMS=["quality","novelty","diversity","efficiency","cost"]

def load_artifacts(limit=2000):
    res=[]
    if not os.path.isdir(ART):
        return res
    for d in os.listdir(ART)[:limit]:
        p=Path(ART)/d/"artifact.json"
        if p.exists():
            try:
                obj=json.loads(p.read_text(encoding="utf-8"))
                # payload 형태(artifact.json이 {"strategy":..., "meta":...})를 기대
                if isinstance(obj, dict) and "strategy" in obj:
                    res.append(obj)
            except Exception:
                pass
    return res

def mutate(s, sigma=0.10):
    out=dict(s)
    for k in PARAMS:
        v=float(out.get(k,0.5))
        v=v+random.uniform(-sigma,sigma)
        out[k]=0.0 if v<0 else 1.0 if v>1 else v
    return out

def replay_sample():
    arts=load_artifacts()
    if not arts:
        return None
    a=random.choice(arts)
    s=a.get("strategy") or {}
    if not isinstance(s, dict):
        return None
    return mutate(s)
