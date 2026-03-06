import os, time, shutil
from pathlib import Path

SHARED="shared_artifacts"

# 공유 정책(필요하면 숫자만 바꿔)
TOPK_SCORE = float(os.getenv("METAOS_SHARE_MIN_SCORE", "0.72"))  # 이 점수 이상만 공유
MAX_SHARED = int(os.getenv("METAOS_MAX_SHARED", "6000"))         # shared 최대 개수
SHARED_CLEAN_N = int(os.getenv("METAOS_SHARED_CLEAN_N", "2000")) # 초과 시 삭제 개수

def shared_count():
    try:
        return len(os.listdir(SHARED))
    except Exception:
        return 0

def ensure_shared_dirs():
    Path(SHARED).mkdir(parents=True, exist_ok=True)

def cleanup_shared():
    try:
        ensure_shared_dirs()
        items = [str(Path(SHARED)/d) for d in os.listdir(SHARED)]
        if len(items) <= MAX_SHARED:
            return
        items.sort(key=lambda p: os.path.getmtime(p))
        for p in items[:SHARED_CLEAN_N]:
            shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass

def should_publish(score: float) -> bool:
    try:
        return float(score) >= TOPK_SCORE
    except Exception:
        return False
