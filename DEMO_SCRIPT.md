# Five-minute review demonstration

## Before the reviewer arrives

- Extract the project, start app.py, and open http://127.0.0.1:8000.
- Keep default settings: 30 sensors, 400 seconds, burst, seed 42, H 40, alpha .35.
- Click Run and make sure all three strategy buttons work.
- Keep MODEL.md and VIVA_GUIDE.md available. Save a copy on a teammate's laptop.
- Do not change parameters immediately before the review without checking the new result.

## 0:00-0:40 — Problem

"Battery-powered sensors forward one another's data to a gateway. A heavily used
relay can die early and affect upstream devices. We investigate whether a short
energy forecast can help select a better next hop before that happens."

Point out the gateway at the top, sensor nodes, physical links, and selected arrows.
Explain that sensor 1 has a smaller battery in every strategy.

## 0:40-1:30 — Algorithm

Choose Predictive. Click a node and point to current energy, drain rate, forecast,
queue, and route. Say:

"Every five seconds a sensor smooths its recent energy drain. Every ten seconds it
advertises that state. A neighbor estimates future energy and combines the energy
risk with link loss and queue load. We only forward toward a lower initial level,
which prevents loops. Hysteresis avoids switching for tiny score improvements."

## 1:30-2:20 — Replay

Click Play, then use the slider to move through the middle third. Point out that
the traffic probability triples in this interval. Click several nodes and show
their route-change logs. Show Shortest-hop and Reactive at the same replay time.
The displayed simulation is computed first and then replayed; it is not live hardware.

## 2:20-3:20 — Results

Move the slider to 400 s. The final comparison table always shows the complete run.

"In this seed, the predictive policy's first battery death is later than shortest-hop,
but the reactive policy is later still. Predictive mean delay is lower, while its
demand delivery is slightly lower. We don't claim every metric improves."

Use the exact table on screen rather than memorizing a percentage improvement.
Distinguish demand delivery from packet delivery if asked.

## 3:20-4:10 — Repeated experiments

Open results/FINDINGS.md. Explain that these are actual repeated runs, not mocked
numbers. The five scenarios are low, medium and high steady loads, a burst, and an injected relay
failure. Seeds 0-9 are paired across strategies, giving 150 runs.

"The aggregate behavior is more informative than one seed. We report variability
and have not established statistical significance."

## 4:10-5:00 — Limitations and conclusion

"This is a functional algorithm prototype. Energy costs are illustrative; RF
contention is simplified and initial levels are fixed. A deployment would require
a calibrated energy model, full protocol integration, and realistic wireless tests.
Our result is an inspectable implementation and comparison of prediction-aware
routing, including its trade-offs."

## If the reviewer requests a live change

- Change the seed to another integer, click Run, and inspect the result honestly.
- Change the scenario to relay failure. At 200 s, sensor 1 is forced offline if alive.
- Set H to 20 versus 80 and explain that responsiveness and prediction risk change.
- Never promise that a new parameter setting must produce an improvement.

## Fallback and troubleshooting

If the server fails, open static/index.html. The bundled example still supports
replay, inspection, strategy switching, and export. State that this fallback is a
precomputed example. It cannot run fresh parameters without the Python server.

If a route disappears, inspect offline nodes and stale observations rather than
assuming a UI bug. If demand delivery falls, check offered load, source availability,
queueing, retries, and pending packets. These are modeled behaviors.
