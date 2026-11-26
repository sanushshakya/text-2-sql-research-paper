"""Compare models side by side (descriptive, no significance tests).

  python compare_models.py results/real/final_qwen7b.jsonl results/real/final_qwen14b.jsonl \
         --names qwen7b qwen14b --out results/compare.md

Reads each results file with the same scoring as analyse.py, and writes:
  results/compare.md          tables for the results chapter
  results/per_question.csv    one row per question: correct (1/0) for every model and configuration
  results/gold_audit.csv      questions that EVERY model and configuration got wrong (check the question and the gold SQL)
  results/fig_accuracy.png    accuracy by configuration, one bar per model        (needs matplotlib)
  results/fig_fixed_broken.png  questions fixed and broken by each step           (needs matplotlib)
Only questions answered by every file are compared; a warning is printed if the files cover different questions.
"""
import argparse
import csv
from collections import Counter
from pathlib import Path
import statistics as st

import analyse


def pct(n, d):
    return f"{n}/{d} ({100 * n / d:.0f}%)" if d else "-"


def load_model(path):
    recs, qmap = analyse.load(path)
    maj, _ = analyse.majority(recs)
    first = {}
    for r in sorted(recs, key=lambda r: r["run"]):
        first.setdefault((r["qid"], r["config"]), r)           # run 1 record, for the SQL shown in the audit
    return {"recs": recs, "maj": maj, "first": first, "cfgs": sorted({r["config"] for r in recs}),
            "qids": {r["qid"] for r in recs}}, qmap


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--names", nargs="+")
    ap.add_argument("--out", default="results/compare.md")
    a = ap.parse_args()
    names = a.names or [Path(f).stem.replace("final_", "") for f in a.files]
    if len(names) != len(a.files):
        raise SystemExit("--names must have one name per file")
    models, qmap = {}, {}
    for n, f in zip(names, a.files):
        models[n], qm = load_model(f)
        qmap.update(qm)

    common = set.intersection(*(m["qids"] for m in models.values()))
    union = set.union(*(m["qids"] for m in models.values()))
    qids = sorted(common)
    out_dir = Path(a.out).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    cfgs = sorted(set.intersection(*(set(m["cfgs"]) for m in models.values())))
    L = []
    if common != union:
        L.append(f"> WARNING: the files cover different questions ({len(union)} in total, {len(common)} in all of them). "
                 "Only the common questions are compared.\n")
    for n, m in models.items():
        miss = [(q, c) for q in qids for c in cfgs if (q, c) not in m["maj"]]
        if miss:
            L.append(f"> WARNING: {n} has {len(miss)} missing question/configuration results (e.g. {miss[:3]}); finish that run first.\n")

    # 1 overall
    L.append(f"## Result correctness, {len(qids)} questions (correct in the majority of runs)\n")
    L.append("| Model | " + " | ".join(cfgs) + " |\n|---|" + "---|" * len(cfgs))
    for n, m in models.items():
        L.append(f"| {n} | " + " | ".join(pct(sum(m["maj"].get((q, c), False) for q in qids), len(qids)) for c in cfgs) + " |")

    # 2 by database and difficulty
    for label, key in (("database", lambda q: qmap[q]["db"]), ("difficulty", lambda q: qmap[q]["difficulty"])):
        groups = sorted({key(q) for q in qids})
        L.append(f"\n## Accuracy by {label}\n")
        L.append("| Model | Configuration | " + " | ".join(groups) + " |\n|---|---|" + "---|" * len(groups))
        for n, m in models.items():
            for c in cfgs:
                cells = []
                for g in groups:
                    qs = [q for q in qids if key(q) == g]
                    cells.append(f"{sum(m['maj'].get((q, c), False) for q in qs)}/{len(qs)}")
                L.append(f"| {n} | {c} | " + " | ".join(cells) + " |")

    # 3 fixed and broken
    pairs = [(x, y) for x, y in (("A", "B"), ("A", "C"), ("B", "C")) if x in cfgs and y in cfgs]
    L.append("\n## Questions fixed and broken (question by question)\n")
    L.append("| Model | Comparison | Fixed (first wrong, second right) | Broken (first right, second wrong) | Net |\n|---|---|---|---|---|")
    fb = {}
    for n, m in models.items():
        for x, y in pairs:
            fixed = sum(1 for q in qids if not m["maj"].get((q, x)) and m["maj"].get((q, y)))
            broken = sum(1 for q in qids if m["maj"].get((q, x)) and not m["maj"].get((q, y)))
            fb[(n, x, y)] = (fixed, broken)
            L.append(f"| {n} | {x} -> {y} | {fixed} | {broken} | {fixed - broken:+d} |")

    # 4 errors
    L.append("\n## Errors by type (all runs)\n")
    L.append("| Model | Config | Syntax | Schema | EXPLAIN | Execution | Semantic (ran, wrong) | Rejected after retry | Runs |\n"
             "|---|---|---|---|---|---|---|---|---|")
    for n, m in models.items():
        for c in cfgs:
            rs = [r for r in m["recs"] if r["config"] == c and r["qid"] in common]
            k = Counter(r["error_kind"] for r in rs if r["status"] != "ok")
            sem = sum(1 for r in rs if r["status"] == "ok" and not r["correct"])
            rej = sum(1 for r in rs if r["status"] == "rejected")
            L.append(f"| {n} | {c} | {k['syntax']} | {k['schema']} | {k['explain']} | {k['execution']} | {sem} | {rej} | {len(rs)} |")

    # 5 latency
    L.append("\n## Latency and LLM calls (all runs; local-model latency depends on the hardware used)\n")
    L.append("| Model | Config | Median latency (s) | Min-max (s) | Mean LLM calls | Retried |\n|---|---|---|---|---|---|")
    for n, m in models.items():
        for c in cfgs:
            rs = [r for r in m["recs"] if r["config"] == c and r["qid"] in common]
            if rs:
                lat = [r["latency_s"] for r in rs]
                L.append(f"| {n} | {c} | {st.median(lat):.2f} | {min(lat):.2f}-{max(lat):.2f} | "
                         f"{st.mean(r['n_llm_calls'] for r in rs):.2f} | {sum(r['retried'] for r in rs)} |")

    # 6 overlap between models
    if len(models) == 2:
        n1, n2 = list(models)
        L.append(f"\n## Which model answers each question correctly ({n1} vs {n2})\n")
        L.append(f"| Config | Both correct | Only {n1} | Only {n2} | Neither |\n|---|---|---|---|---|")
        for c in cfgs:
            r1 = {q: models[n1]["maj"].get((q, c), False) for q in qids}
            r2 = {q: models[n2]["maj"].get((q, c), False) for q in qids}
            L.append(f"| {c} | {sum(r1[q] and r2[q] for q in qids)} | {sum(r1[q] and not r2[q] for q in qids)} | "
                     f"{sum(r2[q] and not r1[q] for q in qids)} | {sum(not r1[q] and not r2[q] for q in qids)} |")

    # per-question csv and gold audit
    cols = [(n, c) for n in models for c in cfgs]
    with open(out_dir / "per_question.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["qid", "database", "difficulty", "question"] + [f"{n}_{c}" for n, c in cols])
        for q in qids:
            w.writerow([q, qmap[q]["db"], qmap[q]["difficulty"], qmap[q]["question"]] +
                       [int(bool(models[n]["maj"].get((q, c), False))) for n, c in cols])
    all_fail = [q for q in qids if not any(models[n]["maj"].get((q, c), False) for n, c in cols)]
    with open(out_dir / "gold_audit.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["qid", "database", "difficulty", "question", "documented_meaning", "gold_sql"] +
                   [f"{n}_{c}_sql" for n, c in cols] + ["your_verdict (gold ok / gold wrong / question ambiguous)", "notes"])
        for q in all_fail:
            w.writerow([q, qmap[q]["db"], qmap[q]["difficulty"], qmap[q]["question"], qmap[q].get("meaning", ""), qmap[q]["gold_sql"]] +
                       [(models[n]["first"].get((q, c)) or {}).get("sql", "") for n, c in cols] + ["", ""])
    L.append(f"\n## Questions that no model or configuration answered correctly: {len(all_fail)}\n")
    L.append("These are the first to check for a flawed question or gold query (results/gold_audit.csv). If a gold query is wrong, fix it "
             "openly, say so in the dissertation and re-score with rescore.py; do not drop questions quietly.\n")
    L.append(", ".join(all_fail) if all_fail else "None.")

    text = "\n".join(L) + "\n"
    Path(a.out).write_text(text)
    print(text)
    print("wrote", a.out, ", per_question.csv, gold_audit.csv")

    # figures
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: skipping figures (pip install matplotlib)")
        return
    width = 0.8 / len(models)
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, (n, m) in enumerate(models.items()):
        vals = [100 * sum(m["maj"].get((q, c), False) for q in qids) / len(qids) for c in cfgs]
        bars = ax.bar([x + i * width for x in range(len(cfgs))], vals, width, label=n)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}", ha="center", fontsize=8)
    ax.set_xticks([x + width * (len(models) - 1) / 2 for x in range(len(cfgs))])
    ax.set_xticklabels(cfgs)
    ax.set_ylabel("Correct results (%)")
    ax.set_xlabel("Configuration")
    ax.set_ylim(0, 105)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / "fig_accuracy.png", dpi=200)
    if pairs:
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = [f"{x} to {y}" for x, y in pairs]
        for i, n in enumerate(models):
            fixed = [fb[(n, x, y)][0] for x, y in pairs]
            broken = [-fb[(n, x, y)][1] for x, y in pairs]
            pos = [p + i * width for p in range(len(pairs))]
            ax.bar(pos, fixed, width, label=f"{n} fixed")
            ax.bar(pos, broken, width, label=f"{n} broken")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks([p + width * (len(models) - 1) / 2 for p in range(len(pairs))])
        ax.set_xticklabels(labels)
        ax.set_ylabel("Questions")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out_dir / "fig_fixed_broken.png", dpi=200)
    print("wrote fig_accuracy.png, fig_fixed_broken.png")


if __name__ == "__main__":
    main()