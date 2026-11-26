# Lightweight schema-aware prompting and SQL validation for LLM Text-to-SQL

Code for the MSc project *Evaluating a Lightweight Schema-Aware Prompting and SQL Validation Approach for
LLM-Based Text-to-SQL in Business Data Queries* (Sanush Shakya, B01847444, University of the West of Scotland).

Three configurations answer the same business questions on two PostgreSQL databases:

| Config | What the LLM gets | After the LLM answers |
|---|---|---|
| A baseline | question + raw table and column names | run the SQL |
| B schema-only | question + keyword-selected tables with descriptions, columns, primary and foreign keys | run the SQL |
| C enhanced | same as B | validate (single SELECT, parses as PostgreSQL, tables and columns exist, EXPLAIN accepts) -> read-only execution with time limit -> one retry with the error message -> otherwise rejected |

Model: `qwen2.5-coder:14b`, temperature 0 (set in `t2s/config.py`).
Results are compared question by question (fixed / broken), with no significance tests.

## 1. Set up

```bash
pip install -r requirements.txt
createdb northwind && psql -d northwind -f db/northwind.sql         # public Northwind sample data (Ms-PL, see db/NORTHWIND_LICENSE.txt)
createdb shopdb && python db/build_synthetic.py --dsn "host=localhost dbname=shopdb user=postgres"   # seeded, reproducible
```
Edit the DSNs in `t2s/config.py` (or set `T2S_DSN_NORTHWIND` / `T2S_DSN_SHOPDB`) if your server differs.
Built and tested on PostgreSQL 16, Python 3.13, sqlglot 30.25, psycopg 3.3, anthropic 2.3.

## 2. Check before spending anything

```bash
python -m pytest -q tests          # 14 offline tests: validator, retry, read-only execution, scoring
python check_gold.py test          # every gold query runs, returns rows and passes the validator
python check_selection.py dev      # schema-selection recall (tune on DEV only)
python run_experiment.py --split test --tag dryrun --oracle   # plumbing test: gold SQL as the "answer" -> must score 100%
```
`--oracle` results go to `results/dryrun/` and are never results.

## 3. Real runs

Pick the model with environment variables (one model for the whole experiment; record its exact id and the date):

```bash
# free option, GitHub Models (key = a GitHub personal access token with the models scope)
export T2S_PROVIDER=github  T2S_MODEL=openai/gpt-4o-mini  GITHUB_TOKEN=...
# or: T2S_PROVIDER=groq (GROQ_API_KEY) | cerebras (CEREBRAS_API_KEY) | gemini (GEMINI_API_KEY) | anthropic (ANTHROPIC_API_KEY)
# any other OpenAI-style endpoint: T2S_PROVIDER=openai_compatible T2S_BASE_URL=... T2S_KEY_ENV=NAME_OF_KEY_VARIABLE T2S_MODEL=...
export T2S_MIN_INTERVAL=4     # optional: seconds between calls, to stay inside a free tier's per-minute limit
```

Rate-limit (429) replies are waited out and retried automatically; the wait is not counted in latency. If a daily limit
is hit the run stops with an error; start it again the next day and it resumes where it stopped.

```bash
python run_experiment.py --split dev  --tag dev1     # tune prompts / descriptions on the dev questions only
# freeze prompts (t2s/prompts.py), descriptions/ and the test set, commit, then:
python run_experiment.py --split test --tag final    # 100 questions x A,B,C x 3 runs (resumable)
python analyse.py results/real/final.jsonl --out results/summary.md
```

## 4. Rules that keep the comparison fair

* Test questions and gold SQL are written and frozen **before any test question is run**; never edit them after.
* Prompts, descriptions and the selector are tuned on the 10 development questions only, then frozen.
* Questions avoid relative dates ("this month"); they use explicit years.
* Results are compared by rows, not by SQL text (`t2s/evaluate.py` documents the rules).
* Record the exact model string, date of the runs and library versions in the dissertation.

## Layout

`t2s/` pipeline (schema, prompts, validate, pipeline, evaluate, llm) - `questions/` test and dev sets with gold SQL and the
documented meaning of each question - `descriptions/` table and column descriptions used by B and C - `db/` data scripts -
`tests/` offline tests - `run_experiment.py`, `analyse.py` - `results/real/` raw records (one JSON line per answer).
