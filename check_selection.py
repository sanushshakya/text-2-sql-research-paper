"""Diagnostic: does keyword schema selection include every table the gold SQL uses? (recall)
Tune the selector and descriptions on the DEV questions only; the test result is for information."""
import sys
import sqlglot
from sqlglot import exp
from t2s import questions, schema

split = sys.argv[1] if len(sys.argv) > 1 else "dev"
infos, descs = {}, {}
tot = hit = 0
sizes = []
for q in questions.load(split):
    db = q["db"]
    if db not in infos:
        infos[db], descs[db] = schema.introspect(db), schema.load_descriptions(db)
    need = {t.name for t in sqlglot.parse_one(q["gold_sql"], dialect="postgres").find_all(exp.Table)} & set(infos[db]["tables"])
    got = set(schema.select_tables(q["question"], infos[db], descs[db]))
    sizes.append((len(got), len(infos[db]["tables"])))
    tot += 1
    ok = need <= got
    hit += ok
    if not ok:
        print(f"{q['id']}: missing {sorted(need - got)}  (selected {sorted(got)})")
print(f"{split}: all gold tables selected for {hit}/{tot} questions; "
      f"mean tables sent {sum(s for s,_ in sizes)/len(sizes):.1f} of {sizes[0][1]}-{max(s for _,s in sizes)} available")
