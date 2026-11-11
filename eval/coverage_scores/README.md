# Coverage eval scores

One file per kept commit of round 11, written by `python eval/run_coverage_eval.py --docs documents --save <file>`.

The totals are not all over the same questions. Up to `06`, the set had 69 questions and x-07 / x-08 were
"not covered" questions (no NPR was loaded). From `07`, both are lookups in the loaded NPRs and x-11 was added
(70 questions). On the 67 questions whose task never changed:

| File | Total as saved | Same 67 questions |
| --- | ---: | ---: |
| `baseline` | 51.1 (69) | 49.6 |
| `01-revision-guard` | 68.4 (69) | 67.5 |
| `02-all-branches-loaded` | 84.5 (69) | 84.0 |
| `03-coverage-signals` | 87.4 (69) | 87.0 |
| `04-lookup-help` | 88.4 (69) | 88.0 |
| `05-find-standards` | 88.4 (69) | 88.0 |
| `06-parser-npr-ranking` | 88.0 (69) | 90.6 |
| `07-npr-questions`, `08-final` | 90.5 (70) | 90.6 |
| `09-review-fixes` | 90.5 (70) | 90.6 |

From `09` the scorer is stricter (review of PR 106): a lookup with an expected page needs a page on the record,
and a clause is matched by itself or its lettered items, not by its subclauses. The final corpus scores the same
under both rules; the earlier files were written with the earlier rule and were not re-scored.
