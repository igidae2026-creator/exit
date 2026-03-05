import json, os, time, random
from datetime import datetime, timezone

QUEST_PATH = "state/quest.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load_quest():
    if not os.path.exists(QUEST_PATH):
        return None
    try:
        with open(QUEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_quest(q):
    os.makedirs("state", exist_ok=True)
    tmp = QUEST_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(q, f, ensure_ascii=False)
    os.replace(tmp, QUEST_PATH)

def default_quest(domain_hint=None):
    # 간단 목표: score를 올리는 방향 + novelty/diversity 가중치 변화
    # (open-ended에서 핵심: 목표가 주기적으로 변해야 붕괴 방지)
    return {
        "id": str(int(time.time())),
        "created_at": now(),
        "domain_hint": domain_hint,
        "target": {
            "min_score": round(random.uniform(0.55, 0.75), 3),
            "min_novelty": round(random.uniform(0.40, 0.75), 3),
            "min_diversity": round(random.uniform(0.35, 0.75), 3),
        },
        "ttl_ticks": random.randint(200, 800),
        "tick_start": 0,
        "wins": 0,
        "fails": 0
    }

def ensure_quest(tick, domain_hint=None):
    q = load_quest()
    if q is None:
        q = default_quest(domain_hint)
        q["tick_start"] = tick
        save_quest(q)
        return q, True

    age = tick - int(q.get("tick_start", 0))
    ttl = int(q.get("ttl_ticks", 400))
    if age >= ttl:
        q = default_quest(domain_hint)
        q["tick_start"] = tick
        save_quest(q)
        return q, True

    return q, False

def update_quest(q, tick, best_score, last_metrics=None):
    # 성공 조건: best_score가 min_score 넘으면 win
    t = q["target"]
    if best_score >= t.get("min_score", 0.65):
        q["wins"] = int(q.get("wins", 0)) + 1
        # 목표 상향(점점 빡세게)
        q["target"]["min_score"] = round(min(0.95, q["target"]["min_score"] + 0.02), 3)

    # 실패 조건: ttl의 25%마다 진척 없으면 fail + 목표 재조정(너무 어렵다면 완화)
    age = tick - int(q.get("tick_start", 0))
    ttl = int(q.get("ttl_ticks", 400))
    if ttl > 0 and age > 0 and age % max(50, ttl // 4) == 0:
        # best_score가 목표치에서 멀면 fail
        if best_score < q["target"]["min_score"] - 0.10:
            q["fails"] = int(q.get("fails", 0)) + 1
            q["target"]["min_score"] = round(max(0.35, q["target"]["min_score"] - 0.03), 3)

    save_quest(q)
    return q
