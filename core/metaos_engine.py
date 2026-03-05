import multiprocessing as mp
import random, json, uuid, os, time
import shutil
from datetime import datetime, timezone
from domains import load_domains

ART="artifact_store"
MAX_WORKERS = mp.cpu_count() * 4
domains = [d for d in load_domains() if hasattr(d, "generate")]

def now():
    return datetime.now(timezone.utc).isoformat()

def log(t,p):
    with open("events.jsonl","a") as f:
        f.write(json.dumps({"timestamp":now(),"event_type":t,"payload":p})+"\n")

def metric(m):
    with open("metrics.jsonl","a") as f:
        f.write(json.dumps({"timestamp":now(),"event_type":"metrics","payload":m})+"\n")

def strat():
    return {k:random.random() for k in ["quality","novelty","diversity","efficiency","cost"]}

def mutate(s):
    return {k:max(0,min(1,v+random.uniform(-0.2,0.2))) for k,v in s.items()}

def evaluate(s):
    score = s["quality"]*0.3+s["novelty"]*0.25+s["diversity"]*0.2+s["efficiency"]*0.15-s["cost"]*0.1
    s["score"]=score
    metric(s)
    return score

def artifact(s):
    aid=str(uuid.uuid4())
    p=f"{ART}/{aid}"
    os.makedirs(p,exist_ok=True)
    json.dump(s,open(f"{p}/artifact.json","w"))
    log("artifact",{"id":aid})

def cleanup():
    files = os.listdir("artifact_store")
    if len(files) > 5000:
        remove = files[:2000]
        for r in remove:
            shutil.rmtree(f"artifact_store/{r}", ignore_errors=True)

def worker(_):
    d = random.choice(domains)
    s = d.generate()
    s = mutate(s)
    score = evaluate(s)
    artifact(s)
    return score

def engine():
    workers = min(MAX_WORKERS, mp.cpu_count() * 4)
    pool = mp.Pool(workers)
    while True:
        scores = pool.map(worker, range(workers))
        avg = sum(scores) / len(scores)
        print("tick score:", avg, "workers:", workers)
        cleanup()
        time.sleep(1)

if __name__=="__main__":
    engine()
