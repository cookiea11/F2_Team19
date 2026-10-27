from pathlib import Path
import sys, json, csv, math, platform
from html import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Preformatted, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs'; PLOTS=ROOT/'results/figures'
OUT.mkdir(exist_ok=True);PLOTS.mkdir(exist_ok=True)
summary=json.loads((ROOT/'results/summary.json').read_text())
lookup={(r['scenario'],r['algorithm']):r for r in summary}
demo=json.loads((ROOT/'results/F2_Team19_Simulation.json').read_text())
meta=json.loads((ROOT/'team.json').read_text())
ALGS=['shortest','reactive','predictive'];COLORS=['#6d7e89','#4d72ca','#087f8c'];LABELS=['Shortest-hop','Reactive','Predictive']
CASES=['low_load','medium_load','high_load','burst','failure']
NAMES={'low_load':'S1 Low load','medium_load':'S2 Medium load','high_load':'S3 High load','burst':'S4 Traffic burst','failure':'S5 Relay failure'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})

# Plot only actual simulation quantities. These figures are not dashboard screenshots.
for metric, ylabel, filename, scale in [('demand_delivery_ratio','Scheduled readings delivered (%)','delivery',100),('average_delay','Mean delivered-packet delay (s)','delay',1),('energy_per_delivered','Sensor EU per delivered packet','efficiency',1)]:
 fig,ax=plt.subplots(figsize=(8.3,3.4),layout='constrained')
 xs=np.arange(len(CASES))
 for i,a in enumerate(ALGS):
  means=[lookup[(c,a)][metric+'_mean']*scale for c in CASES]
  sd=[lookup[(c,a)][metric+'_sd']*scale for c in CASES]
  ax.bar(xs+(i-1)*.24,means,width=.23,label=LABELS[i],color=COLORS[i],yerr=sd,capsize=3,error_kw={'elinewidth':.8})
 ax.set_xticks(xs,['Low','Medium','High','Burst','Failure']);ax.set_ylabel(ylabel)
 ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.legend(loc='upper center',bbox_to_anchor=(.5,1.19),ncol=3,frameon=False)
 if scale==100:ax.set_ylim(0,110)
 fig.savefig(PLOTS/f'F2_Team19_{filename}.png',dpi=180);plt.close(fig)
fig,ax=plt.subplots(figsize=(7.8,4),layout='constrained')
for link in demo['topology']['links']:
 a=demo['topology']['nodes'][link['a']];b=demo['topology']['nodes'][link['b']]
 ax.plot([a['x'],b['x']],[a['y'],b['y']],color='#d5dfdf',lw=.7,zorder=1)
for n in demo['topology']['nodes']:
 color='#192d3b' if n['id']==0 else '#d6802b' if n['id']==1 else '#087f8c'
 ax.scatter(n['x'],n['y'],s=230 if n['id']==0 else 150,color=color,zorder=2,edgecolors='white')
 ax.text(n['x'],n['y'],str(n['id']),color='white',ha='center',va='center',fontsize=7.5,zorder=3)
ax.invert_yaxis();ax.set_xlabel('Abstract x coordinate');ax.set_ylabel('Abstract y coordinate');ax.set_title('Seed 42 physical mesh: 30 sensors and gateway 0',fontsize=11)
fig.savefig(PLOTS/'F2_Team19_topology.png',dpi=180);plt.close(fig)

# Use real Times New Roman when installed; keep an explicit record of substitution.
font_candidates=[Path('C:/Windows/Fonts/times.ttf'),Path('/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf'),Path('/usr/share/fonts/truetype/msttcorefonts/times.ttf')]
regular=next((p for p in font_candidates if p.exists()),None)
if regular:
 pdfmetrics.registerFont(TTFont('TNR',str(regular)));FONT='TNR'
 bold_candidates=[regular.parent/'timesbd.ttf',regular.parent/'Times_New_Roman_Bold.ttf']
 bold_file=next((p for p in bold_candidates if p.exists()),None)
 if bold_file:
  pdfmetrics.registerFont(TTFont('TNRBold',str(bold_file)));BOLD='TNRBold'
 else:BOLD='Times-Bold'
