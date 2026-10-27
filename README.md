# F2 Team 19 — Predictive Adaptive Mesh Routing

**BCSE308P Computer Networks Lab, Fall Semester 2026-2027**

A runnable Python prototype for energy-constrained IoT mesh routing. It forecasts
remaining battery energy and adapts next-hop selection, with an interactive dashboard
and a reproducible comparison against shortest-hop and reactive energy-aware routing.

## Team

Listed in register-number order:

| Register number | Name |
| --- | --- |
| 24BCE0817 | Siddhi Gulati |
| 24BCT0084 | Harshitha Nethi |
| 24BKT0146 | Saamiya Siddique |

## Requirements

Python **3.10 or later** and a modern browser. The application, experiments, and
unit tests require no third-party Python packages, database, API key, or hardware.
Internet is unnecessary for local simulation. Optional screenshot capture has its
own dependencies in requirements-evidence.txt.

## Installation and execution

Extract the entire archive. Open a terminal in this folder and run:

```sh
python app.py
```

Use `python3` on Linux/macOS or `py -3` on Windows if necessary. Open
**http://127.0.0.1:8000**, click **Run all three strategies**, and click **Play**.
Select a sensor to inspect battery, forecast, queue, route, and decisions. Changing
a form value requires clicking Run again. Stop with Ctrl+C.

For another port: `python app.py --port 8001`. Windows launcher: `launch.bat`.
Linux/macOS launcher: `sh launch.sh`.

### Offline fallback

Open static/index.html directly. The bundled seed-42 result supports replay,
inspection, policy switching, and exports. It is a precomputed example. Start the
Python server to compute fresh settings. Keep index.html and demo_data.js together.

## Simulation and configuration files

```sh
python scripts/run_simulation.py
```

This reads simulation/F2_Team19_Config.json, compares all policies, and writes
results/F2_Team19_Simulation.json plus simulation/F2_Team19_Topology.json.

This project uses a custom Python simulator. A Packet Tracer `.pkt` file is not
applicable. The source, saved configuration, topology, and results are the network
simulation files. Do not rename JSON files to `.pkt`.

## Testing and reproducible evaluation

```sh
python -m unittest -v
python experiments.py --seeds 10
```

The recorded suite has **14 passing checks**. Five cases × ten matched seeds ×
three policies produce **150 simulation runs**. The command writes per-run rows to
results/experiments.csv and mean/sample-SD summaries to results/summary.json.

| Case | Base probability / sensor / second | Event |
| --- | ---: | --- |
| Low steady load | 0.015 | None |
| Medium steady load | 0.030 | None |
| High steady load | 0.060 | None |
| Burst | 0.030 | Tripled probability in middle third |
| Relay failure | 0.030 | Relay 1 forced offline at 200 s if alive |

Use `--scenario low_load`, `medium_load`, `high_load`, `burst`, or `failure` for
one case. `steady` is an alias for medium load. Repeated seeds 0-9 are distinct
from demonstration seed 42.

## Expected results

Mean ± sample SD of scheduled readings delivered, in percent:

| Case | Shortest-hop | Reactive | Predictive |
| --- | ---: | ---: | ---: |
| Low | 98.52 ± 0.84 | 98.61 ± 0.70 | 98.68 ± 0.80 |
| Medium | 97.92 ± 1.21 | 98.22 ± 1.03 | 98.50 ± 0.64 |
| High | 73.08 ± 3.46 | 74.82 ± 3.11 | 75.05 ± 2.42 |
| Burst | 73.26 ± 5.88 | 75.51 ± 5.03 | 75.85 ± 4.62 |
| Failure | 79.15 ± 4.54 | 81.74 ± 4.31 | 81.83 ± 4.71 |

![Actual simulation delivery measurements](results/figures/F2_Team19_delivery.png)

The default seed-42 burst run is a counterexample: predictive delivery is 80.94%,
while reactive delivery is 82.32%. Prediction does not improve every metric or run.
No statistical-significance or optimality claim is made. Plots are measurement
figures, not dashboard screenshots.

## Actual dashboard screenshots

Cloud-browser restrictions prevented opening the local project here. Generate real
screenshots on your laptop before submission:

```sh
python -m pip install -r requirements-evidence.txt
python -m playwright install chromium
python scripts/capture_screenshots.py
```

The optional script captures five actual browser views in screenshots/ and checks
for browser JavaScript errors. Manual screenshots are also acceptable. Commit them.

## Repository organization

| Path | Purpose |
| --- | --- |
| simulator.py, app.py, experiments.py | Complete executable simulator and server source |
| static/ | Dashboard and bundled offline example |
| test_simulator.py, test_http.py | Correctness and real HTTP integration checks |
| simulation/ | Named saved configuration and physical topology |
| results/ | Per-run measurements, aggregates, demonstration and figures |
| screenshots/ | Capture instructions and real images after local capture |
| tests/ | Recorded verification output |
| docs/F2_Team19_Report.pdf | Assignment 8 report |
| docs/F2_Team19_PPT.pptx | Assignment 9 presentation |
| docs/F2_Team19_Report_Print.html | Printable source requesting Times New Roman |
| docs/F2_Team19_SubmissionChecklist.md | Rubric mapping and outstanding steps |
| docs/F2_Team19_GitHubSetup.md | Publishing and faculty-access procedure |
| MODEL.md | Equations, constants and assumptions |
| VIVA_GUIDE.md, DEMO_SCRIPT.md | Fundamentals, forty answers and five-minute demo |
| .github/workflows/verify.yml | Automated tests and small repeatability run |

## Suggested explanation ownership

This is a rehearsal split, not an assertion about historical contributions.

| Member | Explain |
| --- | --- |
| Siddhi Gulati | Topology, packets, forwarding, queues and energy accounting |
| Harshitha Nethi | EWMA, score, observations, loop prevention and hysteresis |
| Saamiya Siddique | Dashboard, experiments, metrics and result interpretation |

Everyone must explain the core prediction and score. Read the worked example.

## Submission and GitHub

Assignment 8: docs/F2_Team19_Report.pdf. Assignment 9: docs/F2_Team19_PPT.pptx.
Assignment 10: the actual accessible GitHub URL after publishing this folder.

This repository is prepared locally, not published to a GitHub account here.
Follow docs/F2_Team19_GitHubSetup.md. Add screenshots, check typography and
signatures, and verify faculty access before submission.

## Scope and attribution

The model uses illustrative EU, independent links, fixed initial BFS levels, and
one powered gateway. It implements abstract sensor-to-gateway packets rather than
a full RPL/IPv6/wireless stack. A real deployment needs calibrated energy and radio tests.

The starter implementation and supporting drafts use AI assistance. The submitting
team must inspect, run, understand, and adapt the work as course policy requires,
and describe its contributions accurately. No signatures, hardware measurements,
dashboard screenshots, or GitHub publication have been fabricated.
