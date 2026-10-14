# Corpus parse health

Written by `python -m spacestd.health` (A1/A2 in docs/PUBLIC_RELEASE_PLAN.md). Text-free: counts, IDs
and scores only. A document is `checked` when it meets every threshold; `verified` documents are
hand-checked (tests/test_real_documents.py) and keep that tier.

- Corpus: `all`; 285 documents: 26 verified, 166 checked, 93 unchecked
- Parse errors: 0; parse time 1585 s
- Thresholds: at least 20 records for a standard (3 for other types), valid IDs ≥ 95%, unparsed ≤ 10% (not for ECSS standards), coverage ≥ 75% (words in records and unparsed fragments / body words), ragged tables ≤ 10% or ≤ 1, file name names the same base number (or no standard, or a sidecar sets the identity); adoption notices are listed, not judged
- Parser version: `e09d2efdfbbd`

Why documents are not `checked`:

- 35 × unparsed N > N
- 29 × N records < N
- 25 × valid IDs N < N
- 17 × ragged tables N
- 8 × adoption notice
- 8 × coverage N < N

| Document | Issue | Tier | Records | Kinds (req/rec/perm/guid/del) | Valid IDs | Dup | Unparsed | Coverage | Tables (ragged) | Name ID | Time s | Reasons |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| ECSS-E-AS-11C |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 6 | 87% | 2 (0) | match | 0.4 | adoption notice |
| ECSS-E-AS-50-21C | Rev.2 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 20 | 90% | 1 (0) | match | 0.4 | adoption notice |
| ECSS-E-AS-50-22C | Rev.1 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 12 | 88% | 1 (0) | match | 0.3 | adoption notice |
| ECSS-E-AS-50-23C | Rev.1 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 1 | 69% | 1 (0) | match | 0.3 | adoption notice |
| ECSS-E-AS-50-24C | Rev.1 | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 10 | 87% | 1 (0) | match | 0.6 | adoption notice |
| ECSS-E-AS-50-25C | Rev.1 | unchecked | 1 | 1/0/0/0/0 | 100% | 0 | 7 | 85% | 1 (0) | match | 0.6 | adoption notice |
| ECSS-E-AS-50-26C |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 3 | 91% | 1 (0) | match | 0.4 | adoption notice |
| ECSS-E-HB-10-02A |  | unchecked | 294 | 0/0/0/294/0 | 78% | 64 | 0 | 94% | 3 (0) | match | 5.6 | valid IDs 78% < 95% |
| ECSS-E-HB-10-03A |  | checked | 400 | 0/0/0/400/0 | 98% | 9 | 0 | 95% | 7 (0) | match | 16.1 |  |
| ECSS-E-HB-10-12A |  | checked | 163 | 0/0/0/163/0 | 99% | 0 | 0 | 92% | 20 (0) | match | 7.0 |  |
| ECSS-E-HB-11A |  | checked | 60 | 0/0/0/60/0 | 100% | 0 | 0 | 93% | 6 (0) | match | 3.0 |  |
| ECSS-E-HB-20-01A |  | checked | 123 | 0/0/0/123/0 | 99% | 0 | 0 | 89% | 21 (0) | match | 9.8 |  |
| ECSS-E-HB-20-02A |  | checked | 46 | 0/0/0/46/0 | 100% | 0 | 0 | 93% | 3 (0) | match | 1.1 |  |
| ECSS-E-HB-20-05A |  | checked | 310 | 0/0/0/310/0 | 100% | 0 | 0 | 95% | 15 (0) | match | 13.1 |  |
| ECSS-E-HB-20-07A |  | checked | 236 | 0/0/0/236/0 | 97% | 6 | 0 | 83% | 8 (0) | match | 15.1 |  |
| ECSS-E-HB-20-20A |  | unchecked | 104 | 0/0/0/104/0 | 91% | 9 | 0 | 92% | 1 (0) | match | 4.2 | valid IDs 91% < 95% |
| ECSS-E-HB-20-40A |  | checked | 121 | 0/0/0/121/0 | 96% | 3 | 0 | 88% | 72 (0) | match | 12.8 |  |
| ECSS-E-HB-31-01 Part 10A |  | unchecked | 26 | 0/0/0/26/0 | 96% | 0 | 0 | 88% | 20 (3) | match | 5.7 | ragged tables 3/20 |
| ECSS-E-HB-31-01 Part 11A |  | checked | 72 | 0/0/0/72/0 | 100% | 0 | 0 | 89% | 13 (0) | match | 2.4 |  |
| ECSS-E-HB-31-01 Part 12A |  | checked | 47 | 0/0/0/47/0 | 98% | 0 | 0 | 76% | 18 (0) | match | 3.4 |  |
| ECSS-E-HB-31-01 Part 13A |  | unchecked | 209 | 0/0/0/209/0 | 100% | 0 | 0 | 83% | 82 (11) | match | 21.5 | ragged tables 11/82 |
| ECSS-E-HB-31-01 Part 14A |  | checked | 145 | 0/0/0/145/0 | 100% | 0 | 0 | 83% | 98 (5) | match | 26.5 |  |
| ECSS-E-HB-31-01 Part 15A |  | unchecked | 81 | 0/0/0/81/0 | 99% | 0 | 0 | 94% | 32 (5) | match | 8.9 | ragged tables 5/32 |
| ECSS-E-HB-31-01 Part 16A |  | checked | 20 | 0/0/0/20/0 | 100% | 0 | 0 | 90% | 0 (0) | match | 2.5 |  |
| ECSS-E-HB-31-01 Part 1A |  | unchecked | 65 | 0/0/0/65/0 | 100% | 0 | 0 | 47% | 0 (0) | match | 2.3 | coverage 47% < 75% |
| ECSS-E-HB-31-01 Part 2A |  | checked | 7 | 0/0/0/7/0 | 100% | 0 | 0 | 85% | 0 (0) | match | 0.7 |  |
| ECSS-E-HB-31-01 Part 3A |  | unchecked | 36 | 0/0/0/36/0 | 100% | 0 | 0 | 31% | 2 (0) | match | 1.9 | coverage 31% < 75% |
| ECSS-E-HB-31-01 Part 4A |  | checked | 42 | 0/0/0/42/0 | 100% | 0 | 0 | 80% | 11 (0) | match | 3.9 |  |
| ECSS-E-HB-31-01 Part 5A |  | checked | 98 | 0/0/0/98/0 | 99% | 0 | 0 | 83% | 114 (6) | match | 23.7 |  |
| ECSS-E-HB-31-01 Part 6A |  | unchecked | 30 | 0/0/0/30/0 | 93% | 0 | 0 | 92% | 52 (6) | match | 20.8 | valid IDs 93% < 95%; ragged tables 6/52 |
| ECSS-E-HB-31-01 Part 7A |  | checked | 59 | 0/0/0/59/0 | 98% | 0 | 0 | 81% | 50 (1) | match | 15.0 |  |
| ECSS-E-HB-31-01 Part 8A |  | unchecked | 49 | 0/0/0/49/0 | 100% | 0 | 0 | 77% | 17 (2) | match | 6.1 | ragged tables 2/17 |
| ECSS-E-HB-31-01 Part 9A |  | checked | 29 | 0/0/0/29/0 | 97% | 0 | 0 | 85% | 11 (0) | match | 3.1 |  |
| ECSS-E-HB-31-03A |  | checked | 108 | 0/0/0/108/0 | 98% | 0 | 0 | 94% | 3 (0) | match | 3.1 |  |
| ECSS-E-HB-32-20 Part 1A |  | checked | 495 | 0/0/0/495/0 | 100% | 0 | 0 | 84% | 0 (0) | match | 18.9 |  |
| ECSS-E-HB-32-20 Part 2A |  | checked | 684 | 0/0/0/684/0 | 100% | 0 | 0 | 84% | 0 (0) | match | 16.9 |  |
| ECSS-E-HB-32-20 Part 3A |  | checked | 619 | 0/0/0/619/0 | 100% | 1 | 0 | 88% | 0 (0) | match | 17.6 |  |
| ECSS-E-HB-32-20 Part 4A |  | checked | 775 | 0/0/0/775/0 | 100% | 0 | 0 | 92% | 0 (0) | match | 20.5 |  |
| ECSS-E-HB-32-20 Part 5A |  | checked | 631 | 0/0/0/631/0 | 100% | 0 | 0 | 90% | 0 (0) | match | 18.9 |  |
| ECSS-E-HB-32-20 Part 6A |  | checked | 700 | 0/0/0/700/0 | 100% | 0 | 0 | 93% | 0 (0) | match | 19.9 |  |
| ECSS-E-HB-32-20 Part 7A |  | checked | 758 | 0/0/0/758/0 | 100% | 0 | 0 | 92% | 0 (0) | match | 17.0 |  |
| ECSS-E-HB-32-20 Part 8A |  | checked | 1645 | 0/0/0/1645/0 | 100% | 3 | 0 | 92% | 0 (0) | match | 5.7 |  |
| ECSS-E-HB-32-21A |  | checked | 838 | 0/0/0/838/0 | 100% | 0 | 0 | 89% | 0 (0) | match | 18.0 |  |
| ECSS-E-HB-32-22A |  | unchecked | 487 | 0/0/0/487/0 | 100% | 0 | 0 | 87% | 27 (5) | match | 25.0 | ragged tables 5/27 |
| ECSS-E-HB-32-23A | Rev.1 | checked | 346 | 0/0/0/346/0 | 100% | 0 | 0 | 85% | 24 (1) | match | 11.0 |  |
| ECSS-E-HB-32-24A |  | checked | 697 | 0/0/0/697/0 | 100% | 0 | 0 | 89% | 30 (1) | match | 29.6 |  |
| ECSS-E-HB-32-25A |  | checked | 522 | 0/0/0/522/0 | 100% | 0 | 0 | 88% | 46 (1) | match | 31.2 |  |
| ECSS-E-HB-32-26A |  | checked | 506 | 0/0/0/506/0 | 96% | 16 | 0 | 92% | 38 (0) | match | 29.5 |  |
| ECSS-E-HB-40-01A |  | unchecked | 148 | 0/0/0/148/0 | 99% | 2 | 0 | 96% | 16 (3) | match | 7.5 | ragged tables 3/16 |
| ECSS-E-HB-40A |  | unchecked | 1068 | 0/0/0/1068/0 | 78% | 237 | 0 | 96% | 5 (2) | match | 12.6 | valid IDs 78% < 95%; ragged tables 2/5 |
| ECSS-E-HB-50A |  | checked | 357 | 0/0/0/357/0 | 100% | 0 | 0 | 90% | 19 (0) | match | 16.7 |  |
| ECSS-E-HB-60-10A |  | unchecked | 245 | 0/0/0/245/0 | 100% | 0 | 0 | 88% | 13 (2) | match | 8.2 | ragged tables 2/13 |
| ECSS-E-HB-60A |  | checked | 48 | 0/0/0/48/0 | 100% | 0 | 0 | 92% | 6 (0) | match | 2.5 |  |
| ECSS-E-ST-10-02C | Rev.1 | checked | 192 | 171/1/1/0/19 | 100% | 0 | 76 | 86% | 3 (0) | match | 2.9 |  |
| ECSS-E-ST-10-03C | Rev.1 | verified | 469 | 431/8/7/10/13 | 100% | 0 | 282 | 88% | 14 (0) | match | 7.2 |  |
| ECSS-E-ST-10-04C | Rev.1 | checked | 140 | 105/4/17/1/13 | 100% | 0 | 1004 | 87% | 8 (0) | match | 12.9 |  |
| ECSS-E-ST-10-06C |  | checked | 54 | 48/6/0/0/0 | 100% | 0 | 78 | 91% | 0 (0) | match | 0.9 |  |
| ECSS-E-ST-10-09C |  | checked | 92 | 87/5/0/0/0 | 100% | 0 | 68 | 85% | 0 (0) | match | 2.3 |  |
| ECSS-E-ST-10-11C |  | checked | 197 | 196/0/0/1/0 | 100% | 0 | 114 | 92% | 1 (1) | match | 2.4 |  |
| ECSS-E-ST-10-12C | Corr.1 | checked | 149 | 142/0/6/1/0 | 100% | 0 | 110 | 91% | 13 (1) | match | 4.4 |  |
| ECSS-E-ST-10-24C | Rev.1 | checked | 289 | 118/1/5/165/0 | 100% | 0 | 170 | 90% | 0 (0) | match | 2.7 |  |
| ECSS-E-ST-10C | Rev.1 | checked | 378 | 345/2/2/10/19 | 97% | 12 | 129 | 88% | 2 (0) | match | 5.4 |  |
| ECSS-E-ST-20-01C |  | checked | 229 | 197/3/20/9/0 | 100% | 0 | 121 | 86% | 10 (1) | match | 3.1 |  |
| ECSS-E-ST-20-06C | Rev.1 | checked | 173 | 149/3/13/1/7 | 99% | 0 | 291 | 81% | 3 (0) | match | 5.3 |  |
| ECSS-E-ST-20-07C | Rev.2 | checked | 281 | 256/4/11/4/6 | 100% | 0 | 297 | 86% | 4 (0) | match | 4.8 |  |
| ECSS-E-ST-20-08C | Rev.2 | checked | 1238 | 1167/30/28/1/12 | 100% | 2 | 521 | 87% | 22 (2) | match | 11.0 |  |
| ECSS-E-ST-20-20C |  | checked | 130 | 116/10/0/4/0 | 97% | 0 | 6 | 77% | 4 (0) | match | 3.1 |  |
| ECSS-E-ST-20-21C |  | checked | 87 | 68/17/2/0/0 | 100% | 0 | 24 | 92% | 0 (0) | match | 1.4 |  |
| ECSS-E-ST-20-40C |  | checked | 312 | 302/0/0/10/0 | 100% | 0 | 195 | 84% | 2 (0) | match | 7.0 |  |
| ECSS-E-ST-20C | Rev.2 | checked | 472 | 409/23/4/4/32 | 96% | 17 | 237 | 90% | 6 (1) | match | 25.7 |  |
| ECSS-E-ST-31-02C | Rev.1 | checked | 180 | 169/1/0/0/10 | 100% | 0 | 61 | 87% | 8 (0) | match | 1.8 |  |
| ECSS-E-ST-31-04C |  | checked | 33 | 26/3/3/1/0 | 100% | 0 | 60 | 92% | 1 (0) | match | 2.1 |  |
| ECSS-E-ST-31C |  | checked | 235 | 233/0/1/1/0 | 100% | 0 | 40 | 87% | 1 (1) | match | 2.4 |  |
| ECSS-E-ST-32-01C | Rev.2 | verified | 332 | 243/1/22/0/66 | 100% | 0 | 48 | 85% | 1 (0) | match | 3.7 |  |
| ECSS-E-ST-32-02C | Rev.1 | verified | 418 | 384/0/32/2/0 | 100% | 0 | 39 | 90% | 10 (0) | match | 3.2 |  |
| ECSS-E-ST-32-03C |  | verified | 45 | 43/2/0/0/0 | 100% | 0 | 8 | 87% | 0 (0) | match | 0.8 |  |
| ECSS-E-ST-32-08C | Rev.1 | verified | 77 | 74/1/0/0/2 | 100% | 0 | 20 | 87% | 0 (0) | match | 2.2 |  |
| ECSS-E-ST-32-10C | Rev.2 Corr.1 | verified | 28 | 28/0/0/0/0 | 100% | 0 | 16 | 78% | 6 (0) | match | 0.9 |  |
| ECSS-E-ST-32-11C |  | verified | 128 | 119/9/0/0/0 | 100% | 0 | 121 | 90% | 5 (0) | match | 3.1 |  |
| ECSS-E-ST-32C | Rev.1 | verified | 750 | 714/26/9/1/0 | 100% | 1 | 193 | 86% | 0 (0) | match | 5.4 |  |
| ECSS-E-ST-33-01C | Rev.2 | verified | 451 | 406/24/2/0/19 | 100% | 0 | 45 | 87% | 7 (0) | match | 3.0 |  |
| ECSS-E-ST-33-11C | Rev.1 | checked | 406 | 367/9/5/0/25 | 100% | 0 | 32 | 86% | 25 (0) | match | 3.9 |  |
| ECSS-E-ST-34C |  | checked | 218 | 216/1/0/1/0 | 100% | 0 | 61 | 82% | 1 (0) | match | 2.2 |  |
| ECSS-E-ST-35-01C |  | checked | 349 | 335/12/1/1/0 | 100% | 0 | 16 | 89% | 1 (0) | match | 2.5 |  |
| ECSS-E-ST-35-02C |  | checked | 166 | 157/6/3/0/0 | 100% | 0 | 35 | 86% | 5 (0) | match | 1.4 |  |
| ECSS-E-ST-35-03C |  | checked | 322 | 320/0/1/1/0 | 100% | 0 | 160 | 92% | 0 (0) | match | 1.9 |  |
| ECSS-E-ST-35-06C | Rev.2 | checked | 374 | 355/13/6/0/0 | 100% | 0 | 18 | 87% | 4 (0) | match | 2.9 |  |
| ECSS-E-ST-35-10C |  | checked | 279 | 269/2/6/2/0 | 100% | 0 | 52 | 89% | 0 (0) | match | 2.7 |  |
| ECSS-E-ST-35C | Rev.1 | checked | 403 | 395/8/0/0/0 | 100% | 0 | 132 | 88% | 1 (0) | match | 3.7 |  |
| ECSS-E-ST-40-07C | Rev.1 | checked | 599 | 591/1/6/1/0 | 100% | 0 | 186 | 93% | 19 (0) | match | 9.4 |  |
| ECSS-E-ST-40-08C |  | checked | 255 | 208/0/42/5/0 | 100% | 0 | 169 | 92% | 0 (0) | match | 3.9 |  |
| ECSS-E-ST-40C | Rev.1 | unchecked | 788 | 731/37/14/6/0 | 93% | 59 | 554 | 85% | 0 (0) | match | 11.9 | valid IDs 93% < 95% |
| ECSS-E-ST-50-02C |  | checked | 99 | 81/6/4/8/0 | 100% | 0 | 56 | 87% | 0 (0) | match | 2.4 |  |
| ECSS-E-ST-50-05C | Rev.2 | checked | 254 | 221/24/4/5/0 | 98% | 0 | 56 | 80% | 17 (0) | match | 3.4 |  |
| ECSS-E-ST-50-11C |  | unchecked | 1157 | 1068/46/43/0/0 | 68% | 373 | 47 | 89% | 37 (1) | match | 10.6 | valid IDs 68% < 95% |
| ECSS-E-ST-50-12C | Rev.1 | checked | 531 | 482/38/11/0/0 | 100% | 0 | 70 | 88% | 11 (1) | match | 5.8 |  |
| ECSS-E-ST-50-13C |  | unchecked | 181 | 167/3/9/2/0 | 99% | 0 | 229 | 88% | 25 (5) | match | 5.5 | ragged tables 5/25 |
| ECSS-E-ST-50-14C |  | checked | 137 | 122/8/7/0/0 | 100% | 0 | 174 | 78% | 22 (0) | match | 3.4 |  |
| ECSS-E-ST-50-15C |  | checked | 237 | 221/9/7/0/0 | 100% | 0 | 110 | 84% | 23 (1) | match | 5.0 |  |
| ECSS-E-ST-50-16C |  | checked | 230 | 168/62/0/0/0 | 100% | 0 | 266 | 87% | 23 (2) | match | 5.0 |  |
| ECSS-E-ST-50-51C |  | unchecked | 14 | 12/0/2/0/0 | 100% | 0 | 7 | 86% | 1 (0) | match | 0.8 | 14 records < 20 |
| ECSS-E-ST-50-52C |  | checked | 381 | 291/60/9/21/0 | 100% | 0 | 399 | 81% | 10 (0) | match | 4.6 |  |
| ECSS-E-ST-50-53C |  | checked | 51 | 47/2/2/0/0 | 100% | 0 | 30 | 88% | 0 (0) | match | 0.6 |  |
| ECSS-E-ST-50C | Rev.2 | checked | 236 | 214/14/1/3/4 | 100% | 0 | 254 | 85% | 0 (0) | match | 3.6 |  |
| ECSS-E-ST-60-10C |  | checked | 39 | 35/4/0/0/0 | 100% | 0 | 105 | 86% | 0 (0) | match | 3.6 |  |
| ECSS-E-ST-60-20C | Rev.2 | checked | 204 | 179/6/3/12/4 | 100% | 0 | 148 | 89% | 0 (0) | match | 3.3 |  |
| ECSS-E-ST-60-21C |  | checked | 235 | 229/2/4/0/0 | 100% | 0 | 31 | 89% | 0 (0) | match | 2.0 |  |
| ECSS-E-ST-60-30C |  | checked | 141 | 139/2/0/0/0 | 100% | 0 | 87 | 92% | 0 (0) | match | 1.9 |  |
| ECSS-E-ST-70-01C |  | checked | 140 | 139/1/0/0/0 | 96% | 5 | 89 | 91% | 0 (0) | match | 1.6 |  |
| ECSS-E-ST-70-11C |  | checked | 348 | 330/17/1/0/0 | 100% | 0 | 89 | 94% | 3 (0) | match | 3.4 |  |
| ECSS-E-ST-70-31C |  | unchecked | 190 | 180/6/0/4/0 | 88% | 22 | 1026 | 72% | 118 (16) | match | 11.2 | valid IDs 88% < 95%; coverage 72% < 75%; ragged tables 16/118 |
| ECSS-E-ST-70-32C |  | checked | 78 | 28/4/12/34/0 | 100% | 0 | 913 | 88% | 0 (0) | match | 6.0 |  |
| ECSS-E-ST-70-41C |  | checked | 3197 | 3193/1/1/2/0 | 100% | 0 | 611 | 91% | 41 (0) | match | 31.3 |  |
| ECSS-E-ST-70C |  | checked | 359 | 347/3/8/1/0 | 99% | 4 | 145 | 85% | 34 (0) | match | 10.5 |  |
| ECSS-E-ST-80C |  | checked | 140 | 139/0/1/0/0 | 100% | 0 | 101 | 89% | 0 (0) | match | 2.8 |  |
| ECSS-M-70A |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 206 | 90% | 0 (0) | match | 1.1 | 0 records < 20 |
| ECSS-M-ST-10-01C |  | checked | 54 | 54/0/0/0/0 | 100% | 0 | 39 | 85% | 0 (0) | match | 0.8 |  |
| ECSS-M-ST-10C | Rev.1 | checked | 99 | 93/0/6/0/0 | 100% | 0 | 243 | 90% | 0 (0) | match | 1.9 |  |
| ECSS-M-ST-40C | Rev.1 | checked | 275 | 241/1/2/31/0 | 100% | 0 | 246 | 90% | 0 (0) | match | 3.8 |  |
| ECSS-M-ST-60C |  | checked | 136 | 127/6/2/1/0 | 100% | 0 | 310 | 78% | 0 (0) | match | 3.7 |  |
| ECSS-M-ST-80C |  | checked | 135 | 122/7/4/2/0 | 100% | 0 | 77 | 87% | 0 (0) | match | 1.8 |  |
| ECSS-P-00C | Rev.1 | unchecked | 4 | 2/0/0/2/0 | 100% | 0 | 146 | 90% | 0 (0) | match | 0.9 | 4 records < 20 |
| ECSS-Q-HB-30-01A |  | checked | 37 | 0/0/0/37/0 | 100% | 0 | 0 | 92% | 2 (0) | match | 0.9 |  |
| ECSS-Q-HB-30-03A |  | unchecked | 139 | 0/0/0/139/0 | 73% | 37 | 0 | 93% | 0 (0) | match | 3.0 | valid IDs 73% < 95% |
| ECSS-Q-HB-30-08A |  | checked | 33 | 0/0/0/33/0 | 100% | 0 | 0 | 91% | 2 (0) | match | 1.4 |  |
| ECSS-Q-HB-70-23A |  | unchecked | 132 | 0/0/0/132/0 | 80% | 19 | 0 | 86% | 1 (0) | match | 1.4 | valid IDs 80% < 95% |
| ECSS-Q-HB-80-01A |  | unchecked | 128 | 0/0/0/128/0 | 84% | 0 | 0 | 97% | 2 (0) | match | 3.7 | valid IDs 84% < 95% |
| ECSS-Q-HB-80-02 Part 1A |  | unchecked | 369 | 0/0/0/369/0 | 91% | 0 | 0 | 94% | 8 (1) | match | 7.0 | valid IDs 91% < 95% |
| ECSS-Q-HB-80-02 Part 2A |  | checked | 12 | 0/0/0/12/0 | 100% | 0 | 0 | 91% | 2 (1) | match | 5.9 |  |
| ECSS-Q-HB-80-03A |  | checked | 72 | 0/0/0/72/0 | 100% | 0 | 0 | 97% | 0 (0) | match | 2.4 |  |
| ECSS-Q-HB-80-04A |  | checked | 81 | 0/0/0/81/0 | 100% | 0 | 0 | 92% | 3 (0) | match | 5.1 |  |
| ECSS-Q-ST-10-04C |  | checked | 62 | 62/0/0/0/0 | 100% | 0 | 38 | 86% | 0 (0) | match | 1.2 |  |
| ECSS-Q-ST-10-09C | Rev.1 | checked | 147 | 116/7/1/0/23 | 100% | 0 | 31 | 83% | 0 (0) | match | 1.1 |  |
| ECSS-Q-ST-10C | Rev.1 | checked | 74 | 70/0/4/0/0 | 100% | 0 | 45 | 90% | 1 (0) | match | 2.4 |  |
| ECSS-Q-ST-20-07C |  | checked | 192 | 191/1/0/0/0 | 98% | 3 | 11 | 93% | 0 (0) | match | 1.4 |  |
| ECSS-Q-ST-20-08C |  | checked | 146 | 142/3/0/1/0 | 100% | 0 | 17 | 89% | 1 (0) | match | 2.2 |  |
| ECSS-Q-ST-20-10C |  | checked | 139 | 139/0/0/0/0 | 100% | 0 | 29 | 88% | 0 (0) | match | 1.3 |  |
| ECSS-Q-ST-20-30C |  | unchecked | 66 | 64/0/2/0/0 | 100% | 0 | 242 | 69% | 0 (0) | match | 2.1 | coverage 69% < 75% |
| ECSS-Q-ST-20C | Rev.2 | checked | 256 | 234/1/3/1/17 | 100% | 0 | 41 | 89% | 2 (0) | match | 4.2 |  |
| ECSS-Q-ST-30-02C |  | checked | 181 | 180/0/1/0/0 | 100% | 0 | 74 | 87% | 7 (0) | match | 2.9 |  |
| ECSS-Q-ST-30-09C |  | unchecked | 59 | 44/0/0/15/0 | 76% | 0 | 64 | 90% | 1 (1) | match | 1.2 | valid IDs 76% < 95% |
| ECSS-Q-ST-30-11C | Rev.2 | unchecked | 213 | 127/19/4/0/63 | 100% | 0 | 64 | 72% | 33 (0) | match | 3.2 | coverage 72% < 75% |
| ECSS-Q-ST-30C | Rev.1 | checked | 179 | 125/0/8/35/11 | 100% | 0 | 70 | 83% | 5 (0) | match | 3.4 |  |
| ECSS-Q-ST-40-02C |  | unchecked | 43 | 19/0/0/24/0 | 74% | 0 | 62 | 84% | 4 (1) | match | 1.4 | valid IDs 74% < 95% |
| ECSS-Q-ST-40-12C |  | unchecked | 7 | 7/0/0/0/0 | 100% | 0 | 1 | 91% | 0 (0) | match | 0.2 | 7 records < 20 |
| ECSS-Q-ST-40C | Rev.1 | checked | 349 | 323/0/2/20/4 | 100% | 0 | 68 | 89% | 3 (0) | match | 3.1 |  |
| ECSS-Q-ST-60-03C |  | unchecked | 7 | 0/0/0/7/0 | 100% | 0 | 545 | 88% | 2 (0) | match | 4.4 | 7 records < 20 |
| ECSS-Q-ST-60-05C | Rev.1 | checked | 221 | 196/1/23/1/0 | 100% | 0 | 99 | 89% | 7 (1) | match | 2.9 |  |
| ECSS-Q-ST-60-12C |  | checked | 218 | 198/6/10/4/0 | 100% | 0 | 44 | 88% | 2 (0) | match | 2.1 |  |
| ECSS-Q-ST-60-13C | Rev.2 | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 186 | 69% | 21 (0) | match | 6.3 | 0 records < 20; coverage 69% < 75% |
| ECSS-Q-ST-60-14C | Rev.1 Corr.1 | checked | 109 | 80/1/2/9/17 | 100% | 0 | 2 | 85% | 3 (0) | match | 1.6 |  |
| ECSS-Q-ST-60-15C | Rev.1 | checked | 118 | 114/0/4/0/0 | 100% | 0 | 19 | 91% | 7 (1) | match | 1.9 |  |
| ECSS-Q-ST-60C | Rev.4 | unchecked | 5 | 5/0/0/0/0 | 0% | 0 | 1242 | 93% | 6 (0) | match | 6.8 | 5 records < 20; valid IDs 0% < 95% |
| ECSS-Q-ST-70-01C |  | checked | 273 | 248/5/0/20/0 | 95% | 5 | 176 | 90% | 4 (0) | match | 3.5 |  |
| ECSS-Q-ST-70-02C |  | checked | 152 | 148/4/0/0/0 | 100% | 0 | 37 | 85% | 0 (0) | match | 1.7 |  |
| ECSS-Q-ST-70-03C |  | checked | 102 | 64/0/0/38/0 | 100% | 0 | 29 | 89% | 0 (0) | match | 0.9 |  |
| ECSS-Q-ST-70-04C |  | unchecked | 90 | 58/0/0/32/0 | 88% | 0 | 27 | 89% | 0 (0) | match | 0.8 | valid IDs 88% < 95% |
| ECSS-Q-ST-70-05C | Rev.2 | checked | 259 | 134/1/0/117/7 | 100% | 0 | 242 | 91% | 1 (0) | match | 3.7 |  |
| ECSS-Q-ST-70-06C |  | checked | 80 | 80/0/0/0/0 | 100% | 0 | 13 | 87% | 0 (0) | match | 1.1 |  |
| ECSS-Q-ST-70-09C |  | checked | 55 | 41/0/0/14/0 | 100% | 0 | 56 | 78% | 0 (0) | match | 1.0 |  |
| ECSS-Q-ST-70-12C | Rev.1 | unchecked | 593 | 358/119/63/20/33 | 99% | 3 | 102 | 78% | 30 (4) | match | 9.4 | ragged tables 4/30 |
| ECSS-Q-ST-70-13C | Rev.1 | checked | 75 | 70/3/1/1/0 | 99% | 0 | 16 | 88% | 0 (0) | match | 1.2 |  |
| ECSS-Q-ST-70-14C |  | checked | 74 | 68/1/5/0/0 | 100% | 0 | 68 | 89% | 2 (0) | match | 1.1 |  |
| ECSS-Q-ST-70-15C |  | unchecked | 437 | 351/4/19/63/0 | 93% | 21 | 210 | 89% | 3 (0) | match | 5.4 | valid IDs 93% < 95% |
| ECSS-Q-ST-70-16C |  | checked | 133 | 111/10/12/0/0 | 99% | 0 | 393 | 85% | 0 (0) | match | 3.8 |  |
| ECSS-Q-ST-70-17C |  | checked | 94 | 87/0/4/3/0 | 100% | 0 | 64 | 85% | 6 (0) | match | 1.8 |  |
| ECSS-Q-ST-70-18C |  | checked | 213 | 202/6/3/2/0 | 100% | 0 | 21 | 87% | 2 (0) | match | 1.6 |  |
| ECSS-Q-ST-70-20C |  | checked | 34 | 33/0/1/0/0 | 100% | 0 | 14 | 83% | 1 (0) | match | 0.6 |  |
| ECSS-Q-ST-70-21C |  | checked | 244 | 142/7/1/94/0 | 100% | 0 | 58 | 84% | 0 (0) | match | 1.6 |  |
| ECSS-Q-ST-70-22C |  | unchecked | 30 | 28/0/0/2/0 | 93% | 0 | 4 | 89% | 0 (0) | match | 0.5 | valid IDs 93% < 95% |
| ECSS-Q-ST-70-26C | Rev.1 Corr.1 | checked | 214 | 188/2/4/0/20 | 100% | 0 | 49 | 83% | 1 (0) | match | 1.8 |  |
| ECSS-Q-ST-70-28C |  | checked | 349 | 95/28/0/226/0 | 100% | 0 | 120 | 82% | 1 (0) | match | 2.5 |  |
| ECSS-Q-ST-70-29C |  | checked | 76 | 66/1/0/9/0 | 100% | 0 | 9 | 89% | 1 (0) | match | 0.9 |  |
| ECSS-Q-ST-70-30C |  | checked | 184 | 183/1/0/0/0 | 100% | 0 | 58 | 89% | 4 (0) | match | 1.6 |  |
| ECSS-Q-ST-70-31C | Rev.1 | checked | 107 | 101/0/5/0/1 | 100% | 0 | 0 | 88% | 0 (0) | match | 0.8 |  |
| ECSS-Q-ST-70-36C |  | checked | 55 | 54/0/1/0/0 | 100% | 0 | 54 | 85% | 3 (0) | match | 1.2 |  |
| ECSS-Q-ST-70-37C |  | unchecked | 99 | 70/1/0/28/0 | 84% | 0 | 11 | 92% | 0 (0) | match | 1.2 | valid IDs 84% < 95% |
| ECSS-Q-ST-70-39C |  | checked | 236 | 226/4/6/0/0 | 100% | 0 | 34 | 85% | 12 (0) | match | 2.6 |  |
| ECSS-Q-ST-70-40C |  | unchecked | 2 | 1/0/0/1/0 | 100% | 0 | 198 | 84% | 3 (0) | match | 1.5 | 2 records < 20 |
| ECSS-Q-ST-70-45C |  | checked | 98 | 97/1/0/0/0 | 100% | 0 | 47 | 88% | 0 (0) | match | 1.2 |  |
| ECSS-Q-ST-70-46C | Rev.1 | checked | 147 | 147/0/0/0/0 | 100% | 0 | 9 | 86% | 1 (0) | match | 1.2 |  |
| ECSS-Q-ST-70-50C |  | checked | 219 | 197/21/1/0/0 | 100% | 0 | 37 | 89% | 1 (0) | match | 2.0 |  |
| ECSS-Q-ST-70-53C |  | checked | 55 | 55/0/0/0/0 | 100% | 0 | 133 | 87% | 2 (0) | match | 2.2 |  |
| ECSS-Q-ST-70-54C |  | checked | 55 | 52/2/0/1/0 | 98% | 0 | 365 | 87% | 1 (0) | match | 2.8 |  |
| ECSS-Q-ST-70-55C |  | checked | 36 | 35/0/1/0/0 | 100% | 0 | 455 | 93% | 0 (0) | match | 2.5 |  |
| ECSS-Q-ST-70-56C |  | checked | 43 | 43/0/0/0/0 | 100% | 0 | 25 | 88% | 0 (0) | match | 0.7 |  |
| ECSS-Q-ST-70-57C |  | checked | 37 | 37/0/0/0/0 | 100% | 0 | 29 | 87% | 0 (0) | match | 0.8 |  |
| ECSS-Q-ST-70-58C |  | checked | 106 | 67/2/0/37/0 | 100% | 0 | 125 | 89% | 0 (0) | match | 1.7 |  |
| ECSS-Q-ST-70-60C | Rev.1 | checked | 834 | 675/74/69/13/3 | 97% | 24 | 467 | 83% | 80 (2) | match | 14.8 |  |
| ECSS-Q-ST-70-61C |  | unchecked | 3 | 3/0/0/0/0 | 100% | 0 | 1941 | 90% | 30 (1) | match | 9.8 | 3 records < 20 |
| ECSS-Q-ST-70-71C | Rev.1 | checked | 245 | 243/2/0/0/0 | 100% | 0 | 11 | 89% | 0 (0) | match | 2.2 |  |
| ECSS-Q-ST-70-80C |  | unchecked | 7 | 0/0/0/7/0 | 100% | 0 | 629 | 86% | 7 (0) | match | 2.8 | 7 records < 20 |
| ECSS-Q-ST-70C | Rev.2 | verified | 281 | 241/5/3/24/8 | 100% | 0 | 54 | 85% | 2 (0) | match | 3.3 |  |
| ECSS-Q-ST-80C | Rev.2 | checked | 347 | 343/0/0/1/3 | 100% | 0 | 54 | 83% | 0 (0) | match | 6.9 |  |
| ECSS-S-ST-00-01C | Rev.1 | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 0 | – | 0 (0) | match | 2.2 | 0 records < 20 |
| ECSS-S-ST-00-02C |  | checked | 29 | 23/0/0/6/0 | 100% | 0 | 117 | 86% | 0 (0) | match | 0.9 |  |
| ECSS-S-ST-00C | Rev.1 | unchecked | 6 | 6/0/0/0/0 | 100% | 0 | 94 | 87% | 4 (0) | match | 1.0 | 6 records < 20 |
| ECSS-U-AS-10C | Rev.2 | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 0 | – | 1 (0) | match | 0.5 | adoption notice |
| ECSS-U-ST-20C |  | unchecked | 97 | 84/0/4/9/0 | 92% | 0 | 68 | 89% | 2 (0) | match | 1.5 | valid IDs 92% < 95% |
| NASA-HDBK-1004 |  | unchecked | 2 | 0/0/0/2/0 | 100% | 0 | 0 | 60% | 8 (1) | match | 11.9 | 2 records < 3; coverage 60% < 75% |
| NASA-HDBK-1005 |  | unchecked | 1 | 0/0/0/1/0 | 100% | 0 | 0 | 88% | 8 (0) | match | 7.0 | 1 records < 3 |
| NASA-HDBK-1009A |  | checked | 49 | 0/0/0/49/0 | 100% | 0 | 0 | 78% | 0 (0) | match | 2.9 |  |
| NASA-HDBK-2203 |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 1 | 100% | 0 (0) | match | 0.0 | 0 records < 3; unparsed 100% > 10% |
| NASA-HDBK-4001A |  | checked | 18 | 0/0/0/18/0 | 100% | 0 | 0 | 86% | 5 (1) | match | 2.5 |  |
| NASA-HDBK-4002B |  | unchecked | 1 | 0/0/0/1/0 | 100% | 0 | 0 | 98% | 16 (0) | match | 13.1 | 1 records < 3 |
| NASA-HDBK-4006A |  | checked | 45 | 0/0/0/45/0 | 100% | 0 | 0 | 97% | 2 (0) | match | 5.8 |  |
| NASA-HDBK-4007A |  | unchecked | 1 | 0/0/0/1/0 | 0% | 0 | 39 | 100% | 15 (1) | match | 7.1 | 1 records < 3; valid IDs 0% < 95%; unparsed 98% > 10% |
| NASA-HDBK-4008 | w/Change 2 | unchecked | 140 | 0/0/0/140/0 | 100% | 0 | 0 | 97% | 7 (2) | none | 5.9 | ragged tables 2/7 |
| NASA-HDBK-4011 |  | checked | 14 | 0/0/0/14/0 | 100% | 0 | 0 | 100% | 0 (0) | match | 2.0 |  |
| NASA-HDBK-5010 Vol 1 | Rev.A | checked | 743 | 303/0/0/440/0 | 95% | 34 | 0 | 98% | 0 (0) | match | 20.7 |  |
| NASA-HDBK-5010 Vol 2 | Rev.A | checked | 244 | 8/0/0/236/0 | 100% | 0 | 0 | 91% | 0 (0) | match | 20.9 |  |
| NASA-HDBK-5026 |  | checked | 78 | 12/0/0/66/0 | 97% | 2 | 0 | 97% | 7 (1) | match | 6.8 |  |
| NASA-HDBK-6007B | w/Change 1 | checked | 26 | 0/0/0/26/0 | 100% | 0 | 0 | 93% | 1 (0) | match | 1.5 |  |
| NASA-HDBK-6024 | w/Change 2 | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 0 | 0% | 27 (1) | match | 15.5 | 0 records < 3; coverage 0% < 75% |
| NASA-HDBK-7005 |  | checked | 261 | 0/0/0/261/0 | 100% | 0 | 0 | 99% | 0 (0) | match | 13.2 |  |
| NASA-HDBK-7009B |  | checked | 135 | 1/0/0/134/0 | 100% | 0 | 0 | 95% | 39 (1) | match | 13.2 |  |
| NASA-HDBK-7010 |  | checked | 31 | 0/0/0/31/0 | 100% | 0 | 0 | 93% | 0 (0) | match | 2.6 |  |
| NASA-HDBK-8709.22 |  | unchecked | 1 | 0/0/0/1/0 | 100% | 0 | 0 | 100% | 0 (0) | match | 9.2 | 1 records < 3 |
| NASA-HDBK-8709.24 |  | checked | 40 | 0/0/0/40/0 | 100% | 0 | 0 | 96% | 0 (0) | none | 2.5 |  |
| NASA-HDBK-8709.25 |  | checked | 24 | 0/0/0/24/0 | 100% | 0 | 0 | 98% | 0 (0) | none | 1.6 |  |
| NASA-HDBK-8715.26 |  | checked | 18 | 0/0/0/18/0 | 100% | 0 | 0 | 99% | 9 (0) | none | 5.5 |  |
| NASA-HDBK-8719.14 |  | checked | 182 | 0/0/0/182/0 | 100% | 0 | 0 | 95% | 0 (0) | none | 21.7 |  |
| NASA-HDBK-8739.18 |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 1 | 85% | 0 (0) | none | 4.9 | 0 records < 3; unparsed 100% > 10% |
| NASA-HDBK-8739.19-2 |  | checked | 299 | 0/0/0/299/0 | 100% | 0 | 0 | 97% | 0 (0) | match | 9.2 |  |
| NASA-HDBK-8739.19-3 |  | checked | 319 | 0/0/0/319/0 | 100% | 0 | 0 | 95% | 0 (0) | none | 12.8 |  |
| NASA-HDBK-8739.19-4 |  | checked | 15 | 0/0/0/15/0 | 100% | 0 | 0 | 98% | 0 (0) | none | 10.3 |  |
| NASA-HDBK-8739.21 |  | unchecked | 56 | 0/0/0/56/0 | 100% | 0 | 0 | 97% | 8 (2) | none | 3.8 | ragged tables 2/8 |
| NASA-SPEC-5022 | w/Change 2 | verified | 109 | 79/0/0/30/0 | 100% | 0 | 3 | 89% | 0 (0) | match | 2.2 |  |
| NASA-STD-10001 |  | checked | 156 | 107/0/0/49/0 | 100% | 0 | 2 | 88% | 3 (1) | match | 3.3 |  |
| NASA-STD-10002 |  | checked | 356 | 235/0/0/121/0 | 100% | 0 | 0 | 88% | 0 (0) | match | 4.7 |  |
| NASA-STD-1006A |  | checked | 49 | 6/0/0/43/0 | 100% | 0 | 0 | 95% | 0 (0) | match | 1.0 |  |
| NASA-STD-1008 |  | unchecked | 326 | 15/0/0/311/0 | 100% | 0 | 43 | 96% | 5 (0) | match | 5.4 | unparsed 12% > 10% |
| NASA-STD-2818 |  | unchecked | 1 | 0/0/0/1/0 | 100% | 0 | 23 | 98% | 0 (0) | match | 2.7 | 1 records < 20; unparsed 96% > 10% |
| NASA-STD-2821 |  | unchecked | 18 | 17/0/0/1/0 | 100% | 0 | 29 | 98% | 0 (0) | match | 0.8 | 18 records < 20; unparsed 62% > 10% |
| NASA-STD-2822 |  | unchecked | 16 | 15/0/0/1/0 | 100% | 0 | 102 | 97% | 0 (0) | match | 1.8 | 16 records < 20; unparsed 86% > 10% |
| NASA-STD-3001 Vol 1 | Rev.C | unchecked | 53 | 53/0/0/0/0 | 9% | 31 | 137 | 96% | 0 (0) | match | 4.5 | valid IDs 9% < 95%; unparsed 72% > 10% |
| NASA-STD-3001 Vol 2 | Rev.F | unchecked | 667 | 296/0/0/371/0 | 100% | 0 | 228 | 94% | 0 (0) | match | 21.4 | unparsed 25% > 10% |
| NASA-STD-4003A | w/Change 1 | checked | 135 | 93/0/0/42/0 | 100% | 0 | 1 | 89% | 1 (0) | match | 2.2 |  |
| NASA-STD-4005A | w/Change 1 | checked | 81 | 14/0/0/67/0 | 100% | 0 | 0 | 95% | 0 (0) | match | 3.1 |  |
| NASA-STD-4010B |  | checked | 63 | 35/0/0/28/0 | 100% | 0 | 1 | 96% | 1 (1) | none | 2.1 |  |
| NASA-STD-5001B | w/Change 3 | verified | 117 | 61/0/0/56/0 | 100% | 0 | 1 | 91% | 7 (0) | match | 2.0 |  |
| NASA-STD-5002B |  | verified | 148 | 67/0/0/80/1 | 100% | 0 | 0 | 94% | 1 (0) | match | 3.1 |  |
| NASA-STD-5005D | w/Change 2 | verified | 414 | 251/0/0/163/0 | 100% | 0 | 3 | 94% | 0 (0) | match | 4.0 |  |
| NASA-STD-5006A | w/Change 2 | verified | 176 | 138/0/0/38/0 | 100% | 0 | 0 | 85% | 0 (0) | match | 2.4 |  |
| NASA-STD-5008B | w/Change 2 | verified | 366 | 319/0/0/47/0 | 100% | 0 | 1 | 87% | 1 (0) | match | 5.3 |  |
| NASA-STD-5009C |  | verified | 122 | 74/0/0/48/0 | 100% | 0 | 4 | 91% | 3 (0) | match | 3.0 |  |
| NASA-STD-5012C |  | verified | 55 | 28/0/0/27/0 | 100% | 0 | 1 | 96% | 2 (0) | match | 2.5 |  |
| NASA-STD-5017B |  | verified | 188 | 90/0/0/98/0 | 100% | 0 | 4 | 97% | 8 (0) | match | 7.2 |  |
| NASA-STD-5018 | w/Change 1 | verified | 283 | 234/0/0/49/0 | 100% | 0 | 7 | 87% | 1 (0) | match | 2.9 |  |
| NASA-STD-5019A | w/Change 4 | verified | 498 | 245/0/0/253/0 | 100% | 0 | 0 | 97% | 8 (3) | match | 6.2 | ragged tables 3/8 |
| NASA-STD-5020B |  | verified | 200 | 32/0/0/168/0 | 100% | 0 | 19 | 97% | 7 (0) | match | 5.8 |  |
| NASA-STD-5023 |  | verified | 293 | 105/0/0/188/0 | 100% | 0 | 1 | 96% | 4 (0) | match | 5.4 |  |
| NASA-STD-6001B | w/Change 3 | checked | 324 | 207/0/0/117/0 | 100% | 0 | 7 | 90% | 6 (0) | match | 8.4 |  |
| NASA-STD-6012A |  | unchecked | 128 | 42/0/0/86/0 | 100% | 0 | 31 | 95% | 1 (0) | match | 3.1 | unparsed 19% > 10% |
| NASA-STD-6016C | w/Change 1 | checked | 428 | 207/0/0/221/0 | 100% | 0 | 3 | 94% | 0 (0) | match | 9.6 |  |
| NASA-STD-6030 |  | unchecked | 456 | 114/0/0/342/0 | 100% | 0 | 291 | 97% | 19 (2) | match | 11.2 | unparsed 39% > 10%; ragged tables 2/19 |
| NASA-STD-6033 |  | unchecked | 59 | 31/0/0/28/0 | 100% | 0 | 124 | 97% | 0 (0) | match | 2.6 | unparsed 68% > 10% |
| NASA-STD-7001C |  | verified | 142 | 64/0/0/78/0 | 100% | 0 | 5 | 94% | 3 (0) | match | 2.9 |  |
| NASA-STD-7002B | w/Change 1 | verified | 102 | 63/0/0/39/0 | 100% | 0 | 0 | 89% | 3 (0) | match | 2.3 |  |
| NASA-STD-7003A |  | verified | 69 | 26/0/0/43/0 | 100% | 0 | 2 | 98% | 2 (0) | match | 1.8 |  |
| NASA-STD-7009B |  | checked | 215 | 43/0/0/172/0 | 100% | 0 | 1 | 98% | 18 (1) | match | 7.2 |  |
| NASA-STD-7012A |  | checked | 89 | 39/0/0/50/0 | 100% | 0 | 1 | 97% | 4 (0) | match | 3.8 |  |
| NASA-STD-7919.1 |  | unchecked | 162 | 161/0/0/1/0 | 100% | 0 | 93 | 93% | 0 (0) | match | 6.4 | unparsed 36% > 10% |
| NASA-STD-8719.11B |  | unchecked | 390 | 369/0/0/21/0 | 100% | 0 | 555 | 98% | 0 (0) | none | 3.9 | unparsed 59% > 10% |
| NASA-STD-8719.12B |  | unchecked | 417 | 383/0/0/34/0 | 94% | 25 | 442 | 95% | 25 (4) | match | 10.4 | valid IDs 94% < 95%; unparsed 51% > 10%; ragged tables 4/25 |
| NASA-STD-8719.14C |  | unchecked | 52 | 20/0/0/32/0 | 100% | 0 | 566 | 99% | 0 (0) | none | 5.0 | unparsed 92% > 10% |
| NASA-STD-8719.17 | Rev.C | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 610 | 99% | 0 (0) | none | 3.5 | 0 records < 20; unparsed 100% > 10% |
| NASA-STD-8719.24 |  | unchecked | 32 | 24/0/0/8/0 | 91% | 3 | 40 | 97% | 0 (0) | none | 0.4 | valid IDs 91% < 95%; unparsed 56% > 10% |
| NASA-STD-8719.24 Annex |  | unchecked | 15 | 0/0/0/15/0 | 0% | 0 | 867 | 100% | 0 (0) | match | 36.1 | 15 records < 20; valid IDs 0% < 95%; unparsed 98% > 10% |
| NASA-STD-8719.25 |  | unchecked | 107 | 77/0/0/30/0 | 100% | 0 | 42 | 97% | 0 (0) | none | 1.9 | unparsed 28% > 10% |
| NASA-STD-8719.26 |  | unchecked | 32 | 32/0/0/0/0 | 100% | 0 | 4 | 98% | 0 (0) | none | 0.8 | unparsed 11% > 10% |
| NASA-STD-8719.27 |  | unchecked | 162 | 102/0/0/60/0 | 100% | 0 | 216 | 98% | 0 (0) | none | 2.4 | unparsed 57% > 10% |
| NASA-STD-8719.28 |  | unchecked | 0 | 0/0/0/0/0 | 0% | 0 | 1021 | 99% | 0 (0) | none | 6.8 | 0 records < 20; unparsed 100% > 10% |
| NASA-STD-8719.29 |  | unchecked | 83 | 32/0/0/51/0 | 100% | 0 | 17 | 99% | 0 (0) | none | 1.4 | unparsed 17% > 10% |
| NASA-STD-8719.30 |  | unchecked | 16 | 8/0/0/8/0 | 100% | 0 | 47 | 95% | 0 (0) | match | 0.7 | 16 records < 20; unparsed 75% > 10% |
| NASA-STD-8719.9C |  | unchecked | 401 | 278/0/0/123/0 | 100% | 0 | 183 | 97% | 2 (0) | match | 3.9 | unparsed 31% > 10% |
| NASA-STD-8729.1A |  | unchecked | 11 | 8/0/0/3/0 | 100% | 0 | 45 | 98% | 0 (0) | match | 2.0 | 11 records < 20; unparsed 80% > 10% |
| NASA-STD-8739.10 |  | unchecked | 94 | 90/0/0/4/0 | 100% | 0 | 107 | 97% | 0 (0) | none | 1.6 | unparsed 53% > 10% |
| NASA-STD-8739.12 | Rev.A | unchecked | 8 | 6/0/0/2/0 | 100% | 0 | 8 | 92% | 0 (0) | none | 0.5 | 8 records < 20; unparsed 50% > 10% |
| NASA-STD-8739.14 |  | unchecked | 40 | 29/0/0/11/0 | 100% | 0 | 18 | 95% | 2 (1) | none | 0.8 | unparsed 31% > 10% |
| NASA-STD-8739.1B |  | unchecked | 156 | 151/0/0/5/0 | 86% | 22 | 97 | 93% | 0 (0) | match | 1.9 | valid IDs 86% < 95%; unparsed 38% > 10% |
| NASA-STD-8739.4A |  | unchecked | 365 | 354/0/0/11/0 | 96% | 14 | 168 | 91% | 0 (0) | match | 3.7 | unparsed 32% > 10% |
| NASA-STD-8739.5A |  | unchecked | 144 | 138/0/0/6/0 | 100% | 0 | 23 | 94% | 0 (0) | match | 1.5 | unparsed 14% > 10% |
| NASA-STD-8739.6B |  | unchecked | 199 | 172/0/0/27/0 | 100% | 0 | 85 | 96% | 0 (0) | match | 2.4 | unparsed 30% > 10% |
| NASA-STD-8739.8B |  | unchecked | 74 | 52/0/0/22/0 | 100% | 0 | 191 | 98% | 1 (0) | match | 3.5 | unparsed 72% > 10% |
