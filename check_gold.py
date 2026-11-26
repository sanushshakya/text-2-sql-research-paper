"""Run every gold query, show row counts and a sample, and check the validator accepts them."""
import sys
from t2s import questions, schema, validate, config

split = sys.argv[1] if len(sys.argv) > 1 else "test"
infos = {}
bad = 0
for q in questions.load(split):
    db = q["db"]
    if db not in infos:
        infos[db] = schema.sqlglot_schema(schema.introspect(db))
    try:
        rows = questions.gold_rows(q)
    except Exception as e:
        print(f"{q['id']}: GOLD ERROR {str(e).splitlines()[0]}"); bad += 1; continue
    chk = validate.validate(q["gold_sql"], infos[db], config.DSNS[db])
    flag = "" if chk.ok else f"  <-- VALIDATOR REJECTS: {chk.kind} {chk.message[:120]}"
    if not chk.ok: bad += 1
    if not rows: flag += "  <-- EMPTY RESULT"
    print(f"{q['id']:8} rows={len(rows):<4} {str(rows[:2])[:90]}{flag}")
print("problems:", bad)
