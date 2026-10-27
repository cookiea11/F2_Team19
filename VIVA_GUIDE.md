# PAMR: fundamentals and viva preparation

Read this in order. Understand the worked example and the limitations before
memorizing answers. The implementation is a simulation prototype with a lightweight
statistical predictor, not a physical deployment or a trained deep-learning system.

## 1. Your explanation in 30 seconds

"Our project simulates battery-powered IoT sensors forwarding readings through a
mesh to a gateway. A frequently used relay can drain early and disrupt other sensors.
We estimate each node's recent energy drain using exponential smoothing, forecast
its near-future remaining energy, and select a next hop using that forecast, link
reliability, and queue load. We compare this with shortest-hop and reactive routing
under identical conditions. The goal is to investigate lifetime and delivery trade-offs."

## 2. Understand every word in the title

| Term | Meaning in our project |
| --- | --- |
| Predictive | Forecast energy H seconds ahead using historical drain |
| Adaptive | Change the next-hop parent when a sufficiently better candidate appears |
| Mesh | Sensors can have several physical neighbor links and relay one another's packets |
| Routing | Decide which neighbor receives the packet next on its way to the gateway |
| Protocol | Rules for status exchange, candidate eligibility, parent choice, and stale information |
| Energy-constrained | Sensors have finite modeled battery budgets |
| IoT | Small connected devices generating measurements, represented here by simulated sensors |

The physical graph is a mesh. The active forwarding graph is directed and acyclic,
with one selected parent per live sensor. Do not say every sensor sends directly to
the gateway or that all mesh links carry each packet simultaneously.

## 3. Networking fundamentals you must know

### Node, link, packet, source, relay, sink

A **node** is a device. A **link** allows two neighboring devices to communicate.
A **packet** is a unit of data. A **source** generates a reading. A **relay** forwards
another device's packet. The **sink/gateway** collects readings. One sensor can be
both source and relay. Gateway 0 has external power in our model.

### Routing versus forwarding

Routing chooses or updates the next-hop rule. Forwarding applies that rule to a
particular queued packet. `choose_parent()` is routing; `forward()` handles packet
movement and transmission attempts.

### Single-hop versus multi-hop

Single-hop delivery goes directly from source to destination. Multi-hop delivery
uses intermediate relays. For example, 12 → 4 → 1 → gateway is three hops. Multi-hop
can extend coverage but adds transmission, reception, waiting, and failure points.
This project only creates physical links within radio range; it does not model
variable transmit power or prove multi-hop always saves total energy.

### Why shortest path is not sufficient

Minimum-hop routing minimizes the number of forwarding links on the initial graph.
It can repeatedly choose the same relay and exhaust it. A route with fewer hops
is not automatically the route with the best battery balance or reliability.
Our first version compares alternate parents within a minimum-hop scaffold; it does
not consider longer energy-saving detours. Say this explicitly when asked.

### Why nodes near the gateway are important

They may forward traffic from many upstream sensors, creating a bottleneck. Their
battery exhaustion can affect much more than their own measurements. Load balancing
can help when useful alternatives exist; it cannot create extra gateway capacity.

### Packet loss, retries, and queues

Real links may fail. We model each attempt with a success probability. A failed
attempt still spends energy and may be retried. A finite queue stores packets
waiting for service. When arrivals exceed forwarding capacity, queues grow, delay
increases, and buffers may overflow. A packet without a route waits until a route
appears or its TTL expires. At most three attempts are allowed per current hop.

### Latency, throughput, and packet delivery

- **Latency:** time from packet creation to gateway arrival.
- **Throughput:** delivered packets or bits per unit time. Our raw delivered count
  divided by run duration gives a packet-rate throughput; it is not a bit-rate claim.
- **Packet delivery ratio:** delivered / actually generated packets.
- **Demand delivery ratio:** delivered / all scheduled readings, including times
  when a source is offline. This prevents dead sources from disappearing from the workload.

Delay is measured only on delivered packets. Always discuss delivery and delay
together; losing slow packets can make the surviving packets' mean delay look better.

### OSI layer and the dashboard connection

