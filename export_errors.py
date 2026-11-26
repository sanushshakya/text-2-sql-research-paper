"""Export every wrong answer to a CSV so semantic errors can be labelled by hand.

  python export_errors.py results/real/final_qwen7b.jsonl results/real/final_qwen14b.jsonl \
         --names qwen7b qwen14b --out results/errors_to_label.csv
"""
import argparse
import csv
from pathlib import Path

import sqlglot
from sqlglot import exp

import analyse


def tables_in(sql):
    try:
        tree = sqlglot.parse_one(sql, read="postgres")
    except Exception:
        return set()
    ctes = {c.alias for c in tree.find_all(exp.CTE)}
    return {t.name for t in tree.find_all(exp.Table) if t.name and t.name not in ctes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--names", nargs="+")
    ap.add_argument("--out", default="results/errors_to_label.csv")
    a = ap.parse_args()
    names = a.names or [Path(f).stem.replace("final_", "") for f in a.files]
    rows = []
    for n, f in zip(names, a.files):
        recs, qmap = analyse.load(f)
        maj, _ = analyse.majority(recs)
        first = {}
        for r in sorted(recs, key=lambda r: r["run"]):
            first.setdefault((r["qid"], r["config"]), r)
        for (q, c), ok in sorted(maj.items()):
            if ok:
                continue
            r, qi = first[(q, c)], qmap[q]
            gold_t = tables_in(qi["gold_sql"])
            shown = set(r.get("selected_tables") or [])
            missing = sorted(gold_t - shown) if c in ("B", "C") and shown else []
            if r["status"] == "rejected":
                auto = f"rejected after retry ({r.get('error_kind', '')})"
            elif r["status"] != "ok":
                auto = f"{r.get('error_kind', 'error')} error"
            elif missing:
                auto = "selector did not show a needed table"
            else:
                auto = ""
            rows.append([n, c, q, qi["db"], qi["difficulty"], qi["question"], qi.get("meaning", ""), qi["gold_sql"],
                         r.get("sql", ""), r["status"], r.get("error_kind", ""), (r.get("error_message") or "")[:300],
                         ";".join(sorted(shown)), ";".join(sorted(gold_t)), ";".join(missing), auto, "", ""])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "config", "qid", "database", "difficulty", "question", "documented_meaning", "gold_sql",
                    "predicted_sql", "status", "error_kind", "error_message", "tables_shown", "tables_in_gold",
                    "missing_from_selected", "auto_label", "error_type (fill in)", "notes"])
        w.writerows(rows)
    print(f"wrote {a.out}: {len(rows)} wrong answers to label")


if __name__ == "__main__":
    main()