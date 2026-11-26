"""Result comparison against the gold result.

A predicted result is correct when it contains the same rows as the gold result:
- values are normalised (numbers rounded: whole numbers from 1,000 upward, otherwise 2 decimals;
  dates and text as strings; None kept);
- column names are ignored; the answer must contain every gold column, with the same values on the same rows;
- EXTRA columns are tolerated (a question that says "which customers" can reasonably be answered with more than the
  name), but a missing or wrong column is not;
- row order is ignored, so a 'top N' answer is judged on which rows it returns, not their order.
"""
from decimal import Decimal
from itertools import combinations
import datetime as dt


def _norm(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float, Decimal)):
        f = float(v)
        # float4 columns (e.g. Northwind prices) drift in the last digits depending on how a query sums them,
        # so large values are compared at whole-number precision and small ones at 2 decimals
        return round(f) if abs(f) >= 1000 else round(f, 2)
    if isinstance(v, dt.datetime):
        # a timestamp at exactly midnight is the same calendar day as a date (e.g. date_trunc without ::date)
        return v.date().isoformat() if v.time() == dt.time(0) else v.isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    return str(v).strip()


def _key(row):
    return tuple((-1, "") if v is None else (0, v) if isinstance(v, float) else (1, str(v)) for v in row)


def normalise(rows, ordered: bool):
    out = [tuple(_norm(v) for v in r) for r in rows]
    return out if ordered else sorted(out, key=_key)


def _column(rows, j):
    return sorted((_key((r[j],)) for r in rows))


def is_correct(pred_rows, gold_rows, gold_sql: str) -> bool:
    if pred_rows is None:
        return False
    pred = normalise(pred_rows, ordered=False)
    gold = normalise(gold_rows, ordered=False)
    if pred == gold:
        return True
    if not gold or len(pred) != len(gold):
        return False
    n_gold, n_pred = len(gold[0]), len(pred[0]) if pred else 0
    if n_pred <= n_gold or n_pred > 12:                    # only the "extra columns" case is tolerated
        return False
    # for each gold column, the predicted columns that hold exactly the same values
    cands = [[j for j in range(n_pred) if _column(pred, j) == _column(gold, i)] for i in range(n_gold)]
    if any(not c for c in cands):
        return False
    for pick in combinations(range(n_pred), n_gold):        # keeps the gold column order
        if all(pick[i] in cands[i] for i in range(n_gold)):
            projected = sorted((tuple(r[j] for j in pick) for r in pred), key=_key)
            if projected == gold:
                return True
    return False