"""The three configurations.

A  baseline : question + raw table/column names -> LLM -> execute
B  schema   : A + keyword schema selection with descriptions and foreign keys (no validation, no retry)
C  enhanced : B + validation (parse, schema check, EXPLAIN) + read-only execution check + one retry
"""
import time
from dataclasses import asdict, dataclass, field

from . import config, prompts, schema
from .validate import clean_sql, execute_readonly, validate


@dataclass
class Record:
    qid: str
    db: str
    config: str
    run: int
    sql: str = ""
    rows: list = None
    status: str = ""            # "ok", "error" or "rejected"
    error_kind: str = ""        # syntax / schema / explain / execution
    error_message: str = ""
    n_llm_calls: int = 0
    retried: bool = False
    latency_s: float = 0.0
    llm_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    selected_tables: list = field(default_factory=list)
    attempts: list = field(default_factory=list)

    def to_json(self):
        d = asdict(self)
        d["rows"] = [[str(v) for v in r] for r in (self.rows or [])]
        return d


class Pipeline:
    def __init__(self, db: str, llm):
        self.db = db
        self.llm = llm
        self.dsn = config.DSNS[db]
        self.info = schema.introspect(db)
        self.sg_schema = schema.sqlglot_schema(self.info)
        self.descriptions = schema.load_descriptions(db)

    def _ask(self, rec: Record, user: str) -> str:
        reply = self.llm.complete(prompts.SYSTEM, user)
        rec.n_llm_calls += 1
        rec.llm_seconds += reply.seconds
        rec.input_tokens += reply.input_tokens
        rec.output_tokens += reply.output_tokens
        return clean_sql(reply.text)

    def run(self, cfg: str, qid: str, question: str, run: int = 1) -> Record:
        assert cfg in ("A", "B", "C")
        rec = Record(qid=qid, db=self.db, config=cfg, run=run)
        t0 = time.perf_counter()
        if cfg == "A":
            user = prompts.baseline_prompt(question, schema.raw_schema_text(self.info))
        else:
            tables = schema.select_tables(question, self.info, self.descriptions)
            rec.selected_tables = tables
            user = prompts.schema_prompt(question, schema.schema_context(tables, self.info, self.descriptions))

        sql = self._ask(rec, user)
        if cfg == "C":
            sql = self._validated_with_retry(rec, user, sql)
        else:
            self._execute(rec, sql)
        rec.latency_s = time.perf_counter() - t0
        return rec

    # -- helpers ---------------------------------------------------------------------------
    def _execute(self, rec: Record, sql: str):
        rec.sql = sql
        res = execute_readonly(sql, self.dsn)
        rec.attempts.append({"sql": sql, "ok": res.ok, "kind": res.error_kind, "message": res.message})
        if res.ok:
            rec.status, rec.rows = "ok", res.rows
        else:
            rec.status, rec.error_kind, rec.error_message = "error", res.error_kind, res.message
        return res.ok

    def _validated_with_retry(self, rec: Record, user: str, sql: str) -> str:
        for attempt in (1, 2):
            rec.sql = sql
            chk = validate(sql, self.sg_schema, self.dsn)
            if chk.ok:
                res = execute_readonly(sql, self.dsn)
                rec.attempts.append({"sql": sql, "ok": res.ok, "kind": res.error_kind, "message": res.message})
                if res.ok:
                    rec.status, rec.rows, rec.error_kind, rec.error_message = "ok", res.rows, "", ""
                    return sql
                kind, msg = res.error_kind, res.message
            else:
                kind, msg = chk.kind, chk.message
                rec.attempts.append({"sql": sql, "ok": False, "kind": kind, "message": msg})
            rec.error_kind, rec.error_message = kind, msg
            if attempt == 1:
                rec.retried = True
                sql = self._ask(rec, prompts.retry_prompt(user, sql, msg))
        rec.status = "rejected"
        return sql