else:FONT='Times-Roman';BOLD='Times-Bold'
pdfmetrics.registerFontFamily(FONT,normal=FONT,bold=BOLD,italic=FONT,boldItalic=BOLD)
BASE=ParagraphStyle('Body',fontName=FONT,fontSize=12,leading=13.8,spaceAfter=8,alignment=TA_JUSTIFY)
H=ParagraphStyle('Heading',parent=BASE,fontName=BOLD,fontSize=14,leading=21,spaceBefore=9,spaceAfter=10,alignment=0,keepWithNext=True)
SUB=ParagraphStyle('Subheading',parent=BASE,fontName=BOLD,fontSize=12,leading=18,spaceBefore=6,spaceAfter=6,alignment=0,keepWithNext=True)
SMALL=ParagraphStyle('Small',parent=BASE,fontSize=10,leading=12,spaceAfter=6,alignment=0)
CELL=ParagraphStyle('Cell',parent=SMALL,fontSize=10,leading=11.5,spaceAfter=0)
CENTER=ParagraphStyle('Center',parent=BASE,alignment=TA_CENTER)
TITLE=ParagraphStyle('Title',parent=CENTER,fontName=BOLD,fontSize=16,leading=24,spaceAfter=18)
NAME=ParagraphStyle('Name',parent=CENTER,fontName=BOLD,fontSize=13,leading=19.5)
CODE=ParagraphStyle('Code',fontName='Courier',fontSize=8.2,leading=10.4,spaceAfter=10)
story=[]
def p(text,style=BASE):story.append(Paragraph(text,style))
def h(text):p(text.upper(),H)
def sub(text):p(text,SUB)
def gap(n=8):story.append(Spacer(1,n))
def page():story.append(PageBreak())
def table(rows,widths,header=True):
 vals=[[Paragraph(escape(str(x)).replace('\n','<br/>'),CELL) for x in row] for row in rows]
 t=Table(vals,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
 cmds=[('GRID',(0,0),(-1,-1),.45,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
 if header:cmds += [('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e4ebef'))]
 t.setStyle(TableStyle(cmds));story.append(t);gap(8)
def figure(name,width=468,height=190,caption=''):
 story.append(Image(str(PLOTS/name),width=width,height=height));gap(4)
 if caption:p(caption,SMALL)
def val(case,alg,metric,scale=1):
 r=lookup[(case,alg)];precision=3 if metric=='energy_per_delivered' else 2;return f"{r[metric+'_mean']*scale:.{precision}f} ± {r[metric+'_sd']*scale:.{precision}f}"
def improvement(case,metric,higher=True):
 b=lookup[(case,'shortest')][metric+'_mean'];v=lookup[(case,'predictive')][metric+'_mean']
 return (v-b)/b*100 if higher else (b-v)/b*100

# 1 Cover
p('INNOVATIVE EVALUATION PRACTICES<br/>BCSE308P COMPUTER NETWORKS LAB',NAME);gap(15)
p(meta['title'].upper(),TITLE);gap(13)
p('FALL SEMESTER 2026-2027<br/>SLOT F2 &nbsp;&nbsp; TEAM 19',NAME);gap(16)
for member in meta['members']:p(member['register_number']+' &nbsp; '+member['name'].upper(),NAME)
gap(30);p('B.Tech.<br/>in<br/>Computer Science and Engineering',CENTER);gap(15)
p('School of Computer Science and Engineering<br/>VIT Vellore',CENTER);gap(35);p('October 2026',CENTER);page()
# 2 Abstract
h('Abstract')
abstract=('Battery-powered IoT sensors often forward measurements through neighboring relays to reach a gateway. '
'Repeatedly selecting a convenient relay can exhaust its battery and reduce network availability. This project implements '
'a Predictive Adaptive Mesh Routing prototype that uses recent energy consumption to estimate near-future remaining energy. '
'Each sensor smooths its drain rate using an exponentially weighted moving average. Parent selection combines predicted '
'energy risk, link loss, and queue occupancy, while fixed gateway levels prevent loops and hysteresis limits route changes. '
'The prototype includes a Python simulator and an interactive browser dashboard. It compares shortest-hop, reactive '
'energy-aware, and predictive routing using identical seeded topology and traffic conditions. Five scenarios cover low, '
'medium, and high steady loads, a temporary burst, and an injected relay failure. Ten matched seeds per scenario produce '
'150 simulation runs. At medium load, predictive routing delivers 98.50 percent of scheduled readings on average, compared '
'with 97.92 percent for shortest-hop. Under high load, the corresponding means are 75.05 and 73.08 percent. Improvements '
'are modest and do not hold for every metric or individual seed. The implementation uses illustrative energy units, '
'independent links, and fixed initial levels. It provides a reproducible algorithm demonstration and a foundation for '
'evaluation with calibrated energy and realistic wireless contention.')
assert len(abstract.split())<=300
p(abstract);gap(20);p('<b>Keywords:</b> IoT mesh routing, energy prediction, EWMA, parent selection, network simulation, performance evaluation.');page()
# 3 Certificate
h('Certificate');gap(18)
p('This is to certify that the project report titled "'+meta['title']+'" is a bonafide record of the work done by '+', '.join(m['name']+' ('+m['register_number']+')' for m in meta['members'])+' in partial fulfilment of the requirements of the Innovative Evaluation Practices for BCSE308P Computer Networks Lab during the Fall Semester 2026-2027.')
gap(45);sub('Name and signature of the students')
for m in meta['members']:
 p(m['name']+' &nbsp; '+m['register_number']);p('Signature ______________________________');gap(22)
page()
# 4 TOC
h('Table of contents')
toc=[('Abstract','2'),('Certificate','3'),('1 Introduction','5'),('1.1 Background and motivation','5'),('1.2 Problem statement','5'),('1.3 Objectives','5'),('1.4 Scope and limitations','5'),('1.5 Course and lab mapping','5'),('2 Literature survey','6'),('3 Proposed system','7'),('3.1 Architecture and topology','7'),('3.2 Baseline mechanism','7'),('3.3 Algorithm and pseudocode','8'),('3.4 Novelty statement','8'),('3.5 Assumptions and design decisions','8'),('4 Implementation','9'),('4.1 Tools and 4.2 configuration','9'),('4.3 Code structure and 4.4 challenges','10'),('5 Experimental setup and evaluation','11'),('5.1 Metrics and 5.2 scenarios','11'),('5.3 Repeated-run results','12'),('Performance graphs','13'),('5.4 Analysis and 5.5 critical evaluation','14'),('6 Conclusion and future work','15'),('7 References','16'),('Appendix A Source and configuration listings','17'),('Appendix B Verification evidence and reproduction','18')]
t=Table([[Paragraph(a,SMALL),Paragraph(b,SMALL)] for a,b in toc],colWidths=[425,43]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]));story.append(t);page()
# 5 Intro
h('1 Introduction');sub('1.1 Background and motivation')
p('A multi-hop sensor network extends connectivity by allowing devices to relay measurements. Sensors near the gateway may forward traffic from several sources and deplete earlier than lightly used nodes. This motivates a routing rule that considers future energy availability alongside communication quality. Low-power routing standards provide relevant background [1], [2].')
sub('1.2 Problem statement');p('Given a static physical mesh, finite sensor batteries, and scheduled sensor readings, select loop-free next hops that balance delivery, delay, and battery use. The central question is whether a short-horizon energy forecast adds value beyond current-energy routing under identical modeled conditions.')
sub('1.3 Objectives');p('Implement and visualize three comparable policies, account for data and monitoring energy, predict future remaining energy without reading future simulator state, and evaluate repeated scenarios. Preserve raw measurements so another evaluator can reproduce the result.')
sub('1.4 Scope and limitations');p('The prototype uses one powered gateway, static sensor positions, abstract energy costs, and independent lossy links. It implements sensor-to-gateway traffic. It excludes a full IPv6/RPL stack, radio contention, device power calibration, and distributed level repair. Claims concern this model only.')
sub('1.5 Mapping to course concepts and lab work')
table([['Course concept','Project implementation'],['Topology and routing','Physical mesh, BFS gateway levels, next-hop selection'],['Reliability and queues','Lossy attempts, bounded retries, buffers, packet TTL'],['Performance evaluation','Delivery, delay, energy, failures, repeatability'],['Network programming','Local HTTP API and interactive dashboard']],[165,303])
p('This mapping identifies concepts rather than asserting numbered syllabus modules or lab experiment numbers that were not supplied.',SMALL);page()
# 6 Literature
h('2 Literature survey');sub('2.1 Existing mechanisms')
p('RPL organizes routing toward a root through a destination-oriented directed acyclic graph [1]. RFC 6551 describes usable node and link metrics [2]. MRHOF combines metric-based selection with hysteresis to reduce route churn [3]. Exponential smoothing provides a compact way to estimate a changing scalar rate [4].')
sub('2.2 Related work')
table([['Authors and year','Technique','Metrics and tool','Merits','Gap for this study'],['Winter et al., 2012 [1]','RPL routing framework','Rank and objective function; specification','Loop-aware routing structure','No prescribed predictor for our energy forecast'],['Vasseur et al., 2012 [2]','LLN routing metrics','Node energy, loss and delay; specification','Flexible metric vocabulary','Does not validate our chosen weighted policy'],['Gnawali and Levis, 2012 [3]','MRHOF','Additive path metric and hysteresis; specification','Reduces parent churn','Our local cost and forecast are distinct'],['NIST / SEMATECH, n.d. [4]','Exponential smoothing','Smoothed scalar observations; handbook','Small state and computation','Forecast accuracy depends on changing load']],[87,86,102,91,102])
sub('2.3 Research gap and justification')
p('This project tests a clearly bounded implementation question: what changes when current advertised energy in a local parent score is replaced by an age-corrected energy forecast? The contribution is an inspectable prototype and matched comparison. Energy-aware and prediction-aware routing already exist as research themes. Publication-level originality has not been established, and the implementation is not a standards-compliant RPL extension.')
page()
# 7 Architecture
h('3 Proposed system');sub('3.1 System architecture and topology')
p('The simulator maintains node batteries, packet queues, physical links, and a gateway. Local status observations feed the parent-selection policy. Packet events update energy and delivery counters. The HTTP server returns complete run histories to the dashboard for playback and inspection.')
figure('F2_Team19_topology.png',468,245,'Figure 1. Actual physical topology for the bundled seed. Gateway 0 is externally powered. Sensor 1 has a smaller battery. Coordinates are abstract units.')
sub('3.2 Baseline mechanisms')
p('Shortest-hop routing selects a fresh neighbor on a lower initial BFS level and breaks ties using link quality. Reactive energy-aware routing uses current advertised battery fraction, link loss, and queue occupancy. Predictive routing changes only the energy input to the same weighted score. All policies use the same monitoring schedule, costs, and initial level constraint.')
page()
# 8 Algorithm
sub('3.3 Proposed mechanism and pseudocode')
p('Every five seconds, the sensor updates its estimated drain using historical samples. An advertisement carries remaining energy, capacity, drain, queue length, and timestamp. At time t, PAMR projects the candidate to t + H, including advertisement age.')
story.append(Preformatted('recent = (previous_energy - current_energy) / 5\ndrain = alpha * recent + (1-alpha) * previous_drain\nfuture = max(0, advertised_energy - drain * (H + age))\nrisk = 1 - min(1, future / capacity)\ncost = 0.65*risk + 0.20*(1-link_success) + 0.15*(queue/20)',CODE))
story.append(Preformatted('FOR each live sensor every decision interval:\n  eligible = fresh advertised neighbors on lower initial levels\n  IF eligible is empty: parent = none; retain queued packets\n  ELSE:\n    best = candidate with minimum normalized cost\n    IF current parent is invalid OR improvement > 0.06:\n      parent = best\n  Forward at most one queued packet attempt per slot',CODE))
sub('3.4 Novelty relative to the implemented baselines')
p('The predictive policy replaces observed current energy with estimated future energy. The reactive baseline isolates this difference from the benefit of energy awareness itself. A worked example and full function explanations are available in the viva guide. No additional hop-count term is used because eligible parents already lie on minimum-hop progress in the fixed initial scaffold.')
sub('3.5 Assumptions and design decisions')
p('Use a strict decreasing initial level to prevent loops. Expire observations after 20 seconds. Prefer direct gateway access when eligible. Treat the gateway as externally powered. Use soft energy risk instead of a hard low-battery ban. Keep weights and horizon fixed during a run. These decisions simplify explanation but limit route flexibility.')
page()
# 9 Implementation
h('4 Implementation');sub('4.1 Tools platform versions and hardware')
p(f'The implementation uses Python 3.10 or later and its standard library. Verification ran under Python {platform.python_version()} in a Linux execution environment. The dashboard uses HTML, CSS, JavaScript, and SVG in a browser. No physical sensor hardware or database is required. A normal laptop is the intended demonstration platform; hardware performance was not benchmarked.')
sub('4.2 Simulation configuration')
table([['Parameter','Value'],['Sensors and gateway','30 battery-powered sensors plus gateway 0'],['Duration and time step','400 s; one-second illustrative service slots'],['Spatial link rule','Undirected link when distance is within radius 32'],['Sensor energy','Seeded capacity 85-115 EU; sensor 1 has 38 EU'],['Data TX / RX cost','0.10 / 0.05 EU per powered attempt'],['Idle and control cost','0.005 EU/slot; TX 0.02 and RX 0.005 EU'],['Queue limit / retries / TTL','20 packets; 3 attempts per current hop; 100 s'],['Sample / advertisement / decision','5 s / 10 s / 5 s'],['Forecast horizon and smoothing','H = 40 s; alpha = 0.35'],['Cost weights and hysteresis','0.65 energy, 0.20 link, 0.15 queue; margin 0.06'],['Seeds','0-9 for repeated results; 42 for the dashboard demo']],[185,283])
p('EU denotes illustrative energy units. These costs do not support a joule, mAh, or real-device lifetime claim.',SMALL);page()
# 10 modules
sub('4.3 Code structure and key modules')
table([['Module','Responsibility'],['simulator.py','State, topology, observations, scoring, forwarding, energy, metrics'],['app.py','Local HTTP server, bounded input validation and cached runs'],['experiments.py','Five cases, matched seeds, CSV output, mean and sample SD'],['static/index.html','Network replay, node inspection, comparison table and charts'],['scripts/run_simulation.py','Load saved JSON configuration and export reproducible simulation'],['test_simulator.py / test_http.py','Conservation, reproducibility, route safety and real HTTP tests']],[175,293])
sub('4.4 Implementation challenges and resolutions')
p('<b>Fair randomness.</b> Event-based seeded hashes preserve the same offered traffic across different routing decisions. A sequential shared random stream could accidentally change later workloads when a policy takes another path.')
p('<b>Instant forwarding artifacts.</b> Successful packets enter a next-slot inbox. This prevents one source iteration order from forwarding a packet through several hops at zero simulated delay.')
p('<b>Accounting.</b> Separate scheduled demand, live-source generation, terminal drops, and packets pending at the observation boundary. Verify both packet totals and per-node energy balance.')
p('<b>Stale state and route churn.</b> Timestamp advertisements, expire them, and use a switching margin. These rules retain realistic delayed knowledge without consulting a global live-energy oracle for parent choice.')
p('<b>Evidence limits.</b> Local HTTP and programmatic dashboard checks ran successfully. Cloud-browser restrictions prevented genuine dashboard screenshot capture here. The repository provides a local capture script; those images must be added before final submission.')
page()
# 11 experiments
h('5 Experimental setup and performance evaluation');sub('5.1 Metrics and rationale')
table([['Metric','Definition and purpose'],['Demand delivery ratio','Delivered / scheduled readings, including offline-source demand'],['Packet delivery ratio','Delivered / generated packets from live sources'],['Mean delay','Creation-to-gateway time over delivered packets only'],['EU per delivered packet','All sensor energy spent / delivered count'],['First battery death','Earliest depletion; injected failure excluded'],['Route changes / forecast MAE','Policy churn and absolute future-energy forecast error']],[165,303])
sub('5.2 Scenarios and parameter values')
table([['Case','Traffic per sensor per second','Change during run'],['S1 Low load','0.015','Steady Bernoulli generation'],['S2 Medium load','0.030','Steady Bernoulli generation'],['S3 High load','0.060','Steady Bernoulli generation'],['S4 Burst','0.030 normally','Probability triples in middle third'],['S5 Relay failure','0.030','Sensor 1 forced offline at 200 s if alive']],[100,160,208])
p('Every case uses ten matched seeds and all three policies: 5 x 10 x 3 = 150 runs. Other parameters remain fixed. Means and sample standard deviations summarize runs, without a significance claim. No-death observations are right-censored at 400 seconds. Control-message costs are shared across policies to isolate selection behavior.')
page()
# 12 results
sub('5.3 Repeated-run results baseline versus proposed')
p('Values show mean ± sample SD across ten seeds. Demand delivery uses percent; delay uses seconds; energy uses EU per delivered packet. Positive improvement means higher delivery or lower delay/energy. Negative values indicate a regression.')
rows=[['Case','Metric','Shortest-hop','Predictive','Improvement %']]
for case in CASES[:3]:
 for metric,name,scale,higher in [('demand_delivery_ratio','Demand %',100,True),('average_delay','Delay s',1,False),('energy_per_delivered','EU/packet',1,False)]:
  rows.append([NAMES[case],name,val(case,'shortest',metric,scale),val(case,'predictive',metric,scale),f'{improvement(case,metric,higher):+.2f}'])
