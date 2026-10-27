# Actual repeated-run findings

Five cases x ten matched seeds x three policies = 150 simulation runs.

| Case | Policy | Demand delivery mean ± SD (%) | Mean delay s | EU / delivered | Runs with battery death / 10 |
| --- | --- | ---: | ---: | ---: | ---: |
| low_load | shortest | 98.52 ± 0.84 | 3.60 | 1.265 | 0 |
| low_load | reactive | 98.61 ± 0.70 | 3.60 | 1.264 | 0 |
| low_load | predictive | 98.68 ± 0.80 | 3.61 | 1.263 | 0 |
| medium_load | shortest | 97.92 ± 1.21 | 4.35 | 0.855 | 4 |
| medium_load | reactive | 98.22 ± 1.03 | 4.51 | 0.854 | 1 |
| medium_load | predictive | 98.50 ± 0.64 | 4.55 | 0.851 | 0 |
| high_load | shortest | 73.08 ± 3.46 | 16.45 | 0.781 | 10 |
| high_load | reactive | 74.82 ± 3.11 | 15.90 | 0.777 | 10 |
| high_load | predictive | 75.05 ± 2.42 | 16.06 | 0.775 | 10 |
| burst | shortest | 73.26 ± 5.88 | 15.38 | 0.858 | 8 |
| burst | reactive | 75.51 ± 5.03 | 13.84 | 0.844 | 8 |
| burst | predictive | 75.85 ± 4.62 | 13.43 | 0.842 | 6 |
| failure | shortest | 79.15 ± 4.54 | 4.70 | 0.987 | 0 |
| failure | reactive | 81.74 ± 4.31 | 4.75 | 0.964 | 0 |
| failure | predictive | 81.83 ± 4.71 | 4.83 | 0.962 | 0 |

The predictive mean gain beyond reactive routing is small in several cases. No significance test establishes a universal improvement. The seed-42 dashboard example has lower predictive delivery than reactive delivery. Report all results and limitations.

Energy units are synthetic. A missing first battery death is censored at 400 seconds. The source CSV and JSON are authoritative.