The routing decision is a **network-layer concept**. Our simulator represents this
decision without implementing every packet header and layer. It uses abstract data
packets, not real UDP/IPv6 sensor traffic. The browser uses HTTP over the computer's
normal network stack to reach the local Python dashboard server. That HTTP connection
is separate from the simulated sensor network.

### Mesh, tree, and DAG

A mesh offers multiple physical links. A tree has a unique path toward its root.
A directed acyclic graph (DAG) has directed edges but no directed cycles. Our initial
level constraints create a DAG of possible parent edges; selecting one parent per
node gives an active gateway-rooted forwarding structure where connectivity exists.

## 4. The algorithm, step by step

1. Create a connected physical graph and assign initial BFS levels from gateway 0.
2. Initialize finite sensor batteries. Sensor 1 has a deliberately smaller capacity.
3. Generate scheduled sensor readings and enqueue packets from live sensors.
4. Measure energy consumption every five seconds and update smoothed drain.
5. Broadcast status every ten seconds. Neighbors keep successfully received records.
6. Every five seconds, examine fresh lower-level neighbor records.
7. Predict candidate energy, compute costs, and change parent if worthwhile.
8. Forward queued packets, deduct energy, and handle losses, retries, and failures.
9. Record packet, energy, routing, and prediction metrics.

This is the conceptual flow; see `step()` for exact within-slot ordering.

### Energy-drain estimate

Recent drain = (previous sampled energy − current energy) / elapsed seconds.

Smoothed drain:

```
d_new = alpha * recent_drain + (1 - alpha) * d_old
```

With alpha 0.35, recent drain 0.5 EU/s, and previous drain 0.2 EU/s:

```
d_new = 0.35*0.5 + 0.65*0.2 = 0.305 EU/s
```

EWMA means **exponentially weighted moving average**. Repeated substitution gives
progressively older measurements progressively less weight. A larger alpha reacts
more quickly and is noisier. A smaller alpha smooths more but reacts slowly.
We initialize the estimate at zero, so early estimates have a warm-up bias.

### Forecast

```
future_energy = max(0, energy - H * smoothed_drain)
```

For a received advertisement, account for its age as well:

```
future_energy = max(0, advertised_energy - (H + advertisement_age) * advertised_drain)
```

This assumes recent drain approximately continues. It is not a guarantee about
future battery levels. No future simulator values are read to make the prediction.

### Cost

```
energy_risk = 1 - future_energy / initial_capacity
link_loss = 1 - link_success_probability
queue_fraction = queue_length / queue_limit

cost = 0.65*energy_risk + 0.20*link_loss + 0.15*queue_fraction
```

The implementation clamps fractions to valid bounds. Lower cost is better. It
compares candidate next hops, not the entire end-to-end route cost. Weights are
chosen settings, not learned values. The reactive baseline substitutes current
advertised energy for future energy.

### Worked example: why prediction changes the choice

Suppose two fresh candidate advertisements have:

| Attribute | Relay A | Relay B |
| --- | ---: | ---: |
| Capacity | 100 EU | 100 EU |
| Current energy | 80 EU | 65 EU |
| Smoothed drain | 0.9 EU/s | 0.1 EU/s |
| Link success probability | 0.90 | 0.85 |
| Queue length (limit 20) | 4 | 2 |

With H = 40 seconds:

- A predicted energy = 80 − 40×0.9 = **44 EU**.
- B predicted energy = 65 − 40×0.1 = **61 EU**.

Reactive scores:

```
A = .65*(1-.80) + .20*(1-.90) + .15*(4/20) = .1800
B = .65*(1-.65) + .20*(1-.85) + .15*(2/20) = .2725
```

Reactive routing prefers **A** because it currently looks stronger.

Predictive scores:

```
A = .65*(1-.44) + .20*(1-.90) + .15*(4/20) = .4140
B = .65*(1-.61) + .20*(1-.85) + .15*(2/20) = .2985
```

PAMR prefers **B** because its recent drain is much lower. If A is the current
parent, improvement is .4140 − .2985 = **.1155**, greater than the .06 hysteresis
margin, so it switches. These are illustrative arithmetic inputs, not a quoted
trace from the bundled experiment.

### Loop prevention

