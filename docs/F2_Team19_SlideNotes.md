# Slide explanation notes

## Slide 1
Introduce the three team members. This is a custom Python simulation and dashboard. It does not implement a full wireless stack or standard RPL. The evaluation uses synthetic modeled energy.

## Slide 2
Source: our simulator model and RFC 6550 background, https://www.rfc-editor.org/rfc/rfc6550.html. Explain sensors, relays, gateway, and why a relay affects upstream sources.

## Slide 3
Background: RFC 6550, https://www.rfc-editor.org/rfc/rfc6550.html; RFC 6551, https://www.rfc-editor.org/rfc/rfc6551.html; RFC 6719, https://www.rfc-editor.org/rfc/rfc6719.html. The two implemented baselines are custom controls, not standard RPL or MRHOF implementations.

## Slide 4
This is an editable algorithm architecture diagram, not a hardware deployment. The simulator has global state for execution and visualization. Parent choice reads local received observations. Initial BFS levels are centrally computed.

## Slide 5
Background: NIST/SEMATECH e-Handbook of Statistical Methods, Single Exponential Smoothing, https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm. This implementation smooths recent energy drain, then linearly projects remaining energy. It does not train a neural network.

## Slide 6
Our cost is a local normalized score, not an accumulated end-to-end path metric. Strict decreasing initial levels prevent loops but exclude some post-failure detours. All terms are clamped to comparable ranges. Gateway eligibility is preferred.

## Slide 7
Illustrative arithmetic, not a trace quoted from experiments. Both capacities are 100 EU, advertisement age is zero, H=40 s, queue limit=20. Reactive cost prefers A (.1800 versus .2725). Predictive cost prefers B (.4140 versus .2985). The improvement .1155 exceeds hysteresis .06.

## Slide 8
Runtime dependencies: Python standard library only. Source: Config and Simulation in simulator.py, app.py, static/index.html. Energy units are illustrative. One-second service slots are not measured radio transmission times.

## Slide 9
Source: experiments.py and results/experiments.csv. Five scenarios times ten matched seeds times three policies equals 150 runs. Use sample standard deviation. No formal significance test is claimed.

## Slide 10
Actual means and sample SD from results/summary.json. Values are percent of all scheduled sensor readings, including unavailable source demand. The improvement beyond reactive routing is smaller than the gain relative to shortest-hop.

## Slide 11
Source: results/summary.json, means over ten matched seeds per load. The chart displays means only. Sample SD is in the preceding table and report plots. Literal chart data are embedded for editability.

## Slide 12
Source: results/summary.json and results/F2_Team19_Simulation.json. In repeated burst runs, predictive mean delay is 13.43 seconds versus 15.38 seconds for shortest-hop. The default seed-42 example is a separate run and shows why no universal improvement is claimed.

## Slide 13
Source: MODEL.md and actual experiments. No real RF, hardware calibration, or protocol compliance is claimed. Tests verify algorithm and accounting invariants, not the fidelity of a complete wireless network stack.

## Slide 14
References: [1] T. Winter et al., RPL, RFC 6550, March 2012, doi:10.17487/RFC6550. [2] J. P. Vasseur et al., Routing Metrics Used for Path Calculation in Low-Power and Lossy Networks, RFC 6551, March 2012, doi:10.17487/RFC6551. [3] O. Gnawali and P. Levis, MRHOF, RFC 6719, September 2012, doi:10.17487/RFC6719. [4] NIST/SEMATECH e-Handbook, Single Exponential Smoothing, https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm. Live demo: run app.py, switch strategies, alter a parameter, inspect decisions, and explain actual results.
