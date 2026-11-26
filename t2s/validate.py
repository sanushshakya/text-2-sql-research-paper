"""Rule-based SQL validation (step 2 of the enhanced system) and read-only execution (step 3)."""
import re
from dataclasses import dataclass

import psycopg
import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.qualify import qualify

from . import config

SCHEMA_SQLSTATES = {"42P01", "42703", "42883"}   # undefined table, column, function


@dataclass
class Check:
    ok: bool
    kind: str = ""      # "syntax", "schema", "explain" when not ok
    message: str = ""


def clean_sql(text: str) -> str:
    """Strip markdown fences and trailing semicolons from model output."""
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.S | re.I)
    sql = (m.group(1) if m else text).strip()
    return sql.rstrip(";").strip()


def validate(sql: str, schema: dict, dsn: str) -> Check:
    # 1. one SELECT statement that parses as PostgreSQL
    try:
        parsed = sqlglot.parse(sql, dialect="postgres")
    except SqlglotError as e:
        return Check(False, "syntax", f"SQL does not parse as PostgreSQL: {str(e)[:300]}")
    parsed = [p for p in parsed if p is not None]
    if len(parsed) != 1:
        return Check(False, "syntax", "Output must be exactly one SQL statement.")
    tree = parsed[0]
    if not isinstance(tree, (exp.Select, exp.Union, exp.Subquery)):
        return Check(False, "syntax", "Only SELECT statements are allowed.")
    # 2. every table and column exists
    try:
        qualify(tree.copy(), schema=schema, dialect="postgres", validate_qualify_columns=True,
                identify=False, quote_identifiers=False)
    except SqlglotError as e:
        return Check(False, "schema", f"Unknown table or column: {str(e)[:300]}")
    # 3. PostgreSQL's planner accepts it
    try:
        with psycopg.connect(dsn) as con:
            con.read_only = True
            con.execute("EXPLAIN " + sql)
    except psycopg.Error as e:
        kind = "schema" if getattr(e, "sqlstate", "") in SCHEMA_SQLSTATES else "explain"
        return Check(False, kind, f"PostgreSQL rejected the query: {str(e).splitlines()[0][:300]}")
    return Check(True)


@dataclass
class ExecResult:
    ok: bool
    rows: list = None
    error_kind: str = ""     # "schema" or "execution"
    message: str = ""


def execute_readonly(sql: str, dsn: str) -> ExecResult:
    """Run the query in a read-only transaction with a time limit."""
    try:
        with psycopg.connect(dsn) as con:
            con.read_only = True
            con.execute(f"SET statement_timeout = {config.STATEMENT_TIMEOUT_MS}")
            cur = con.execute(sql)
            rows = cur.fetchmany(config.MAX_ROWS) if cur.description else []
        return ExecResult(True, rows=rows)
    except psycopg.Error as e:
        kind = "schema" if getattr(e, "sqlstate", "") in SCHEMA_SQLSTATES else "execution"
        return ExecResult(False, error_kind=kind, message=str(e).splitlines()[0][:300])