Initial gateway level is 0. Each transmission goes to a strictly lower level.
A sequence of strictly decreasing nonnegative integers cannot return to its
starting value, so a forwarding loop is impossible under this constraint.
The price is reduced flexibility: some surviving physical paths cannot be used.

### Hysteresis

Keep the current valid parent unless the alternative improves cost by more than
0.06. This prevents small metric fluctuations from triggering repeated switches.
If the current parent becomes invalid, replace it without requiring that margin.
Hysteresis is an absolute normalized-score difference here, not a 6% relative gain.

## 5. Baselines and experiment interpretation

| Strategy | Main decision |
| --- | --- |
| Shortest-hop | Move down initial levels; prefer better link quality among ties |
| Reactive energy-aware | Evaluate current advertised energy, link loss, and queue |
| Predictive adaptive | Replace current energy with age-corrected forecast energy |

The reactive baseline is essential. Without it, an improvement over shortest-hop
could come from considering energy at all, rather than from predicting it.

All algorithms share the topology, traffic schedule, capacities, link probabilities,
control interval, queue rules, energy costs, and duration. They differ in next-hop
selection. Random draws use event-based seeded hashes, preserving offered traffic
even when routes differ.

The supplied results include 10 seeds per scenario, five scenarios, and three
strategies: **150 actual simulation runs**. The dashboard seed 42 is an additional
example. The report gives sample means and standard deviations; no statistical
significance or universal superiority is established.

Default burst run, seed 42 (rounding may occur):

| Metric | Shortest-hop | Reactive | Predictive |
| --- | ---: | ---: | ---: |
| Demand delivery | 81.98% | 82.32% | 80.94% |
| First battery death | 347 s | 375 s | 361 s |
| Mean delivered-packet delay | 13.86 s | 13.54 s | 13.13 s |

Say: **"In this example, prediction delayed the first death relative to shortest-hop
and reduced delivered-packet mean delay, but delivered fewer scheduled readings.
Reactive routing performed better on delivery and first-death time. We therefore
evaluate repeated scenarios and report trade-offs."**

Do not say "our algorithm always wins" or hide the reactive result. A defensible
engineering conclusion is stronger than an unsupported improvement percentage.

## 6. What to say about novelty and limitations

The implemented contribution is combining a lightweight energy forecast, local
neighbor information, normalized scoring, and route hysteresis in an inspectable
experimental comparison. Prediction-aware and energy-aware routing are existing
research areas. We have not established publication-level novelty.

Main limitations:

1. Synthetic energy units; no measured hardware power profile.
2. Independent links; no RF interference or real MAC contention.
3. Fixed initial levels; no distributed level repair or longer detours.
4. Known fixed link-quality estimates; no online estimation from acknowledgements.
5. One gateway and static positions; no mobility or general peer-to-peer routing.
6. Fixed weights and horizon; no parameter optimization or broad sensitivity study.
7. Small synthetic experiments; results need validation in a standard simulator or hardware.

Good next steps: calibrate a device energy model, implement realistic MAC behavior,
evaluate larger and more varied topologies, tune parameters on separate validation
scenarios, and consider a genuine Contiki-NG/RPL implementation.

## 7. Likely viva questions and direct answers

**1. What problem are you solving?**
Early relay exhaustion in battery-powered multi-hop sensor networks, where repeatedly
using a convenient route can disconnect useful traffic.

**2. What exactly is predicted?**
A neighbor's remaining energy H seconds ahead, using its last advertised remaining
energy and smoothed consumption rate. We do not predict the complete traffic sequence.

**3. What exactly adapts?**
The selected next-hop parent. We do not automatically learn the weights or change radio power.

**4. How is this different from checking current battery?**
Equal or high current batteries can hide different drain rates. Prediction penalizes
a currently strong relay if it is consuming energy rapidly. Show the worked example.

**5. Is EWMA machine learning?**
We describe it as lightweight statistical prediction. It has no training dataset,
learned model weights, or neural network. Calling it deep learning would be inaccurate.

**6. Why not use an LSTM or reinforcement learning?**
They add data, training, validation, and compute requirements. A transparent scalar
forecast is feasible for constrained nodes and gives a clear baseline. More complex
models would need evidence of benefit that exceeds their overhead.

