# Corpus parse health

Written by `python -m spacestd.health` (A1/A2 in docs/PUBLIC_RELEASE_PLAN.md). Text-free: counts, IDs
and scores only. A document is `checked` when it meets every threshold; `verified` documents are
hand-checked (tests/test_real_documents.py) and keep that tier.

- Corpus: `loaded`; 44 documents: 26 verified, 17 checked, 1 unchecked
- Parse errors: 0; parse time 0 s
- Thresholds: at least 20 records for a standard (3 for other types), valid IDs ≥ 95%, unparsed ≤ 10% (not for ECSS standards), coverage ≥ 75% (words in records and unparsed fragments / body words), ragged tables ≤ 10% or ≤ 1, file name names the same base number (or no standard, or a sidecar sets the identity); adoption notices are listed, not judged
- Parser version: `317693dd1109`

Why documents are not `checked`:

- 2 × ragged tables N

| Document | Issue | Tier | Records | Kinds (req/rec/perm/guid/del) | Valid IDs | Dup | Unparsed | Coverage | Tables (ragged) | Name ID | Time s | Reasons |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| ECSS-E-HB-32-20 Part 1A |  | checked | 495 | 0/0/0/495/0 | 100% | 0 | 0 | 84% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 2A |  | checked | 684 | 0/0/0/684/0 | 100% | 0 | 0 | 84% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 3A |  | checked | 619 | 0/0/0/619/0 | 100% | 1 | 0 | 88% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 4A |  | checked | 775 | 0/0/0/775/0 | 100% | 0 | 0 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 5A |  | checked | 631 | 0/0/0/631/0 | 100% | 0 | 0 | 90% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 6A |  | checked | 700 | 0/0/0/700/0 | 100% | 0 | 0 | 93% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 7A |  | checked | 758 | 0/0/0/758/0 | 100% | 0 | 0 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-20 Part 8A |  | checked | 1645 | 0/0/0/1645/0 | 100% | 3 | 0 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-21A |  | checked | 838 | 0/0/0/838/0 | 100% | 0 | 0 | 89% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-32-22A |  | unchecked | 487 | 0/0/0/487/0 | 100% | 0 | 0 | 87% | 27 (5) | match | 0.0 | ragged tables 5/27 |
| ECSS-E-HB-32-23A | Rev.1 | checked | 346 | 0/0/0/346/0 | 100% | 0 | 0 | 85% | 24 (1) | match | 0.0 |  |
| ECSS-E-HB-32-24A |  | checked | 697 | 0/0/0/697/0 | 100% | 0 | 0 | 89% | 30 (1) | match | 0.0 |  |
| ECSS-E-HB-32-25A |  | checked | 522 | 0/0/0/522/0 | 100% | 0 | 0 | 88% | 46 (1) | match | 0.0 |  |
| ECSS-E-HB-32-26A |  | checked | 506 | 0/0/0/506/0 | 96% | 16 | 0 | 92% | 38 (0) | match | 0.0 |  |
| ECSS-E-ST-10-03C | Rev.1 | verified | 469 | 431/8/7/10/13 | 100% | 0 | 282 | 88% | 14 (1) | match | 0.0 |  |
| ECSS-E-ST-32-01C | Rev.2 | verified | 332 | 243/1/22/0/66 | 100% | 0 | 48 | 85% | 1 (0) | match | 0.0 |  |
| ECSS-E-ST-32-02C | Rev.1 | verified | 418 | 384/0/32/2/0 | 100% | 0 | 39 | 90% | 10 (0) | match | 0.0 |  |
| ECSS-E-ST-32-03C |  | verified | 45 | 43/2/0/0/0 | 100% | 0 | 8 | 87% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-32-08C | Rev.1 | verified | 77 | 74/1/0/0/2 | 100% | 0 | 20 | 87% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-32-10C | Rev.2 Corr.1 | verified | 28 | 28/0/0/0/0 | 100% | 0 | 16 | 78% | 6 (0) | match | 0.0 |  |
| ECSS-E-ST-32-11C |  | verified | 128 | 119/9/0/0/0 | 100% | 0 | 121 | 90% | 5 (0) | match | 0.0 |  |
| ECSS-E-ST-32C | Rev.1 | verified | 750 | 714/26/9/1/0 | 100% | 1 | 193 | 86% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-33-01C | Rev.2 | verified | 451 | 406/24/2/0/19 | 100% | 0 | 45 | 87% | 7 (0) | match | 0.0 |  |
| ECSS-Q-ST-70C | Rev.2 | verified | 281 | 241/5/3/24/8 | 100% | 0 | 54 | 85% | 2 (0) | match | 0.0 |  |
| NASA-HDBK-5010 Vol 1 | Rev.A | checked | 743 | 303/0/0/440/0 | 95% | 34 | 0 | 98% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-5010 Vol 2 | Rev.A | checked | 244 | 8/0/0/236/0 | 100% | 0 | 0 | 91% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-5026 |  | checked | 78 | 12/0/0/66/0 | 97% | 2 | 0 | 97% | 7 (1) | match | 0.0 |  |
| NASA-HDBK-7005 |  | checked | 261 | 0/0/0/261/0 | 100% | 0 | 0 | 99% | 0 (0) | match | 0.0 |  |
| NASA-SPEC-5022 | w/Change 2 | verified | 109 | 79/0/0/30/0 | 100% | 0 | 3 | 89% | 0 (0) | match | 0.0 |  |
| NASA-STD-5001B | w/Change 3 | verified | 117 | 61/0/0/56/0 | 100% | 0 | 1 | 91% | 7 (0) | match | 0.0 |  |
| NASA-STD-5002B |  | verified | 148 | 67/0/0/80/1 | 100% | 0 | 0 | 94% | 1 (0) | match | 0.0 |  |
| NASA-STD-5005D | w/Change 2 | verified | 414 | 251/0/0/163/0 | 100% | 0 | 3 | 94% | 0 (0) | match | 0.0 |  |
| NASA-STD-5006A | w/Change 2 | verified | 176 | 138/0/0/38/0 | 100% | 0 | 0 | 85% | 0 (0) | match | 0.0 |  |
| NASA-STD-5008B | w/Change 2 | verified | 366 | 319/0/0/47/0 | 100% | 0 | 1 | 87% | 1 (0) | match | 0.0 |  |
| NASA-STD-5009C |  | verified | 122 | 74/0/0/48/0 | 100% | 0 | 4 | 91% | 3 (0) | match | 0.0 |  |
| NASA-STD-5012C |  | verified | 55 | 28/0/0/27/0 | 100% | 0 | 1 | 96% | 2 (0) | match | 0.0 |  |
| NASA-STD-5017B |  | verified | 188 | 90/0/0/98/0 | 100% | 0 | 4 | 97% | 8 (0) | match | 0.0 |  |
| NASA-STD-5018 | w/Change 1 | verified | 283 | 234/0/0/49/0 | 100% | 0 | 7 | 87% | 1 (0) | match | 0.0 |  |
| NASA-STD-5019A | w/Change 4 | verified | 498 | 245/0/0/253/0 | 100% | 0 | 0 | 97% | 8 (3) | match | 0.0 | ragged tables 3/8 |
| NASA-STD-5020B |  | verified | 200 | 32/0/0/168/0 | 100% | 0 | 19 | 97% | 7 (0) | match | 0.0 |  |
| NASA-STD-5023 |  | verified | 293 | 105/0/0/188/0 | 100% | 0 | 1 | 96% | 4 (0) | match | 0.0 |  |
| NASA-STD-7001C |  | verified | 142 | 64/0/0/78/0 | 100% | 0 | 5 | 94% | 3 (0) | match | 0.0 |  |
| NASA-STD-7002B | w/Change 1 | verified | 102 | 63/0/0/39/0 | 100% | 0 | 0 | 89% | 3 (0) | match | 0.0 |  |
| NASA-STD-7003A |  | verified | 68 | 26/0/0/42/0 | 100% | 0 | 3 | 98% | 2 (0) | match | 0.0 |  |
