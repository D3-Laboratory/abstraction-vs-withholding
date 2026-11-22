"""WLLFM v3: task metrics for withheld vs abstracted conversations with 95% CIs from resampling cases (5,000 draws, seed 25)."""
import json,glob,random,statistics,re
from collections import defaultdict
L={}
for f in glob.glob("experiments/results/target-disclosure-outcome-v23-luna/judgments/*/*.json"):
    j=json.load(open(f)); L[(j["case_id"],j["condition"])]=j
gated={"generic_feedback_v22","ci_feedback_v22","generic_gate_modify","ci_gate_modify","privacy_prompt_ci_gate_modify"}
rows=[]
for k,j in L.items():
    o=j["judgment"]["outcome"]
    if k[1] in gated and o in("WITHHELD","CONVEYED"):
        e=json.load(open(j["source_episode"])); u=e.get("utility_judge") or {}
        c=None
        try:
            a,b=u["coverage"]["UTILITY"]["HOW_MANY_ITEMS_COVERED"].split("/"); c=int(a)/int(b)
        except Exception: pass
        rows.append(dict(case=k[0],o=o,done=float(bool(e["completed"])),cov=c,rat=u.get("average_rating")))
def stat(rs,m,o):
    v=[x[m] for x in rs if x["o"]==o and x[m] is not None]; return sum(v)/len(v),len(v)
for m in["done","cov","rat"]:
    print(m,"W %.3f (n=%d)"%stat(rows,m,"WITHHELD"),"A %.3f (n=%d)"%stat(rows,m,"CONVEYED"))
# cluster bootstrap over cases
bycase=defaultdict(list)
for x in rows: bycase[x["case"]].append(x)
cases=list(bycase); rng=random.Random(25); B=5000
print("cases",len(cases))
for m in["done","cov","rat"]:
    d0=stat(rows,m,"WITHHELD")[0]-stat(rows,m,"CONVEYED")[0]; ds=[]
    for _ in range(B):
        samp=[x for c in rng.choices(cases,k=len(cases)) for x in bycase[c]]
        try: ds.append(stat(samp,m,"WITHHELD")[0]-stat(samp,m,"CONVEYED")[0])
        except ZeroDivisionError: pass
    ds.sort(); print(m,"diff W-A %.3f  95%% CI [%.3f, %.3f]"%(d0,ds[int(.025*len(ds))],ds[int(.975*len(ds))]))