**7. Why alpha 0.35 and horizon 40 seconds?**
They are reasonable demonstration defaults, not proven optimal values. Alpha controls
responsiveness; horizon controls how far ahead energy is projected. The dashboard
allows changing them. A proper parameter study is future work.

**8. What if traffic changes suddenly?**
The recent-drain assumption becomes less accurate. EWMA catches up as new samples
arrive, but there is lag. Very long horizons can amplify errors and cause poor choices.

**9. How does a node learn its neighbor's energy?**
Through received periodic status advertisements. The node stores the advertised
energy, capacity, drain, queue length, and timestamp. Records can be lost or become stale.

**10. Is this centralized or distributed?**
Execution occurs in one simulator, and initial levels are centrally computed.
The parent-choice logic uses local received neighbor records. We have not implemented
a complete distributed initialization or a deployable protocol stack.

**11. How do you prevent loops?**
Forward only to a lower fixed gateway level. Levels strictly decrease on each hop.

**12. What is BFS doing here?**
Breadth-first search assigns minimum-hop levels in an unweighted initial graph.
It is initialization, not the energy predictor. Network-wide BFS is O(V+E) once
the graph exists; generating all possible distance-based links is O(V²).

**13. Why are there no hop-count weights in your final cost?**
The initial level restriction already constrains candidates to minimum-hop progress.
An extra hop term would be constant among eligible parents in this graph and would
not change their ranking.

**14. What if all lower-level parents disappear?**
Packets wait for a valid fresh route until the TTL expires, or are lost when their
node fails. This version cannot take a sideways/upward detour or rebuild levels.

**15. Why not simply avoid every low-battery node?**
A hard exclusion can unnecessarily partition the network. Our version uses a soft
energy penalty and may still select a risky node if alternatives are worse or absent.

**16. What is hysteresis, and what happens without it?**
A switching margin that avoids frequent route changes for tiny score differences.
Without it, changing energy and queue observations could cause route oscillation.

**17. What prevents unlimited retries?**
A maximum of three attempts on the current hop, a finite queue, and an overall
packet TTL. A parent change resets that hop-attempt counter, but not the packet TTL.

**18. What does link quality mean?**
The modeled probability of successful delivery in one link attempt. Routing receives
that fixed estimate. In hardware it could be estimated from acknowledgement statistics.

**19. Is your link metric ETX?**
No. We use 1 − success probability as a normalized loss term. ETX is an expected
transmission count metric; its derivation and acknowledgement model are different.

**20. Is high battery enough to choose a route?**
No. A high-energy neighbor may have a poor link or a congested queue. The cost trades
off these factors, subject to loop-free eligibility.

**21. Why normalize the metrics?**
To put different quantities on comparable scales before weighting them. Otherwise
one quantity could dominate merely because of its units or numeric range.

**22. Are the weights optimal?**
No. They encode our energy-first design preference. Sensitivity testing and tuning
on held-out scenarios would be needed before making stronger claims.

**23. Why is the sink externally powered?**
It models a gateway with a separate power supply and focuses analysis on sensor
batteries. If the gateway were constrained, its energy and bottleneck behavior
would need to be included explicitly.

**24. How do you calculate energy?**
Deduct fixed illustrative costs for data transmission and reception, idle operation,
and control broadcasting/reception. Energy cannot go below zero. These are not joules.

**25. How do you know the simulator is not creating or losing packets accidentally?**
We check generated = delivered + dropped + pending, and offered = generated +
source unavailable. Unit checks also verify per-node energy conservation.

**26. Why not just compare battery remaining at the end?**
A protocol that delivers almost nothing may consume little energy. Energy must be
considered alongside delivered demand, delay, and availability. EU per delivered
packet is more informative than battery remaining alone.

**27. What is network lifetime?**
It depends on the application. We explicitly report time to first battery death,
alongside online sensors and delivered demand. We do not equate that single metric
with all definitions of useful network lifetime.

**28. What does 'no first death' mean?**
No battery depletion was observed before the experiment ended. It is a censored
observation, not zero lifetime or infinite lifetime.

