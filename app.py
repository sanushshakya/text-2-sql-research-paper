import glob
import json
import os

import pandas as pd
import streamlit as st

from t2s import config, evaluate, llm, questions
from t2s.pipeline import Pipeline

st.set_page_config(page_title="Text-to-SQL demo", page_icon="🗄️", layout="wide")

CFG_NAMES = {
    "A": "A · Baseline",
    "B": "B · Schema-aware prompt",
    "C": "C · Schema-aware + validation",
}
CFG_HELP = {
    "A": "Question + the full list of tables and columns → model → run the SQL.",
    "B": "Keyword schema selection (top 4 tables + join path, with descriptions and keys) → model → run the SQL.",
    "C": "Same as B, then check the SQL (parse, single SELECT, tables/columns exist, EXPLAIN). One retry on failure, else rejected.",
}


# ----------------------------------------------------------------------------------------------- helpers
@st.cache_resource(show_spinner="Reading the database schema…")
def get_pipeline(db: str, provider: str, model: str):
    config.PROVIDER, config.MODEL_ID = provider, model      # same settings mechanism as the experiment
    return Pipeline(db, llm.make_llm())


@st.cache_data
def get_questions(db: str):
    qs = questions.load("test", db) + questions.load("dev", db)
    return {q["id"]: q for q in qs}


def to_frame(rows, limit=50):
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([[str(v) for v in r] for r in rows[:limit]])


def badge(rec):
    if rec.status == "ok":
        return "Query ran"
    if rec.status == "rejected":
        return "Rejected after retry (system declines to answer)"
    return f"Database error ({rec.error_kind})"


def find_result_files():
    out = {}
    for label, pat in [("Qwen2.5-Coder 7B", "*qwen7b*rescored.jsonl"), ("Qwen2.5-Coder 14B", "*qwen14b*rescored.jsonl")]:
        hits = sorted(glob.glob(os.path.join("results", "**", pat), recursive=True))
        hits = [h for h in hits if "dev" not in os.path.basename(h)]
        if hits:
            out[label] = hits[-1]
    return out


# ----------------------------------------------------------------------------------------------- sidebar
st.sidebar.title("Settings")
db = st.sidebar.selectbox("Database", ["shopdb", "northwind"], format_func=lambda d: {"shopdb": "UK grocery shop (synthetic)", "northwind": "Northwind (public sample)"}[d])
provider = st.sidebar.text_input("Provider", config.PROVIDER, help="e.g. openai_compatible for Ollama (set T2S_BASE_URL=http://localhost:11434/v1)")
model = st.sidebar.text_input("Model", config.MODEL_ID or "qwen2.5-coder:7b")
st.sidebar.caption("Temperature 0, one answer per configuration. Local models: the first call is slow while the model loads.")

tab_demo, tab_results, tab_how = st.tabs(["Live demo", "Study results", "How it works"])

