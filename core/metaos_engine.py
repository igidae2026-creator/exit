import multiprocessing as mp
import random, json, uuid, os, time
from datetime import datetime, timezone

ART="artifact_store"

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

def evals(s):
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

def worker(_):
    s=mutate(strat())
    score=evals(s)
    artifact(s)
    return score

def run():
    pool=mp.Pool(mp.cpu_count())
    while True:
        scores=pool.map(worker,range(mp.cpu_count()))
        print("tick:",sum(scores)/len(scores))
        time.sleep(1)

if __name__=="__main__":
    run()