table(rows,[85,72,108,108,95])
p('Relative improvement uses (proposed - baseline) / baseline for delivery, and (baseline - proposed) / baseline for costs. Delivery differences in percentage points are distinct from relative percentage improvements.')
sub('Reactive baseline for the prediction contribution')
table([['Case','Reactive demand %','Predictive demand %'],*[ [NAMES[c],val(c,'reactive','demand_delivery_ratio',100),val(c,'predictive','demand_delivery_ratio',100)] for c in CASES[:3]]],[140,164,164])
page()
# 13 graphs
sub('Performance graphs')
figure('F2_Team19_delivery.png',468,200,'Figure 2. Demand delivery under five scenarios. Error bars show sample SD across ten matched seeds. All three algorithms share workloads and physical conditions.')
gap(9)
figure('F2_Team19_delay.png',468,200,'Figure 3. Mean delivered-packet delay. Lower delay alone does not establish a better network because dropped and pending packets are outside the delay mean.')
p('Raw per-run rows are preserved in results/experiments.csv. Summary values in results/summary.json drive these plots and the presentation.',SMALL);page()
# 14 discussion
sub('5.4 Analysis and discussion')
table([['Stress case','Shortest-hop demand %','Reactive demand %','Predictive demand %'],*[ [NAMES[c],val(c,'shortest','demand_delivery_ratio',100),val(c,'reactive','demand_delivery_ratio',100),val(c,'predictive','demand_delivery_ratio',100)] for c in CASES[3:]]],[102,122,122,122])
p('Medium-load delivery rises from 97.92 to 98.50 percent, a gain of 0.58 percentage points. High-load delivery rises from 73.08 to 75.05 percent, a gain of 1.97 points. Burst delivery rises from 73.26 to 75.85 percent. The predictive improvement beyond reactive routing is smaller, so current-energy awareness explains part of the benefit.')
p('At low load, idle and control costs contribute a larger share per delivered packet. Under high load, bottleneck queues and root-adjacent relays constrain all strategies. Forecasts can redistribute load when alternatives exist but cannot increase physical forwarding capacity.')
sub('5.5 Critical evaluation')
p('In the default burst example at seed 42, demand delivery is 81.98 percent for shortest-hop, 82.32 percent for reactive routing, and 80.94 percent for predictive routing. First battery death occurs at 347, 375, and 361 seconds respectively. Prediction therefore does not dominate either baseline on all outcomes.')
p('Potential failure conditions include abrupt drain changes, stale advertisements, a long forecast horizon, correlated radio failures absent from this model, and loss of every eligible lower-level parent. Fixed levels exclude some valid detours. Sample variation is material, and no statistical significance test was performed.')
page()
# 15 conclusion
h('6 Conclusion and future work');sub('6.1 Summary of work and quantified findings')
p('The project delivers a runnable simulator, a visual dashboard, three routing policies, saved configuration/topology files, raw results, and automated checks. The evaluation covers 150 runs across five scenarios. At medium load, predictive demand delivery averages 98.50 percent versus 97.92 percent for shortest-hop. Under high load, the means are 75.05 and 73.08 percent. Burst mean delay falls from 15.38 to 13.43 seconds, while individual runs can favor the reactive baseline.')
sub('6.2 Limitations')
p('The energy model is synthetic. Link attempts are independent and there is no MAC contention. Topology is static and levels do not repair after failures. The predictor starts at zero and can lag abrupt changes. Weights and horizon are chosen defaults, and the study does not establish optimality or publication-level novelty.')
sub('6.3 Future enhancements')
p('Calibrate radio and device power states; add realistic contention, duty cycling, and acknowledgement-driven link estimates; implement distributed topology repair; and test more network sizes and traffic structures. Parameter sensitivity should use separate validation cases before testing generalization. A full Contiki-NG/RPL or hardware implementation would provide a stronger deployment assessment.')
gap(16)
p('<b>Project outcome.</b> The implementation supports live policy comparison and parameter changes. The results demonstrate modest conditional gains and explicit trade-offs, with sufficient source and raw evidence for verification.')
page()
# 16 refs
h('7 References')
references=[
'[1] T. Winter et al., "RPL: IPv6 Routing Protocol for Low-Power and Lossy Networks," IETF, RFC 6550, Mar. 2012, doi: 10.17487/RFC6550. [Online]. Available: https://www.rfc-editor.org/rfc/rfc6550.html',
'[2] J. P. Vasseur et al., "Routing Metrics Used for Path Calculation in Low-Power and Lossy Networks," IETF, RFC 6551, Mar. 2012, doi: 10.17487/RFC6551. [Online]. Available: https://www.rfc-editor.org/rfc/rfc6551.html',
'[3] O. Gnawali and P. Levis, "The Minimum Rank with Hysteresis Objective Function," IETF, RFC 6719, Sep. 2012, doi: 10.17487/RFC6719. [Online]. Available: https://www.rfc-editor.org/rfc/rfc6719.html',
'[4] NIST/SEMATECH, "Single Exponential Smoothing," e-Handbook of Statistical Methods, Sec. 6.4.3.1. [Online]. Available: https://www.itl.nist.gov/div898/handbook/pmc/section4/pmc431.htm. Accessed: Oct. 27, 2026.'
]
for ref in references:p(escape(ref));gap(12)
p('The references support background concepts. The custom score, parameter choices, and generated results belong to the supplied prototype and are not validated by those standards.',SMALL)
page()
# 17 listing
h('Appendix A Source and configuration listings')
sub('A.1 Forecast and local parent cost')
source=(ROOT/'simulator.py').read_text()
block=source.split('    def score(self, n, candidate):',1)[1].split('    def candidates',1)[0]
block=block.replace('        lookahead = self.c.horizon + self.t - obs.at if self.algorithm == \"predictive\" else 0', '        lookahead = 0\n        if self.algorithm == \"predictive\":\n            lookahead = self.c.horizon + self.t - obs.at')
story.append(Preformatted('def score(self, n, candidate):'+block,CODE,maxLineLength=92))
sub('A.2 Configuration extract')
config=json.loads((ROOT/'simulation/F2_Team19_Config.json').read_text())
keys=['nodes','duration','seed','scenario','traffic','horizon','alpha','advertise_every','decide_every']
story.append(Preformatted(json.dumps({k:config[k] for k in keys},indent=2),CODE))
p('The complete executable implementation is in simulator.py. simulation/F2_Team19_Topology.json stores every node, initial level, link, and modeled link quality.',SMALL)
page()
# 18 evidence
h('Appendix B Verification and supporting evidence')
sub('B.1 Reproduction commands')
story.append(Preformatted('python -m unittest -v\npython scripts/run_simulation.py\npython experiments.py --seeds 10\npython app.py',CODE))
p('Automated checks verify packet and energy conservation, deterministic repeatability, decreasing parent levels, predictor arithmetic, stale observation handling, hysteresis, input validation, serialization, and actual local HTTP requests. The expected automated suite contains 14 passing checks.')
sub('B.2 Evidence files')
table([['Repository path','Verification purpose'],['simulation/F2_Team19_Config.json','Full scenario and protocol configuration'],['simulation/F2_Team19_Topology.json','Actual seed-42 physical network'],['results/experiments.csv','150 per-policy result rows'],['results/summary.json','15 scenario-policy aggregates'],['results/figures/','Plots of actual repeated-run measurements'],['tests/F2_Team19_TestResults.txt','Recorded automated verification output'],['screenshots/','Real dashboard images captured on the presentation laptop']],[225,243])
sub('B.3 Dashboard screenshot completion')
p('The local capture script generates network, final-state, comparison, relay-failure, and parameter-change screenshots. These images require execution on a laptop with a browser and must be committed before submission. They were not captured in the cloud environment. The provided plots are measurement figures and are not labeled as dashboard screenshots.')
p('No packet capture is supplied because this simulator uses abstract packets rather than a full deployed IP stack. No Packet Tracer file is applicable to this Python implementation.',SMALL)

