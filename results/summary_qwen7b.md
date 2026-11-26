## Result correctness (majority of runs)

| Configuration | Correct | Total | Accuracy |
|---|---|---|---|
| A | 59 | 100 | 59.0% |
| B | 72 | 100 | 72.0% |
| C | 72 | 100 | 72.0% |

## Accuracy by database

| Configuration | northwind | shopdb |
|---|---|---|
| A | 35/50 | 24/50 |
| B | 34/50 | 38/50 |
| C | 34/50 | 38/50 |

## Accuracy by difficulty

| Configuration | complex | easy | medium |
|---|---|---|---|
| A | 8/30 | 26/30 | 25/40 |
| B | 10/30 | 29/30 | 33/40 |
| C | 10/30 | 29/30 | 33/40 |

## Questions fixed and broken (question by question)

| Comparison | Fixed (first wrong, second right) | Broken (first right, second wrong) | Net |
|---|---|---|---|
| A -> C | 19 | 6 | +13 |
| A -> B | 19 | 6 | +13 |
| B -> C | 0 | 0 | +0 |

## Errors by type (all runs)

| Configuration | Syntax | Schema | EXPLAIN | Execution | Semantic (ran, wrong) | Rejected after retry | Runs |
|---|---|---|---|---|---|---|---|
| A | 0 | 15 | 0 | 6 | 102 | 0 | 300 |
| B | 0 | 18 | 0 | 3 | 63 | 0 | 300 |
| C | 0 | 18 | 0 | 0 | 66 | 18 | 300 |

## Execution success, latency and LLM calls (all runs)

| Configuration | Executed OK | Median latency (s) | Min-max (s) | Mean LLM calls | Retried |
|---|---|---|---|---|---|
| A | 93.0% | 3.81 | 0.66-18.26 | 1.00 | 0 |
| B | 93.0% | 4.53 | 0.71-28.18 | 1.00 | 0 |
| C | 94.0% | 5.13 | 0.75-26.53 | 1.07 | 21 |

## Run-to-run stability

| Configuration | Questions whose runs all agree | Questions |
|---|---|---|
| A | 100 | 100 |
| B | 100 | 100 |
| C | 100 | 100 |
