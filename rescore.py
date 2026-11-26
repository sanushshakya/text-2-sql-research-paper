"""Re-score a results file with the current evaluator (no LLM calls): re-runs each stored SQL and compares again.

  python rescore.py results/real/dev1.jsonl
Writes <name>_rescored.jsonl next to it and prints the old and new number correct per configuration.
"""
import json
import sys
from collections import Counter

from t2s import config, evaluate, questions
from t2s.validate import execute_readonly

path = sys.argv[1]
qmap = {q["id"]: q for q in questions.load("test") + questions.load("dev")}
gold = {}
old, new = Counter(), Counter()
out = open(path.replace(".jsonl", "_rescored.jsonl"), "w")
for line in open(path):
    r = json.loads(line)
    q = qmap[r["qid"]]
    if r["qid"] not in gold:
        gold[r["qid"]] = questions.gold_rows(q)
    ok = False
    if r["status"] == "ok" and r.get("sql"):
        res = execute_readonly(r["sql"], config.DSNS[q["db"]])
        ok = res.ok and evaluate.is_correct(res.rows, gold[r["qid"]], q["gold_sql"])
    old[r["config"]] += bool(r["correct"]); new[r["config"]] += ok
    r["correct"] = ok
    out.write(json.dumps(r) + "\n")
for c in sorted(new):
    print(f"config {c}: correct runs {old[c]} -> {new[c]}")
print("wrote", out.name)