def footer(canvas,doc):
 if doc.page>1:
  canvas.setFont(FONT,9);canvas.setFillColor(colors.HexColor('#4b5960'))
  canvas.drawString(72,35,'BCSE308P Computer Networks Lab   F2 Team 19')
  canvas.drawRightString(540,35,str(doc.page))
pdf=OUT/'F2_Team19_Report.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=letter,rightMargin=72,leftMargin=72,topMargin=55,bottomMargin=54,title=meta['title'],author='; '.join(m['name'] for m in meta['members']))
html_parts=['<!doctype html><meta charset="utf-8"><title>F2 Team19 Report</title><style>@page{size:Letter;margin:0}body{margin:0;color:black;font-family:"Times New Roman",Times,serif;font-size:12pt;line-height:1.15}section{box-sizing:border-box;width:8.5in;min-height:11in;padding:55pt 72pt 54pt;break-after:page}p{margin:0 0 8pt;text-align:justify}h1,h2,h3{color:black}table{border-collapse:collapse;width:100%;font-size:10pt;margin:8pt 0}td{border:1px solid #d9d9d9;padding:5pt;vertical-align:middle}tr:first-child{background:#e4ebef}pre{font-family:monospace;font-size:8pt;white-space:pre-wrap}img{max-width:100%} .Title{font-size:16pt;line-height:1.5;font-weight:bold;text-align:center}.Name{font-size:13pt;line-height:1.5;font-weight:bold;text-align:center}.Center{text-align:center}.Heading{font-size:14pt;line-height:1.5;font-weight:bold}.Subheading{font-size:12pt;line-height:1.5;font-weight:bold}.Small{font-size:10pt}</style><section>']
for item in story:
 if isinstance(item,PageBreak):html_parts.append('</section><section>')
 elif isinstance(item,Paragraph):html_parts.append('<p class="'+item.style.name+'">'+item.text+'</p>')
 elif isinstance(item,Table):
  html_parts.append('<table>')
  for row in item._cellvalues:
   html_parts.append('<tr>'+''.join('<td>'+(v.text if isinstance(v,Paragraph) else escape(str(v)))+'</td>' for v in row)+'</tr>')
  html_parts.append('</table>')
 elif isinstance(item,Image):html_parts.append('<img src="../results/figures/'+Path(item.filename).name+'">')
 elif isinstance(item,Preformatted):html_parts.append('<pre>'+escape('\n'.join(item.lines))+'</pre>')
 elif isinstance(item,Spacer):html_parts.append('<div style="height:'+str(item.height)+'pt"></div>')
html_parts.append('</section>')
(OUT/'F2_Team19_Report_Print.html').write_text(''.join(html_parts))
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'F2_Team19_ReportFormatting.txt').write_text('Report typography: 16 pt bold uppercase title, 13 pt bold uppercase member names, 14 pt bold uppercase chapter headings, 12 pt body at 1.15 line spacing.\nRequested face: Times New Roman. The included PDF embeds a Times-compatible Nimbus Roman substitute. This rebuild script uses genuine Times New Roman when detected in Windows Fonts or msttcorefonts; otherwise it falls back to PDF Times-Roman. Check the resulting font before submission. For literal font compliance, rebuild using an installed Times New Roman face or open F2_Team19_Report_Print.html on a machine with Times New Roman and print to PDF with browser headers and footers disabled. Verify page breaks after export. Table text is reduced for fit.\n')
(ROOT/'results/summary_for_deck.json').write_text(json.dumps({'summary':summary,'demo':{a:demo['runs'][a]['metrics'] for a in ALGS},'members':meta['members']},indent=2))
print(pdf)
