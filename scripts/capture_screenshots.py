"""Run on your own laptop to capture real dashboard evidence, never mock images.

python -m pip install -r requirements-evidence.txt
python -m playwright install chromium
python scripts/capture_screenshots.py
"""
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import Handler

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Install optional screenshot dependencies: python -m pip install -r requirements-evidence.txt\nThen: python -m playwright install chromium")
    output = ROOT / "screenshots"
    output.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1440, "height": 1050}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(f"http://127.0.0.1:{server.server_port}")
            page.get_by_role("button", name="Run all three strategies").click()
            page.wait_for_function("document.querySelector('#status').textContent.startsWith('Complete.')")
            page.screenshot(path=str(output / "F2_Team19_Dashboard.png"), full_page=True)
            page.locator("#scrub").evaluate("el => {el.value=el.max;el.dispatchEvent(new Event('input'));}")
            page.screenshot(path=str(output / "F2_Team19_FinalState.png"), full_page=True)
            page.locator(".results").screenshot(path=str(output / "F2_Team19_Results.png"))
            page.locator("#scenario").select_option("failure")
            page.get_by_role("button", name="Run all three strategies").click()
            page.wait_for_function("document.querySelector('#status').textContent.startsWith('Complete.')")
            page.locator("#scrub").evaluate("el => {el.value=el.max;el.dispatchEvent(new Event('input'));}")
            page.screenshot(path=str(output / "F2_Team19_RelayFailure.png"), full_page=True)
            page.locator("#nodes").fill("20")
            page.locator("#seed").fill("7")
            page.get_by_role("button", name="Run all three strategies").click()
            page.wait_for_function("document.querySelector('#experiment-label').textContent.includes('20 sensors')")
            page.screenshot(path=str(output / "F2_Team19_ParameterChange.png"), full_page=True)
            browser.close()
            if errors:
                raise RuntimeError("Browser JavaScript errors: " + "; ".join(errors))
        print(f"Captured 5 real screenshots in {output}. Commit them before submission.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

if __name__ == "__main__":
    main()
