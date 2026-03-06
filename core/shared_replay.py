import os, json, random, shutil
from pathlib import Path

SHARED="shared_artifacts"
PARAMS=["quality","novelty","diversity","efficiency","cost"]

def clamp01(x):
    try: x=float(x)
    except: return 0.5
    return 0.0 if x<0 else 1.0 if x>1 else x

def load_shared(limit=2000):
    res=[]
    if not os.path.isdir(SHARED):
        return res
    for d in os.listdir(SHARED)[:limit]:
        p=Path(SHARED)/d/"artifact.json"
        if p.exists():
            try:
                obj=json.loads(p.read_text(encoding="utf-8"))
                if isinstance(obj, dict) and "strategy" in obj:
                    res.append(obj)
            except: pass
    return res

def sample_shared():
    arts=load_shared()
    if not arts:
        return None
    s = arts[random.randrange(len(arts))].get("strategy") or {}
    if not isinstance(s, dict):
        return None
    return {k: clamp01(s.get(k,0.5)) for k in PARAMS}

def publish_to_shared(artifact_dir, artifact_id):
    # artifact_dir/<uuid>/artifact.json -> shared_artifacts/<uuid>/artifact.json
    src = Path(artifact_dir)/artifact_id/"artifact.json"
    if not src.exists():
        return
    dst_dir = Path(SHARED)/artifact_id
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst_dir/"artifact.json")
