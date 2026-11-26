## Result correctness (majority of runs)

| Configuration | Correct | Total | Accuracy |
|---|---|---|---|
| A | 62 | 100 | 62.0% |
| B | 73 | 100 | 73.0% |
| C | 73 | 100 | 73.0% |

## Accuracy by database

| Configuration | northwind | shopdb |
|---|---|---|
| A | 35/50 | 27/50 |
| B | 37/50 | 36/50 |
| C | 37/50 | 36/50 |

## Accuracy by difficulty

| Configuration | complex | easy | medium |
|---|---|---|---|
| A | 7/30 | 25/30 | 30/40 |
| B | 9/30 | 30/30 | 34/40 |
| C | 9/30 | 30/30 | 34/40 |

## Questions fixed and broken (question by question)

| Comparison | Fixed (first wrong, second right) | Broken (first right, second wrong) | Net |
|---|---|---|---|
| A -> C | 17 | 6 | +11 |
| A -> B | 17 | 6 | +11 |
| B -> C | 0 | 0 | +0 |

## Errors by type (all runs)

| Configuration | Syntax | Schema | EXPLAIN | Execution | Semantic (ran, wrong) | Rejected after retry | Runs |
|---|---|---|---|---|---|---|---|
| A | 0 | 6 | 0 | 3 | 29 | 0 | 100 |
| B | 0 | 9 | 0 | 0 | 18 | 0 | 100 |
| C | 0 | 9 | 0 | 0 | 18 | 9 | 100 |

## Execution success, latency and LLM calls (all runs)

| Configuration | Executed OK | Median latency (s) | Min-max (s) | Mean LLM calls | Retried |
|---|---|---|---|---|---|
| A | 91.0% | 9.24 | 2.60-41.37 | 1.00 | 0 |
| B | 91.0% | 11.24 | 3.00-41.20 | 1.00 | 0 |
| C | 91.0% | 13.31 | 3.31-41.53 | 1.09 | 9 |

## Run-to-run stability

| Configuration | Questions whose runs all agree | Questions |
|---|---|---|
| A | 100 | 100 |
| B | 100 | 100 |
| C | 100 | 100 |