**29. Why do you use several random seeds?**
One topology and traffic realization may be unusually favorable. Matched seeds
show variability while keeping each algorithm comparison on equivalent inputs.

**30. Does the algorithm always improve performance?**
No. Prediction error, stale information, queue behavior, and switching can reduce
performance. Our supplied runs contain both improvements and trade-offs.

**31. Can you claim statistical significance?**
No. We provide means and sample standard deviations from ten matched seeds, without
a formal significance test. The observed differences may be small relative to variation.

**32. Is your comparison fair if shortest-hop also sends energy advertisements?**
It isolates the decision rule under common monitoring costs. It is not an end-to-end
comparison against the most optimized low-overhead shortest-hop implementation.
Separate optimized-control comparisons would be needed for that broader claim.

**33. What is the prediction error metric?**
Mean absolute error between an issued energy forecast and the node's later actual
energy. Only matured forecasts count. Errors are in EU, with normalized errors also
exported. Routes can change after the forecast, so these are actual-run errors.

**34. Why can making a prediction affect its accuracy?**
If the forecast causes traffic to leave a relay, that relay's subsequent drain falls.
The intervention changes the trajectory being predicted. Our metric is not a clean
counterfactual evaluation of an unchanged routing policy.

**35. Is this RPL? How does it relate?**
RPL is an IETF protocol for low-power and lossy networks that organizes routing
using a destination-oriented DAG, Rank, and objective functions. We borrow the idea
of loop-free progress toward a root, but do not implement RPL messages, full Rank
rules, repairs, or IPv6 behavior. Do not call the shortest-hop baseline standard RPL.

**36. Why use a custom Python simulator?**
It makes the routing policy transparent and quick to inspect and compare. The
trade-off is simplified radio and protocol behavior. A standard IoT simulator or
hardware testbed would provide a stronger next validation step.

**37. What is the per-node computation overhead?**
O(1) for its scalar drain update and forecast; O(d) to score d neighbor candidates,
with O(d) neighbor storage. Dashboard history is simulator overhead, not device overhead.

**38. What happens if a relay fails abruptly?**
Packets sent to it fail. Its advertisements stop; cached observations expire and
another eligible parent can be selected. Recovery is not instantaneous. The failure
scenario demonstrates this, within the fixed-level limitation.

**39. What real applications could use this idea?**
Battery-powered environmental, agricultural, or building-monitoring sensor networks
with multi-hop forwarding. Deployment suitability would require measured power,
realistic link behavior, and application-specific reliability validation.

**40. What would you improve next?**
Calibrated energy, realistic contention, online link estimates, distributed level
repair, parameter sensitivity, and evaluation in an established networking simulator.

## 8. Code-reading map for an unexpected question

| Question | Look at |
| --- | --- |
| Where do neighbors and levels come from? | make_topology(), levels_for() |
| Where is the prediction made? | update_predictor(), score() |
| Where is the next hop chosen? | candidates(), choose_parent() |
| Where are control messages handled? | advertise() |
| Where is battery deducted? | spend() |
| Where are losses and retries modeled? | forward() |
| Where are packet totals checked? | End of run() |
| Where are repeated experiments summarized? | experiments.py |
| Where does the browser get a fresh simulation? | POST /api/simulate in app.py |

## 9. Team rehearsal tonight

Each person should answer the 30-second explanation without reading. Then each
explains their own source functions and asks the others five questions from section 7.
Everyone should calculate the worked example by hand once.

Avoid statements you cannot support:

- "We use deep learning." → "We use EWMA-based statistical energy prediction."
- "It always saves 30% energy." → Quote the actual metric and experiment conditions.
- "These are real sensor measurements." → "These are synthetic simulation results."
- "This is a full RPL implementation." → "It is an RPL-inspired experimental policy."
- "Prediction prevents all failures." → "It can redistribute forwarding load when alternatives exist."

## Background references

- RFC 6550: https://www.rfc-editor.org/rfc/rfc6550.html
- NIST exponential smoothing: https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm

The formulas, limits, and observations in this guide describe the delivered code.
The references support background concepts, not a claim that our custom algorithm
is standardized or proven novel.
