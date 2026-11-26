"""Offline tests (no LLM, no API key). Run: python -m pytest -q tests   (needs the two databases)."""
import pytest

from t2s import config, evaluate, schema
from t2s.llm import ScriptedLLM
from t2s.pipeline import Pipeline
from t2s.validate import clean_sql, validate

GOOD = "SELECT count(*) FROM customers"
BAD_COL = "SELECT count(*) FROM customers WHERE nonexistent_col = 1"
BAD_TABLE = "SELECT * FROM clients"


@pytest.fixture(scope="module")
def shop_schema():
    return schema.sqlglot_schema(schema.introspect("shopdb"))


def test_clean_sql_strips_fences_and_semicolon():
    assert clean_sql("```sql\nSELECT 1;\n```") == "SELECT 1"


def test_validator_accepts_select(shop_schema):
    assert validate(GOOD, shop_schema, config.DSNS["shopdb"]).ok


@pytest.mark.parametrize("sql,kind", [
    ("SELECT 1; SELECT 2", "syntax"),
    ("DELETE FROM customers", "syntax"),
    (BAD_TABLE, "schema"),
    (BAD_COL, "schema"),
    ("SELEC count(*) FROM customers", "syntax"),
])
def test_validator_rejects(shop_schema, sql, kind):
    chk = validate(sql, shop_schema, config.DSNS["shopdb"])
    assert not chk.ok and chk.kind == kind


def test_C_retries_once_and_recovers():
    llm = ScriptedLLM([BAD_COL, GOOD])
    rec = Pipeline("shopdb", llm).run("C", "t1", "How many customers do we have?")
    assert rec.status == "ok" and rec.retried and rec.n_llm_calls == 2 and rec.rows == [(400,)]
    assert "nonexistent_col" in llm.calls[1][1]          # the retry prompt carries the error


def test_C_rejects_after_one_retry():
    rec = Pipeline("shopdb", ScriptedLLM([BAD_COL, BAD_TABLE])).run("C", "t2", "x")
    assert rec.status == "rejected" and rec.n_llm_calls == 2 and rec.error_kind == "schema"


def test_A_and_B_never_retry():
    for cfg in ("A", "B"):
        rec = Pipeline("shopdb", ScriptedLLM([BAD_COL, GOOD])).run(cfg, "t3", "How many customers?")
        assert rec.status == "error" and rec.n_llm_calls == 1 and not rec.retried and rec.error_kind == "schema"


def test_A_sees_names_only_but_C_sees_descriptions():
    llm_a, llm_c = ScriptedLLM([GOOD]), ScriptedLLM([GOOD])
    Pipeline("shopdb", llm_a).run("A", "t4", "How many customers do we have?")
    Pipeline("shopdb", llm_c).run("C", "t4", "How many customers do we have?")
    assert "Registered shoppers" not in llm_a.calls[0][1] and "reviews(" in llm_a.calls[0][1]
    assert "Registered shoppers" in llm_c.calls[0][1]
    assert "Table customers" in llm_c.calls[0][1]


def test_execution_is_read_only():
    rec = Pipeline("shopdb", ScriptedLLM(["WITH x AS (DELETE FROM reviews RETURNING 1) SELECT count(*) FROM x"])).run(
        "A", "t5", "x")
    assert rec.status == "error"
    assert Pipeline("shopdb", ScriptedLLM([GOOD])).run("A", "t6", "x").rows == [(400,)]


def test_evaluate_rules():
    gold = [("a", 1.0), ("b", 2.0)]
    assert evaluate.is_correct([("b", 2), ("a", 1)], gold, "")            # row order ignored
    assert not evaluate.is_correct([("a", 1), ("b", 3)], gold, "")        # wrong value
    assert not evaluate.is_correct([("a", 1)], gold, "")                  # missing row
    assert evaluate.is_correct([(1234567.4,)], [(1234567.1,)], "")        # large numbers: whole-number precision
    assert not evaluate.is_correct(None, gold, "")


def test_extra_columns_tolerated_but_wrong_or_missing_are_not():
    gold = [("Callahan", 19), ("King", 11)]
    assert evaluate.is_correct([(1, "Laura", "Callahan", 19), (2, "Robert", "King", 11)][:2], gold, "")      # extra columns
    assert evaluate.is_correct([(19, "Callahan", 1), (11, "King", 2)], gold, "") is False                     # gold column order kept
    assert not evaluate.is_correct([("Callahan", 19, 1), ("King", 12, 2)], gold, "")                          # wrong value
    assert not evaluate.is_correct([("Callahan", 1), ("King", 2)], gold, "")                                  # missing column
    assert not evaluate.is_correct([("Callahan", 19, "x")], gold, "")                                         # missing row


def test_selection_is_deterministic():
    info = schema.introspect("shopdb")
    d = schema.load_descriptions("shopdb")
    q = "How many returns were there for each product category?"
    assert schema.select_tables(q, info, d) == schema.select_tables(q, info, d)
