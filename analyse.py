"""Question-by-question analysis (no significance tests).

  python analyse.py results/real/final.jsonl [--out results/summary.md]

Per record: correct = status ok and rows equal the gold rows. Per question and configuration the
primary result is the majority over the three runs (correct in at least two). Prints and saves tables.
"""
import argparse
import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

from t2s import questions


def load(path):
    """Read a results file. Correctness is the flag stored at run time (computed from the real database values).

    Do NOT re-score from the text saved in `rows`: values are stored as strings, so types and columns cannot be
    compared reliably. To re-score after any change to the evaluator or a gold query, run `python rescore.py FILE`
    (it re-executes each stored SQL against the database) and analyse the *_rescored.jsonl file it writes.
    """
    recs = [json.loads(l) for l in open(path) if l.strip()]
    qmap = {q["id"]: q for q in questions.load("test") + questions.load("dev")}
    for r in recs:
        r["correct"] = bool(r["correct"])
        r["difficulty"] = qmap[r["qid"]]["difficulty"]
    return recs, qmap


def majority(recs):
    """{(qid, config): bool} correct in at least two of the runs (or the single run if only one)."""
    g = defaultdict(list)
    for r in recs:
        g[(r["qid"], r["config"])].append(r["correct"])
    return {k: sum(v) * 2 > len(v) for k, v in g.items()}, g


def pct(n, d):
    return f"{100 * n / d:.1f}%" if d else "-"


def build(recs, qmap):
    maj, g = majority(recs)
    cfgs = sorted({r["config"] for r in recs})
    qids = sorted({r["qid"] for r in recs})
    lines = []
    expected = len(qids) * len(cfgs)
    missing = [(q, c) for q in qids for c in cfgs if (q, c) not in maj]
    if missing:
        lines.append(f"> WARNING: incomplete results file: {len(missing)} of {expected} question/configuration pairs have no records "
                     f"(first few: {missing[:4]}). Re-run the same run_experiment.py command to resume before using these numbers.\n")
    lines.append("## Result correctness (majority of runs)\n")
    lines.append("| Configuration | Correct | Total | Accuracy |\n|---|---|---|---|")
    for c in cfgs:
        n = sum(maj[(q, c)] for q in qids if (q, c) in maj)
        d = sum(1 for q in qids if (q, c) in maj)
        lines.append(f"| {c} | {n} | {d} | {pct(n, d)} |")
    for label, key in (("database", lambda q: qmap[q]["db"]), ("difficulty", lambda q: qmap[q]["difficulty"])):
        lines.append(f"\n## Accuracy by {label}\n")
        groups = sorted({key(q) for q in qids})
        lines.append("| Configuration | " + " | ".join(groups) + " |\n|---|" + "---|" * len(groups))
        for c in cfgs:
            cells = []
            for gname in groups:
                qs = [q for q in qids if key(q) == gname and (q, c) in maj]
                cells.append(f"{sum(maj[(q, c)] for q in qs)}/{len(qs)}")
            lines.append(f"| {c} | " + " | ".join(cells) + " |")

    lines.append("\n## Questions fixed and broken (question by question)\n")
    lines.append("| Comparison | Fixed (first wrong, second right) | Broken (first right, second wrong) | Net |\n|---|---|---|---|")
    for a, b in (("A", "C"), ("A", "B"), ("B", "C")):
        if a in cfgs and b in cfgs:
            both = [q for q in qids if (q, a) in maj and (q, b) in maj]      # only questions answered by both
            fixed = sum(1 for q in both if not maj[(q, a)] and maj[(q, b)])
            broken = sum(1 for q in both if maj[(q, a)] and not maj[(q, b)])
            note = f" (of {len(both)} questions)" if len(both) < len(qids) else ""
            lines.append(f"| {a} -> {b}{note} | {fixed} | {broken} | {fixed - broken:+d} |")

    lines.append("\n## Errors by type (all runs)\n")
    lines.append("| Configuration | Syntax | Schema | EXPLAIN | Execution | Semantic (ran, wrong) | Rejected after retry | Runs |\n"
                 "|---|---|---|---|---|---|---|---|")
    for c in cfgs:
        rs = [r for r in recs if r["config"] == c]
        kinds = Counter(r["error_kind"] for r in rs if r["status"] != "ok")
        sem = sum(1 for r in rs if r["status"] == "ok" and not r["correct"])
        rej = sum(1 for r in rs if r["status"] == "rejected")
        lines.append(f"| {c} | {kinds['syntax']} | {kinds['schema']} | {kinds['explain']} | {kinds['execution']} | "
                     f"{sem} | {rej} | {len(rs)} |")

    lines.append("\n## Execution success, latency and LLM calls (all runs)\n")
    lines.append("| Configuration | Executed OK | Median latency (s) | Min-max (s) | Mean LLM calls | Retried |\n|---|---|---|---|---|---|")
    for c in cfgs:
        rs = [r for r in recs if r["config"] == c]
        lat = [r["latency_s"] for r in rs]
        ok = sum(1 for r in rs if r["status"] == "ok")
        lines.append(f"| {c} | {pct(ok, len(rs))} | {st.median(lat):.2f} | {min(lat):.2f}-{max(lat):.2f} | "
                     f"{st.mean(r['n_llm_calls'] for r in rs):.2f} | {sum(r['retried'] for r in rs)} |")

    lines.append("\n## Run-to-run stability\n")
    lines.append("| Configuration | Questions whose runs all agree | Questions |\n|---|---|---|")
    for c in cfgs:
        qs = [q for q in qids if (q, c) in g]
        agree = sum(1 for q in qs if len(set(g[(q, c)])) == 1)
        lines.append(f"| {c} | {agree} | {len(qs)} |")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--out")
    a = ap.parse_args()
    recs, qmap = load(a.path)
    text = build(recs, qmap)
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n")