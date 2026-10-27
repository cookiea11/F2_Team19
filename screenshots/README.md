# Dashboard evidence

This directory must contain actual dashboard screenshots before VTOP submission.
The cloud browser cannot open the local project in this environment, so screenshots
have not been fabricated or substituted with plots.

From the repository root on your laptop:

```sh
python -m pip install -r requirements-evidence.txt
python -m playwright install chromium
python scripts/capture_screenshots.py
```

The command starts a temporary local server and captures the actual browser UI:

- F2_Team19_Dashboard.png
- F2_Team19_FinalState.png
- F2_Team19_Results.png
- F2_Team19_RelayFailure.png
- F2_Team19_ParameterChange.png

Alternatively, take screenshots manually from the dashboard. Show the default
network, comparison table, relay failure, and a live parameter change. Save images
with the F2_Team19 prefix and commit them to this directory.

Manual screenshots are the quickest fallback if browser installation is unavailable.
