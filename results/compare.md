## Result correctness, 100 questions (correct in the majority of runs)

| Model | A | B | C |
|---|---|---|---|
| qwen7b | 59/100 (59%) | 73/100 (73%) | 73/100 (73%) |
| qwen14b | 62/100 (62%) | 73/100 (73%) | 73/100 (73%) |

## Accuracy by database

| Model | Configuration | northwind | shopdb |
|---|---|---|---|
| qwen7b | A | 35/50 | 24/50 |
| qwen7b | B | 34/50 | 39/50 |
| qwen7b | C | 34/50 | 39/50 |
| qwen14b | A | 35/50 | 27/50 |
| qwen14b | B | 37/50 | 36/50 |
| qwen14b | C | 37/50 | 36/50 |

## Accuracy by difficulty

| Model | Configuration | complex | easy | medium |
|---|---|---|---|---|
| qwen7b | A | 8/30 | 26/30 | 25/40 |
| qwen7b | B | 11/30 | 29/30 | 33/40 |
| qwen7b | C | 11/30 | 29/30 | 33/40 |
| qwen14b | A | 7/30 | 25/30 | 30/40 |
| qwen14b | B | 9/30 | 30/30 | 34/40 |
| qwen14b | C | 9/30 | 30/30 | 34/40 |

## Questions fixed and broken (question by question)

| Model | Comparison | Fixed (first wrong, second right) | Broken (first right, second wrong) | Net |
|---|---|---|---|---|
| qwen7b | A -> B | 20 | 6 | +14 |
| qwen7b | A -> C | 20 | 6 | +14 |
| qwen7b | B -> C | 0 | 0 | +0 |
| qwen14b | A -> B | 17 | 6 | +11 |
| qwen14b | A -> C | 17 | 6 | +11 |
| qwen14b | B -> C | 0 | 0 | +0 |

## Errors by type (all runs)

| Model | Config | Syntax | Schema | EXPLAIN | Execution | Semantic (ran, wrong) | Rejected after retry | Runs |
|---|---|---|---|---|---|---|---|---|
| qwen7b | A | 0 | 15 | 0 | 6 | 102 | 0 | 300 |
| qwen7b | B | 0 | 18 | 0 | 3 | 60 | 0 | 300 |
| qwen7b | C | 0 | 18 | 0 | 0 | 63 | 18 | 300 |
| qwen14b | A | 0 | 6 | 0 | 3 | 29 | 0 | 100 |
| qwen14b | B | 0 | 9 | 0 | 0 | 18 | 0 | 100 |
| qwen14b | C | 0 | 9 | 0 | 0 | 18 | 9 | 100 |

## Latency and LLM calls (all runs; local-model latency depends on the hardware used)

| Model | Config | Median latency (s) | Min-max (s) | Mean LLM calls | Retried |
|---|---|---|---|---|---|
| qwen7b | A | 3.81 | 0.66-18.26 | 1.00 | 0 |
| qwen7b | B | 4.53 | 0.71-28.18 | 1.00 | 0 |
| qwen7b | C | 5.13 | 0.75-26.53 | 1.07 | 21 |
| qwen14b | A | 9.24 | 2.60-41.37 | 1.00 | 0 |
| qwen14b | B | 11.24 | 3.00-41.20 | 1.00 | 0 |
| qwen14b | C | 13.31 | 3.31-41.53 | 1.09 | 9 |

## Which model answers each question correctly (qwen7b vs qwen14b)

| Config | Both correct | Only qwen7b | Only qwen14b | Neither |
|---|---|---|---|---|
| A | 50 | 9 | 12 | 29 |
| B | 65 | 8 | 8 | 19 |
| C | 65 | 8 | 8 | 19 |

## Questions that no model or configuration answered correctly: 13

These are the first to check for a flawed question or gold query (results/gold_audit.csv). If a gold query is wrong, fix it openly, say so in the dissertation and re-score with rescore.py; do not drop questions quietly.

NW-C01, NW-C05, NW-C08, NW-C09, NW-C11, NW-C15, NW-M03, NW-M11, SH-C03, SH-C05, SH-C06, SH-C09, SH-C13