# ----------------------------------------------------------------------------------------------- live demo
with tab_demo:
    st.title("Lightweight schema-aware prompting + SQL validation")
    st.write("Ask a business question in plain English. The same model answers it three ways, so you can see what each added step changes.")

    qmap = get_questions(db)
    source = st.radio("Question", ["Pick a study question", "Type my own"], horizontal=True)
    gold_q = None
    if source == "Pick a study question":
        qid = st.selectbox("Study questions (test + dev)", list(qmap), format_func=lambda i: f"{i} · {qmap[i]['difficulty']} · {qmap[i]['question']}")
        gold_q = qmap[qid]
        question = gold_q["question"]
        st.info(question)
    else:
        question = st.text_input("Your question", "How many orders were cancelled?")
        qid = "adhoc"
    cfgs = st.multiselect("Configurations to run", list(CFG_NAMES), default=list(CFG_NAMES), format_func=lambda c: CFG_NAMES[c])

    if st.button("Run", type="primary", disabled=not (question and cfgs)):
        try:
            pipe = get_pipeline(db, provider, model)
        except Exception as e:                                   # database or LLM settings problem
            st.error(f"Could not start the pipeline: {e}")
            st.stop()
        gold_rows = None
        if gold_q:
            gold_rows = questions.gold_rows(gold_q)
        cols = st.columns(len(cfgs))
        for col, c in zip(cols, cfgs):
            with col:
                st.subheader(CFG_NAMES[c])
                st.caption(CFG_HELP[c])
                with st.spinner("Asking the model…"):
                    try:
                        rec = pipe.run(c, qid, question)
                    except Exception as e:
                        st.error(f"Model call failed: {e}")
                        continue
                st.markdown(f"**{badge(rec)}**")
                if gold_rows is not None and rec.status == "ok":
                    ok = evaluate.is_correct(rec.rows, gold_rows, gold_q["gold_sql"])
                    st.markdown("**Matches the gold result: " + ("yes**" if ok else "no**"))
                m1, m2, m3 = st.columns(3)
                m1.metric("Latency", f"{rec.latency_s:.1f} s")
                m2.metric("LLM calls", rec.n_llm_calls)
                m3.metric("Retried", "yes" if rec.retried else "no")
                if rec.selected_tables:
                    st.write("Tables shown to the model: " + ", ".join(f"`{t}`" for t in rec.selected_tables))
                elif c == "A":
                    st.write("Tables shown to the model: all of them (raw names only)")
                st.code(rec.sql or "(no SQL)", language="sql")
                if rec.status != "ok":
                    st.error(rec.error_message)
                elif rec.rows is not None:
                    st.write(f"{len(rec.rows)} row(s)")
                    st.dataframe(to_frame(rec.rows), width="stretch")
                if len(rec.attempts) > 1 or (c == "C" and rec.retried):
                    with st.expander("Validation and retry trail"):
                        for i, a in enumerate(rec.attempts, 1):
                            st.write(f"Attempt {i}: {'passed' if a['ok'] else 'failed – ' + a['kind']}")
                            st.code(a["sql"], language="sql")
                            if a["message"]:
                                st.caption(a["message"])
        if gold_q:
            with st.expander("Gold (reference) query and its meaning"):
                st.write(gold_q["meaning"])
                st.code(gold_q["gold_sql"], language="sql")
                st.dataframe(to_frame(gold_rows), width="stretch")

# ----------------------------------------------------------------------------------------------- results
with tab_results:
    st.title("Final study results")
    st.write("100 test questions (50 Northwind, 50 shop), majority of runs, re-scored files.")
    files = find_result_files()
    rows = []
    for label, path in files.items():
        per_q = {}
        for line in open(path):
            r = json.loads(line)
            per_q.setdefault((r["config"], r["qid"]), []).append(bool(r["correct"]))
        for c in "ABC":
            n = sum(1 for (cc, _), v in per_q.items() if cc == c and sum(v) * 2 > len(v))
            rows.append({"Model": label, "Config": CFG_NAMES[c], "Correct (of 100)": n})
    if not rows:                                                 # report figures, if result files are not next to the app
        st.caption("Result files not found in ./results, showing the figures from the report.")
        for label, vals in [("Qwen2.5-Coder 7B", (59, 73, 73)), ("Qwen2.5-Coder 14B", (62, 73, 73))]:
            for c, v in zip("ABC", vals):
                rows.append({"Model": label, "Config": CFG_NAMES[c], "Correct (of 100)": v})
    df = pd.DataFrame(rows)
    st.bar_chart(df.pivot(index="Config", columns="Model", values="Correct (of 100)"))
    st.dataframe(df.pivot(index="Config", columns="Model", values="Correct (of 100)"), width="stretch")
    st.markdown(
        "- Schema selection with descriptions fixed 20 questions and broke 6 (7B), and fixed 17 and broke 6 (14B).\n"
        "- Adding validation (C) changed no answers compared with B: it turned database errors into explicit rejections.\n"
        "- Median latency: +19% to +22% for B and +35% to +44% for C compared with A.\n"
        "- Main weakness: when the keyword selector omits a needed table, B was right on only 1 of 9 (7B) and 0 of 9 (14B) questions."
    )

# - how it works
with tab_how:
    st.title("How the system works")
    st.markdown(
        """
1. **Question** in plain English.
2. **Schema selection (B, C):** keywords are matched against table names, descriptions and columns (weights 3, 2, 1); the top 4 tables plus a bridging table are sent with descriptions, primary and foreign keys. **A** sends every table and column name.
3. **Model:** Qwen2.5-Coder (7B or 14B, 4-bit) running locally in Ollama, temperature 0, returns one PostgreSQL SELECT.
4. **Validation (C only):** sqlglot parses it as PostgreSQL and checks it is a single SELECT; every table and column must exist; PostgreSQL `EXPLAIN` must accept it. On failure the model gets one retry that includes the previous SQL and the error; if that fails the query is **rejected**.
5. **Execution:** read-only transaction, 10 s time limit.
6. **Scoring (study only):** result rows are compared with the gold query's rows.
"""
    )