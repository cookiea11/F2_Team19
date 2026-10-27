"""Check local submission files. Does not claim faculty access to a GitHub URL."""
from pathlib import Path
import argparse, csv, json, sys, zipfile
ROOT = Path(__file__).resolve().parents[1]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--strict", action="store_true", help="Also require actual screenshot files")
    args = p.parse_args()
    missing = []
    required = ['README.md','simulator.py','app.py','experiments.py','static/index.html',
                'static/demo_data.js','simulation/F2_Team19_Config.json',
                'simulation/F2_Team19_Topology.json','results/experiments.csv',
                'results/summary.json','tests/F2_Team19_TestResults.txt',
                'docs/F2_Team19_Report.pdf','docs/F2_Team19_PPT.pptx']
    for name in required:
        file = ROOT / name
        if not file.is_file() or file.stat().st_size == 0:
            missing.append(name)
    if missing:
        print('MISSING: ' + ', '.join(missing))
        return 1
    rows = list(csv.DictReader((ROOT/'results/experiments.csv').open()))
    aggregates = json.loads((ROOT/'results/summary.json').read_text())
    if len(rows) != 150 or len(aggregates) != 15:
        print('ERROR: expected 150 per-run rows and 15 aggregate records')
        return 1
    with zipfile.ZipFile(ROOT/'docs/F2_Team19_PPT.pptx') as z:
        assert z.testzip() is None
        slides = [n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml') and '/_rels/' not in n]
        if len(slides) != 14:
            print('ERROR: expected 14 slides')
            return 1
    screenshots = list((ROOT/'screenshots').glob('F2_Team19_*.png'))
    print('PASS: source, simulation inputs, report, 14-slide deck, 150 runs, and recorded tests present.')
    print(f'Actual screenshot files found: {len(screenshots)}')
    if len(screenshots) < 4:
        print('PENDING: capture and commit dashboard, results, failure and parameter-change screenshots.')
        if args.strict:
            return 1
    print('MANUAL: verify exact font requirements, signatures if required, actual GitHub URL, and faculty access.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
