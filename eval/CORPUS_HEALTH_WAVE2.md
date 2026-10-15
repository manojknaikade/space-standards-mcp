# Corpus parse health

Written by `python -m spacestd.health` (A1/A2 in docs/PUBLIC_RELEASE_PLAN.md). Text-free: counts, IDs
and scores only. A document is `checked` when it meets every threshold; `verified` documents are
hand-checked (tests/test_real_documents.py) and keep that tier.

- Corpus: `loaded`; 167 documents: 26 verified, 103 checked, 38 unchecked
- Parse errors: 0; parse time 0 s
- Thresholds: at least 20 records for a standard (3 for other types), valid IDs ≥ 95%, unparsed ≤ 10% (not for ECSS standards), coverage ≥ 75% (words in records and unparsed fragments / body words), ragged tables ≤ 10% or ≤ 1, file name names the same base number (or no standard, or a sidecar sets the identity); adoption notices are listed, not judged
- Parser version: `91167984535b`

Why documents are not `checked`:

- 14 × ragged tables N
- 11 × unparsed N > N
- 9 × valid IDs N < N
- 7 × adoption notice
- 6 × N records < N
- 3 × coverage N < N

| Document | Issue | Tier | Records | Kinds (req/rec/perm/guid/del) | Valid IDs | Dup | Unparsed | Coverage | Tables (ragged) | Name ID | Time s | Reasons |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| ECSS-E-AS-11C |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 6 | 87% | 2 (0) | match | 0.0 | adoption notice |
| ECSS-E-AS-50-21C | Rev.2 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 20 | 90% | 1 (0) | match | 0.0 | adoption notice |
| ECSS-E-AS-50-22C | Rev.1 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 12 | 88% | 1 (0) | match | 0.0 | adoption notice |
| ECSS-E-AS-50-23C | Rev.1 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 1 | 69% | 1 (0) | match | 0.0 | adoption notice |
| ECSS-E-AS-50-24C | Rev.1 | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 10 | 87% | 1 (0) | match | 0.0 | adoption notice |
| ECSS-E-AS-50-25C | Rev.1 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 7 | 85% | 1 (0) | match | 0.0 | adoption notice |
| ECSS-E-AS-50-26C |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 3 | 91% | 1 (0) | match | 0.0 | adoption notice |
| ECSS-E-HB-10-02A |  | unchecked | 294 | 0/0/0/294/0 | 78% | 64 | 0 | 94% | 3 (0) | match | 0.0 | valid IDs 78% < 95% |
| ECSS-E-HB-10-03A |  | checked | 400 | 0/0/0/400/0 | 98% | 9 | 0 | 95% | 7 (0) | match | 0.0 |  |
| ECSS-E-HB-10-12A |  | checked | 163 | 0/0/0/163/0 | 99% | 0 | 0 | 92% | 20 (0) | match | 0.0 |  |
| ECSS-E-HB-11A |  | checked | 60 | 0/0/0/60/0 | 100% | 0 | 0 | 93% | 6 (0) | match | 0.0 |  |
| ECSS-E-HB-20-01A |  | checked | 123 | 0/0/0/123/0 | 99% | 0 | 0 | 89% | 21 (0) | match | 0.0 |  |
| ECSS-E-HB-20-02A |  | checked | 46 | 0/0/0/46/0 | 100% | 0 | 0 | 93% | 3 (0) | match | 0.0 |  |
| ECSS-E-HB-20-05A |  | checked | 310 | 0/0/0/310/0 | 100% | 0 | 0 | 95% | 15 (0) | match | 0.0 |  |
| ECSS-E-HB-20-07A |  | checked | 236 | 0/0/0/236/0 | 97% | 6 | 0 | 83% | 8 (0) | match | 0.0 |  |
| ECSS-E-HB-20-20A |  | unchecked | 104 | 0/0/0/104/0 | 91% | 9 | 0 | 92% | 1 (0) | match | 0.0 | valid IDs 91% < 95% |
| ECSS-E-HB-20-40A |  | checked | 121 | 0/0/0/121/0 | 96% | 3 | 0 | 88% | 72 (0) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 10A |  | unchecked | 26 | 0/0/0/26/0 | 96% | 0 | 0 | 88% | 20 (3) | match | 0.0 | ragged tables 3/20 |
| ECSS-E-HB-31-01 Part 11A |  | checked | 72 | 0/0/0/72/0 | 100% | 0 | 0 | 89% | 13 (0) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 12A |  | checked | 47 | 0/0/0/47/0 | 98% | 0 | 0 | 76% | 18 (0) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 13A |  | unchecked | 209 | 0/0/0/209/0 | 100% | 0 | 0 | 83% | 82 (11) | match | 0.0 | ragged tables 11/82 |
| ECSS-E-HB-31-01 Part 14A |  | checked | 145 | 0/0/0/145/0 | 100% | 0 | 0 | 83% | 98 (5) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 15A |  | unchecked | 81 | 0/0/0/81/0 | 99% | 0 | 0 | 94% | 32 (5) | match | 0.0 | ragged tables 5/32 |
| ECSS-E-HB-31-01 Part 16A |  | checked | 20 | 0/0/0/20/0 | 100% | 0 | 0 | 90% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 1A |  | unchecked | 65 | 0/0/0/65/0 | 100% | 0 | 0 | 47% | 0 (0) | match | 0.0 | coverage 47% < 75% |
| ECSS-E-HB-31-01 Part 2A |  | checked | 7 | 0/0/0/7/0 | 100% | 0 | 0 | 85% | 0 (0) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 3A |  | unchecked | 36 | 0/0/0/36/0 | 100% | 0 | 0 | 31% | 2 (0) | match | 0.0 | coverage 31% < 75% |
| ECSS-E-HB-31-01 Part 4A |  | checked | 42 | 0/0/0/42/0 | 100% | 0 | 0 | 80% | 11 (0) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 5A |  | checked | 98 | 0/0/0/98/0 | 99% | 0 | 0 | 83% | 114 (6) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 6A |  | unchecked | 30 | 0/0/0/30/0 | 93% | 0 | 0 | 92% | 52 (6) | match | 0.0 | valid IDs 93% < 95%; ragged tables 6/52 |
| ECSS-E-HB-31-01 Part 7A |  | checked | 59 | 0/0/0/59/0 | 98% | 0 | 0 | 81% | 50 (1) | match | 0.0 |  |
| ECSS-E-HB-31-01 Part 8A |  | unchecked | 49 | 0/0/0/49/0 | 100% | 0 | 0 | 77% | 17 (2) | match | 0.0 | ragged tables 2/17 |
| ECSS-E-HB-31-01 Part 9A |  | checked | 29 | 0/0/0/29/0 | 97% | 0 | 0 | 85% | 11 (0) | match | 0.0 |  |
| ECSS-E-HB-31-03A |  | checked | 108 | 0/0/0/108/0 | 98% | 0 | 0 | 94% | 3 (0) | match | 0.0 |  |
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
| ECSS-E-HB-40-01A |  | unchecked | 148 | 0/0/0/148/0 | 99% | 2 | 0 | 96% | 16 (3) | match | 0.0 | ragged tables 3/16 |
| ECSS-E-HB-40A |  | unchecked | 1068 | 0/0/0/1068/0 | 78% | 237 | 0 | 96% | 5 (2) | match | 0.0 | valid IDs 78% < 95%; ragged tables 2/5 |
| ECSS-E-HB-50A |  | checked | 357 | 0/0/0/357/0 | 100% | 0 | 0 | 90% | 19 (0) | match | 0.0 |  |
| ECSS-E-HB-60-10A |  | unchecked | 245 | 0/0/0/245/0 | 100% | 0 | 0 | 88% | 13 (2) | match | 0.0 | ragged tables 2/13 |
| ECSS-E-HB-60A |  | checked | 48 | 0/0/0/48/0 | 100% | 0 | 0 | 92% | 6 (0) | match | 0.0 |  |
| ECSS-E-ST-10-02C | Rev.1 | checked | 192 | 171/1/1/0/19 | 100% | 0 | 76 | 86% | 3 (0) | match | 0.0 |  |
| ECSS-E-ST-10-03C | Rev.1 | verified | 469 | 431/8/7/10/13 | 100% | 0 | 282 | 88% | 14 (0) | match | 0.0 |  |
| ECSS-E-ST-10-04C | Rev.1 | checked | 140 | 105/4/17/1/13 | 100% | 0 | 1004 | 87% | 8 (0) | match | 0.0 |  |
| ECSS-E-ST-10-06C |  | checked | 54 | 48/6/0/0/0 | 100% | 0 | 78 | 91% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-10-09C |  | checked | 92 | 87/5/0/0/0 | 100% | 0 | 68 | 85% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-10-11C |  | checked | 197 | 196/0/0/1/0 | 100% | 0 | 114 | 92% | 1 (1) | match | 0.0 |  |
| ECSS-E-ST-10-12C | Corr.1 | checked | 149 | 142/0/6/1/0 | 100% | 0 | 110 | 91% | 13 (1) | match | 0.0 |  |
| ECSS-E-ST-10-24C | Rev.1 | checked | 289 | 118/1/5/165/0 | 100% | 0 | 170 | 90% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-10C | Rev.1 | checked | 378 | 345/2/2/10/19 | 97% | 12 | 129 | 88% | 2 (0) | match | 0.0 |  |
| ECSS-E-ST-20-01C |  | checked | 229 | 197/3/20/9/0 | 100% | 0 | 121 | 86% | 10 (1) | match | 0.0 |  |
| ECSS-E-ST-20-06C | Rev.1 | checked | 173 | 149/3/13/1/7 | 99% | 0 | 291 | 81% | 3 (0) | match | 0.0 |  |
| ECSS-E-ST-20-07C | Rev.2 | checked | 281 | 256/4/11/4/6 | 100% | 0 | 297 | 86% | 4 (0) | match | 0.0 |  |
| ECSS-E-ST-20-08C | Rev.2 | checked | 1238 | 1167/30/28/1/12 | 100% | 2 | 521 | 87% | 22 (2) | match | 0.0 |  |
| ECSS-E-ST-20-20C |  | checked | 130 | 116/10/0/4/0 | 97% | 0 | 6 | 77% | 4 (0) | match | 0.0 |  |
| ECSS-E-ST-20-21C |  | checked | 87 | 68/17/2/0/0 | 100% | 0 | 24 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-20-40C |  | checked | 312 | 302/0/0/10/0 | 100% | 0 | 195 | 84% | 2 (0) | match | 0.0 |  |
| ECSS-E-ST-20C | Rev.2 | checked | 472 | 409/23/4/4/32 | 96% | 17 | 237 | 90% | 6 (1) | match | 0.0 |  |
| ECSS-E-ST-31-02C | Rev.1 | checked | 180 | 169/1/0/0/10 | 100% | 0 | 61 | 87% | 8 (0) | match | 0.0 |  |
| ECSS-E-ST-31-04C |  | checked | 33 | 26/3/3/1/0 | 100% | 0 | 60 | 92% | 1 (0) | match | 0.0 |  |
| ECSS-E-ST-31C |  | checked | 235 | 233/0/1/1/0 | 100% | 0 | 40 | 87% | 1 (1) | match | 0.0 |  |
| ECSS-E-ST-32-01C | Rev.2 | verified | 332 | 243/1/22/0/66 | 100% | 0 | 48 | 85% | 1 (0) | match | 0.0 |  |
| ECSS-E-ST-32-02C | Rev.1 | verified | 418 | 384/0/32/2/0 | 100% | 0 | 39 | 90% | 10 (0) | match | 0.0 |  |
| ECSS-E-ST-32-03C |  | verified | 45 | 43/2/0/0/0 | 100% | 0 | 8 | 87% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-32-08C | Rev.1 | verified | 77 | 74/1/0/0/2 | 100% | 0 | 20 | 87% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-32-10C | Rev.2 Corr.1 | verified | 28 | 28/0/0/0/0 | 100% | 0 | 16 | 78% | 6 (0) | match | 0.0 |  |
| ECSS-E-ST-32-11C |  | verified | 128 | 119/9/0/0/0 | 100% | 0 | 121 | 90% | 5 (0) | match | 0.0 |  |
| ECSS-E-ST-32C | Rev.1 | verified | 750 | 714/26/9/1/0 | 100% | 1 | 193 | 86% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-33-01C | Rev.2 | verified | 451 | 406/24/2/0/19 | 100% | 0 | 45 | 87% | 7 (0) | match | 0.0 |  |
| ECSS-E-ST-33-11C | Rev.1 | checked | 406 | 367/9/5/0/25 | 100% | 0 | 32 | 86% | 25 (0) | match | 0.0 |  |
| ECSS-E-ST-34C |  | checked | 218 | 216/1/0/1/0 | 100% | 0 | 61 | 82% | 1 (0) | match | 0.0 |  |
| ECSS-E-ST-35-01C |  | checked | 349 | 335/12/1/1/0 | 100% | 0 | 16 | 89% | 1 (0) | match | 0.0 |  |
| ECSS-E-ST-35-02C |  | checked | 166 | 157/6/3/0/0 | 100% | 0 | 35 | 86% | 5 (0) | match | 0.0 |  |
| ECSS-E-ST-35-03C |  | checked | 322 | 320/0/1/1/0 | 100% | 0 | 160 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-35-06C | Rev.2 | checked | 374 | 355/13/6/0/0 | 100% | 0 | 18 | 87% | 4 (0) | match | 0.0 |  |
| ECSS-E-ST-35-10C |  | checked | 279 | 269/2/6/2/0 | 100% | 0 | 52 | 89% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-35C | Rev.1 | checked | 403 | 395/8/0/0/0 | 100% | 0 | 132 | 88% | 1 (0) | match | 0.0 |  |
| ECSS-E-ST-40-07C | Rev.1 | checked | 599 | 591/1/6/1/0 | 100% | 0 | 186 | 93% | 19 (0) | match | 0.0 |  |
| ECSS-E-ST-40-08C |  | checked | 255 | 208/0/42/5/0 | 100% | 0 | 169 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-40C | Rev.1 | unchecked | 788 | 731/37/14/6/0 | 93% | 59 | 554 | 85% | 0 (0) | match | 0.0 | valid IDs 93% < 95% |
| ECSS-E-ST-50-02C |  | checked | 99 | 81/6/4/8/0 | 100% | 0 | 56 | 87% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-50-05C | Rev.2 | checked | 254 | 221/24/4/5/0 | 98% | 0 | 56 | 80% | 17 (0) | match | 0.0 |  |
| ECSS-E-ST-50-11C |  | unchecked | 1157 | 1068/46/43/0/0 | 68% | 373 | 47 | 89% | 37 (1) | match | 0.0 | valid IDs 68% < 95% |
| ECSS-E-ST-50-12C | Rev.1 | checked | 531 | 482/38/11/0/0 | 100% | 0 | 70 | 88% | 11 (1) | match | 0.0 |  |
| ECSS-E-ST-50-13C |  | unchecked | 181 | 167/3/9/2/0 | 99% | 0 | 229 | 88% | 25 (5) | match | 0.0 | ragged tables 5/25 |
| ECSS-E-ST-50-14C |  | checked | 137 | 122/8/7/0/0 | 100% | 0 | 174 | 78% | 22 (0) | match | 0.0 |  |
| ECSS-E-ST-50-15C |  | checked | 237 | 221/9/7/0/0 | 100% | 0 | 110 | 84% | 23 (1) | match | 0.0 |  |
| ECSS-E-ST-50-16C |  | checked | 230 | 168/62/0/0/0 | 100% | 0 | 266 | 87% | 23 (2) | match | 0.0 |  |
| ECSS-E-ST-50-51C |  | unchecked | 14 | 12/0/2/0/0 | 100% | 0 | 7 | 86% | 1 (0) | match | 0.0 | 14 records < 20 |
| ECSS-E-ST-50-52C |  | checked | 381 | 291/60/9/21/0 | 100% | 0 | 399 | 81% | 10 (0) | match | 0.0 |  |
| ECSS-E-ST-50-53C |  | checked | 51 | 47/2/2/0/0 | 100% | 0 | 30 | 88% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-50C | Rev.2 | checked | 236 | 214/14/1/3/4 | 100% | 0 | 254 | 85% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-60-10C |  | checked | 39 | 35/4/0/0/0 | 100% | 0 | 105 | 86% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-60-20C | Rev.2 | checked | 204 | 179/6/3/12/4 | 100% | 0 | 148 | 89% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-60-21C |  | checked | 235 | 229/2/4/0/0 | 100% | 0 | 31 | 89% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-60-30C |  | checked | 141 | 139/2/0/0/0 | 100% | 0 | 87 | 92% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-70-01C |  | checked | 140 | 139/1/0/0/0 | 96% | 5 | 89 | 91% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-70-11C |  | checked | 348 | 330/17/1/0/0 | 100% | 0 | 89 | 94% | 3 (0) | match | 0.0 |  |
| ECSS-E-ST-70-31C |  | unchecked | 190 | 180/6/0/4/0 | 88% | 22 | 1026 | 72% | 118 (16) | match | 0.0 | valid IDs 88% < 95%; coverage 72% < 75%; ragged tables 16/118 |
| ECSS-E-ST-70-32C |  | checked | 78 | 28/4/12/34/0 | 100% | 0 | 913 | 88% | 0 (0) | match | 0.0 |  |
| ECSS-E-ST-70-41C |  | checked | 3197 | 3193/1/1/2/0 | 100% | 0 | 611 | 91% | 41 (0) | match | 0.0 |  |
| ECSS-E-ST-70C |  | checked | 359 | 347/3/8/1/0 | 99% | 4 | 145 | 85% | 34 (0) | match | 0.0 |  |
| ECSS-E-ST-80C |  | checked | 140 | 139/0/1/0/0 | 100% | 0 | 101 | 89% | 0 (0) | match | 0.0 |  |
| ECSS-Q-ST-70C | Rev.2 | verified | 281 | 241/5/3/24/8 | 100% | 0 | 54 | 85% | 2 (0) | match | 0.0 |  |
| NASA-HDBK-1004 |  | unchecked | 2 | 0/0/0/2/0 | 100% | 0 | 0 | 96% | 8 (1) | match | 0.0 | 2 records < 3 |
| NASA-HDBK-1005 |  | checked | 17 | 0/0/0/17/0 | 100% | 0 | 0 | 96% | 8 (0) | match | 0.0 |  |
| NASA-HDBK-1009A |  | checked | 42 | 0/0/0/42/0 | 100% | 0 | 0 | 75% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-2203 |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 1 | 100% | 0 (0) | match | 0.0 | 0 records < 3; unparsed 100% > 10% |
| NASA-HDBK-4001A |  | checked | 18 | 0/0/0/18/0 | 100% | 0 | 0 | 86% | 5 (1) | match | 0.0 |  |
| NASA-HDBK-4002B |  | checked | 141 | 0/0/0/141/0 | 100% | 0 | 0 | 93% | 16 (0) | match | 0.0 |  |
| NASA-HDBK-4006A |  | checked | 45 | 0/0/0/45/0 | 100% | 0 | 0 | 97% | 2 (0) | match | 0.0 |  |
| NASA-HDBK-4007A |  | unchecked | 25 | 0/0/0/25/0 | 0% | 0 | 626 | 95% | 15 (1) | match | 0.0 | valid IDs 0% < 95%; unparsed 96% > 10% |
| NASA-HDBK-4008 | w/Change 2 | unchecked | 140 | 0/0/0/140/0 | 100% | 0 | 0 | 97% | 7 (2) | none | 0.0 | ragged tables 2/7 |
| NASA-HDBK-4011 |  | checked | 14 | 0/0/0/14/0 | 100% | 0 | 0 | 100% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-5010 Vol 1 | Rev.A | checked | 743 | 303/0/0/440/0 | 95% | 34 | 0 | 98% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-5010 Vol 2 | Rev.A | checked | 244 | 8/0/0/236/0 | 100% | 0 | 0 | 91% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-5026 |  | checked | 78 | 12/0/0/66/0 | 97% | 2 | 0 | 97% | 7 (1) | match | 0.0 |  |
| NASA-HDBK-6007B | w/Change 1 | checked | 26 | 0/0/0/26/0 | 100% | 0 | 0 | 93% | 1 (0) | match | 0.0 |  |
| NASA-HDBK-6024 | w/Change 2 | checked | 93 | 0/0/0/93/0 | 100% | 0 | 0 | 91% | 27 (1) | match | 0.0 |  |
| NASA-HDBK-7005 |  | checked | 261 | 0/0/0/261/0 | 100% | 0 | 0 | 99% | 0 (0) | match | 0.0 |  |
| NASA-HDBK-7009B |  | checked | 135 | 1/0/0/134/0 | 100% | 0 | 0 | 95% | 39 (1) | match | 0.0 |  |
| NASA-HDBK-7010 |  | checked | 31 | 0/0/0/31/0 | 100% | 0 | 0 | 93% | 0 (0) | match | 0.0 |  |
| NASA-SPEC-5022 | w/Change 2 | verified | 109 | 79/0/0/30/0 | 100% | 0 | 3 | 89% | 0 (0) | match | 0.0 |  |
| NASA-STD-1006A |  | checked | 49 | 6/0/0/43/0 | 100% | 0 | 0 | 95% | 0 (0) | match | 0.0 |  |
| NASA-STD-1008 |  | unchecked | 326 | 15/0/0/311/0 | 100% | 0 | 43 | 96% | 5 (0) | match | 0.0 | unparsed 12% > 10% |
| NASA-STD-2818 |  | unchecked | 1 | 0/0/0/1/0 | 100% | 0 | 23 | 98% | 0 (0) | match | 0.0 | 1 records < 20; unparsed 96% > 10% |
| NASA-STD-2821 |  | unchecked | 18 | 17/0/0/1/0 | 100% | 0 | 28 | 98% | 0 (0) | match | 0.0 | 18 records < 20; unparsed 61% > 10% |
| NASA-STD-2822 |  | unchecked | 16 | 15/0/0/1/0 | 100% | 0 | 102 | 97% | 0 (0) | match | 0.0 | 16 records < 20; unparsed 86% > 10% |
| NASA-STD-3001 Vol 1 | Rev.C | unchecked | 53 | 53/0/0/0/0 | 9% | 31 | 137 | 96% | 0 (0) | match | 0.0 | valid IDs 9% < 95%; unparsed 72% > 10% |
| NASA-STD-3001 Vol 2 | Rev.F | unchecked | 667 | 296/0/0/371/0 | 100% | 0 | 228 | 94% | 0 (0) | match | 0.0 | unparsed 25% > 10% |
| NASA-STD-4003A | w/Change 1 | checked | 135 | 93/0/0/42/0 | 100% | 0 | 1 | 89% | 1 (0) | match | 0.0 |  |
| NASA-STD-4005A | w/Change 1 | checked | 81 | 14/0/0/67/0 | 100% | 0 | 0 | 95% | 0 (0) | match | 0.0 |  |
| NASA-STD-4010B |  | checked | 63 | 35/0/0/28/0 | 100% | 0 | 1 | 96% | 1 (1) | none | 0.0 |  |
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
| NASA-STD-6001B | w/Change 3 | checked | 324 | 207/0/0/117/0 | 100% | 0 | 7 | 90% | 6 (0) | match | 0.0 |  |
| NASA-STD-6012A |  | unchecked | 128 | 42/0/0/86/0 | 100% | 0 | 31 | 95% | 1 (0) | match | 0.0 | unparsed 19% > 10% |
| NASA-STD-6016C | w/Change 1 | checked | 428 | 207/0/0/221/0 | 100% | 0 | 3 | 94% | 0 (0) | match | 0.0 |  |
| NASA-STD-6030 |  | unchecked | 456 | 114/0/0/342/0 | 100% | 0 | 291 | 97% | 19 (2) | match | 0.0 | unparsed 39% > 10%; ragged tables 2/19 |
| NASA-STD-6033 |  | unchecked | 59 | 31/0/0/28/0 | 100% | 0 | 124 | 97% | 0 (0) | match | 0.0 | unparsed 68% > 10% |
| NASA-STD-7001C |  | verified | 142 | 64/0/0/78/0 | 100% | 0 | 5 | 94% | 3 (0) | match | 0.0 |  |
| NASA-STD-7002B | w/Change 1 | verified | 102 | 63/0/0/39/0 | 100% | 0 | 0 | 89% | 3 (0) | match | 0.0 |  |
| NASA-STD-7003A |  | verified | 69 | 26/0/0/43/0 | 100% | 0 | 2 | 98% | 2 (0) | match | 0.0 |  |
| NASA-STD-7009B |  | checked | 215 | 43/0/0/172/0 | 100% | 0 | 1 | 98% | 18 (1) | match | 0.0 |  |
| NASA-STD-7012A |  | checked | 89 | 39/0/0/50/0 | 100% | 0 | 1 | 97% | 4 (0) | match | 0.0 |  |
