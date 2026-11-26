"""Load the question sets and execute gold SQL to get the gold results."""
import importlib
import psycopg

from . import config

MODULES = {"northwind": "questions.northwind", "shopdb": "questions.shopdb"}


def load(split: str = "test", db: str = None):
    """Return a list of dicts: id, db, difficulty, question, meaning, gold_sql."""
    out = []
    for name, mod in MODULES.items():
        if db and name != db:
            continue
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
        for qid, diff, q, meaning, sql in getattr(m, split.upper()):
            out.append({"id": qid, "db": name, "difficulty": diff, "question": q, "meaning": meaning,
                        "gold_sql": sql})
    return out


def gold_rows(q: dict):
    with psycopg.connect(config.DSNS[q["db"]]) as con:
        con.read_only = True
        return con.execute(q["gold_sql"]).fetchall()
