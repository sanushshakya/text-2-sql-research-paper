"""Run configurations A, B and C over a question split, interleaved, and append every record to JSONL.

  python run_experiment.py --split dev  --tag dev1                (needs an API key, see README: T2S_PROVIDER / T2S_MODEL)
  python run_experiment.py --split test --tag final               (only after the test set is frozen)
  python run_experiment.py --split test --tag dryrun --oracle     (offline plumbing test: NOT a result)

The run is resumable: records already in the file are skipped.
"""
import argparse
import json
import random
from pathlib import Path

from t2s import config, evaluate, questions
from t2s.llm import make_llm, LLMReply
from t2s.pipeline import Pipeline


class OracleLLM:
    """Plumbing test only: answers with the gold SQL of the question being asked."""
    def __init__(self, qmap):
        self.qmap, self.current = qmap, None

    def complete(self, system, user):
        return LLMReply(self.qmap[self.current]["gold_sql"], 0.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], default="dev")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--configs", nargs="+", default=["A", "B", "C"])
    ap.add_argument("--runs", type=int, default=config.N_RUNS)
    ap.add_argument("--oracle", action="store_true", help="offline plumbing test with gold SQL as the answer")
    args = ap.parse_args()

    qs = questions.load(args.split)
    qmap = {q["id"]: q for q in qs}
    gold = {q["id"]: questions.gold_rows(q) for q in qs}
    llm = OracleLLM(qmap) if args.oracle else make_llm()
    out_dir = Path(__file__).parent / "results" / ("dryrun" if args.oracle else "real")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{args.tag}.jsonl"
    done = set()
    if path.exists():
        for line in path.open():
            r = json.loads(line)
            done.add((r["qid"], r["config"], r["run"]))

    pipes = {db: Pipeline(db, llm) for db in {q["db"] for q in qs}}
    rng = random.Random(7)          # fixed seed: the interleaving order is reproducible
    with path.open("a") as f:
        for run in range(1, args.runs + 1):
            order = [(q, c) for q in qs for c in args.configs]
            rng.shuffle(order)      # interleave configurations and questions within each run
            for q, c in order:
                if (q["id"], c, run) in done:
                    continue
                if args.oracle:
                    llm.current = q["id"]
                rec = pipes[q["db"]].run(c, q["id"], q["question"], run)
                row = rec.to_json()
                row["correct"] = rec.status == "ok" and evaluate.is_correct(rec.rows, gold[q["id"]], q["gold_sql"])
                row["model"] = f"{config.PROVIDER}:{config.MODEL_ID}" if not args.oracle else "oracle"
                f.write(json.dumps(row, default=str) + "\n")
                f.flush()
    print("wrote", path)


if __name__ == "__main__":
    main()
