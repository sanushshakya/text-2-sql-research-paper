"""Schema introspection, the raw schema text (baseline A) and keyword schema selection (B and C)."""
import json
import re
from pathlib import Path

import psycopg

from . import config

DESC_DIR = Path(__file__).resolve().parent.parent / "descriptions"


def introspect(db: str) -> dict:
    """Return {'tables': {t: {'columns': [(name, type)], 'pk': [..]}}, 'fks': [(t, col, ref_t, ref_col)]}."""
    with psycopg.connect(config.DSNS[db]) as con:
        cur = con.cursor()
        cur.execute("""select table_name, column_name, data_type from information_schema.columns
                       where table_schema='public' order by table_name, ordinal_position""")
        tables = {}
        for t, c, ty in cur.fetchall():
            tables.setdefault(t, {"columns": [], "pk": []})["columns"].append((c, ty))
        cur.execute("""select tc.table_name, kcu.column_name from information_schema.table_constraints tc
                       join information_schema.key_column_usage kcu using (constraint_name, table_schema)
                       where tc.table_schema='public' and tc.constraint_type='PRIMARY KEY'
                       order by tc.table_name, kcu.ordinal_position""")
        for t, c in cur.fetchall():
            tables[t]["pk"].append(c)
        cur.execute("""select cl.relname, a.attname, cf.relname, af.attname
                       from pg_constraint k
                       join pg_class cl on cl.oid = k.conrelid
                       join pg_class cf on cf.oid = k.confrelid
                       join pg_namespace n on n.oid = cl.relnamespace and n.nspname = 'public'
                       cross join lateral unnest(k.conkey, k.confkey) as u(ck, fk)
                       join pg_attribute a on a.attrelid = k.conrelid and a.attnum = u.ck
                       join pg_attribute af on af.attrelid = k.confrelid and af.attnum = u.fk
                       where k.contype = 'f'""")
        fks = [tuple(r) for r in cur.fetchall()]
    return {"tables": tables, "fks": fks}


def sqlglot_schema(info: dict) -> dict:
    """{table: {column: type}} for sqlglot's qualifier."""
    return {t: {c: ty for c, ty in d["columns"]} for t, d in info["tables"].items()}


def raw_schema_text(info: dict, tables=None) -> str:
    """Names only: table(column, column, ...). This is all the baseline (A) gets."""
    names = tables or sorted(info["tables"])
    return "\n".join(f"{t}({', '.join(c for c, _ in info['tables'][t]['columns'])})" for t in names)


def load_descriptions(db: str) -> dict:
    return json.loads((DESC_DIR / f"{db}.json").read_text())["tables"]


def _tokens(text: str) -> set:
    words = re.findall(r"[a-z]+", text.lower())
    return {_stem(w) for w in words if len(w) > 2}


def _stem(w: str) -> str:
    for suf in ("ing", "ers", "ies", "es", "ed", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


STOP = _tokens("what which who whom how many much the and for with per each all any from that this are was were "
               "has have had show list give tell find get number total average top most least more less than "
               "between during before after into over under about their there them")


def select_tables(question: str, info: dict, descriptions: dict, k: int = None) -> list:
    """Rule-based schema selection: rank tables by keyword overlap with name, description and columns,
    keep the top k, then add tables needed to connect them through foreign keys."""
    k = k or config.TOP_K_TABLES
    q = _tokens(question) - STOP
    scores = {}
    for t, d in info["tables"].items():
        desc = descriptions.get(t, {})
        name_tok = _tokens(t.replace("_", " "))
        desc_tok = _tokens(desc.get("description", ""))
        col_tok = set()
        for c, _ in d["columns"]:
            col_tok |= _tokens(c.replace("_", " "))
        for cdesc in desc.get("columns", {}).values():
            desc_tok |= _tokens(cdesc)
        s = 3 * len(q & name_tok) + 2 * len(q & desc_tok) + 1 * len(q & col_tok)
        scores[t] = s
    ranked = [t for t, s in sorted(scores.items(), key=lambda x: (-x[1], x[0])) if s > 0][:k]
    chosen = set(ranked)
    # join-path expansion: add a bridging table when two chosen tables are linked through one other table
    adj = {}
    for t, _, rt, _ in info["fks"]:
        adj.setdefault(t, set()).add(rt)
        adj.setdefault(rt, set()).add(t)
    for a in list(chosen):
        for b in list(chosen):
            if a < b and b not in adj.get(a, set()):
                for mid in adj.get(a, set()) & adj.get(b, set()):
                    chosen.add(mid)
    return sorted(chosen) if chosen else sorted(info["tables"])


def schema_context(tables: list, info: dict, descriptions: dict) -> str:
    """Selected tables with descriptions, columns and the foreign keys between them (used by B and C)."""
    lines = []
    for t in tables:
        d = info["tables"][t]
        desc = descriptions.get(t, {})
        cdesc = desc.get("columns", {})
        cols = ", ".join(f"{c} ({ty}{'; ' + cdesc[c] if c in cdesc else ''})" for c, ty in d["columns"])
        lines.append(f"Table {t}: {desc.get('description', '')}\n  Columns: {cols}")
        if d["pk"]:
            lines.append(f"  Primary key: {', '.join(d['pk'])}")
    fk_lines = [f"{t}.{c} -> {rt}.{rc}" for t, c, rt, rc in info["fks"] if t in tables and rt in tables]
    if fk_lines:
        lines.append("Foreign keys:\n  " + "\n  ".join(fk_lines))
    return "\n".join(lines)
