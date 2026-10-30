# ClimaQA audit

Dataset `Rose-STL-Lab/ClimaQA` at revision `3f084a0202c6260e588fb5b681d2e4ec859a3845`.

## Inventory

| split | rows | validation | complexity |
|---|---|---|---|
| gold/mcq | 292 | False 47, True 245 | BASE 141, HYPOTHETICAL 65, REASONING 86 |
| gold/cloze | 160 |  |  |
| gold/ffq | 181 | False 20, True 161 | BASE 61, HYPOTHETICAL 61, REASONING 59 |
| silver/mcq | 1000 |  | BASE 501, HYPOTHETICAL 235, REASONING 264 |
| silver/cloze | 1000 |  |  |
| silver/ffq | 1000 |  | BASE 507, HYPOTHETICAL 252, REASONING 241 |

## Paper check

| split | field | paper | released file | match |
|---|---|---|---|---|
| gold/mcq | validated_complexity | BASE 126, HYPOTHETICAL 47, REASONING 72 | BASE 126, HYPOTHETICAL 47, REASONING 72 | True |
| gold/ffq | validated_complexity | BASE 54, HYPOTHETICAL 55, REASONING 52 | BASE 54, HYPOTHETICAL 55, REASONING 52 | True |
| gold/cloze | rows | 160 | 160 | True |
| silver/mcq | complexity | BASE 501, HYPOTHETICAL 235, REASONING 264 | BASE 501, HYPOTHETICAL 235, REASONING 264 | True |
| silver/ffq | complexity | BASE 507, HYPOTHETICAL 252, REASONING 241 | BASE 507, HYPOTHETICAL 252, REASONING 241 | True |
| silver/cloze | rows | 1000 | 1000 | True |

## Findings

| check | kind | split | items | of which Validation=False |
|---|---|---|---|---|
| cloze.answer_in_question | flag | gold/cloze | 24 | 0 |
| cloze.answer_in_question | flag | silver/cloze | 25 | 0 |
| cloze.multiple_masks | flag | silver/cloze | 99 | 0 |
| dup.answer_differs | flag | silver/mcq | 16 | 0 |
| dup.question | flag | silver/cloze | 50 | 0 |
| dup.question | flag | silver/ffq | 61 | 0 |
| dup.question | flag | silver/mcq | 75 | 0 |
| leak.gold_in_other_silver_task | defect | gold/ffq | 4 | 0 |
| leak.gold_in_other_silver_task | defect | gold/mcq | 2 | 0 |
| leak.gold_in_silver | defect | gold/cloze | 9 | 0 |
| leak.gold_in_silver | defect | gold/ffq | 17 | 0 |
| leak.gold_in_silver | defect | gold/mcq | 17 | 0 |
| leak.near_match | flag | gold/cloze | 12 | 0 |
| leak.near_match | flag | gold/ffq | 8 | 2 |
| leak.near_match | flag | gold/mcq | 14 | 2 |
| mcq.all_or_none_of_above | flag | gold/mcq | 2 | 0 |
| mcq.all_or_none_of_above | flag | silver/mcq | 6 | 0 |
| mcq.answer_in_question | flag | gold/mcq | 5 | 3 |
| mcq.answer_in_question | flag | silver/mcq | 5 | 0 |
| mcq.duplicate_options | defect | gold/mcq | 1 | 0 |
| mcq.duplicate_options | defect | silver/mcq | 3 | 0 |

Leak counts are exact matches after case and whitespace folding, so they are a lower
bound; reworded copies appear as leak.near_match flags for a human to judge.
Item-level detail: findings.json. Hand-check sheets: review_sample.csv, leak_review.csv.
