"""
Take clean screenshots of the Streamlit app for the presentation.
Saves to screenshots/ folder.
"""
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

URL = "http://localhost:8501"
DATA_FILE = str(Path(__file__).parent / "data" / "raw" / "KDDTest+.txt")

VIEWPORT = {"width": 1400, "height": 850}


def wait_streamlit(page):
    """Wait until Streamlit finishes loading (spinner gone)."""
    try:
        page.wait_for_selector('[data-testid="stSpinner"]', timeout=3000)
        page.wait_for_selector('[data-testid="stSpinner"]', state="hidden", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(1200)


def shot(page, name, full_page=False):
    page.wait_for_timeout(800)
    path = str(OUT / f"{name}.png")
    page.screenshot(path=path, full_page=full_page)
    print(f"  saved {name}.png")
    return path


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=VIEWPORT)
        page = ctx.new_page()

        # ── 1. Landing / empty state ──────────────────────────────────
        print("1. Landing page...")
        page.goto(URL, wait_until="networkidle")
        wait_streamlit(page)
        shot(page, "01_landing")

        # ── 2. Upload the dataset ─────────────────────────────────────
        print("2. Uploading dataset...")
        fh = page.locator('input[type="file"]').first
        fh.set_input_files(DATA_FILE)
        wait_streamlit(page)
        shot(page, "02_after_upload")

        # ── 3. EDA section ────────────────────────────────────────────
        print("3. Opening EDA...")
        try:
            # expand EDA expander
            eda = page.get_by_text("Show EDA", exact=False).first
            eda.click()
            wait_streamlit(page)
        except Exception:
            pass
        shot(page, "03_eda_open")

        # click Labels tab
        try:
            page.get_by_role("tab", name="Labels").click()
            wait_streamlit(page)
            shot(page, "04_eda_labels")
        except Exception:
            pass

        # click Categoricals tab
        try:
            page.get_by_role("tab", name="Categoricals").click()
            wait_streamlit(page)
            shot(page, "05_eda_categoricals")
        except Exception:
            pass

        # ── 4. Preprocessing ──────────────────────────────────────────
        print("4. Preprocessing...")
        # Scroll to preprocessing section
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
        page.wait_for_timeout(500)
        try:
            preprocess_btn = page.get_by_role("button", name="Run Preprocessing")
            preprocess_btn.scroll_into_view_if_needed()
            shot(page, "06_preprocess_ready")
            preprocess_btn.click()
            wait_streamlit(page)
            shot(page, "07_after_preprocess")
        except Exception as e:
            print(f"  preprocess skip: {e}")

        # ── 5. Run Detection ──────────────────────────────────────────
        print("5. Running detection...")
        try:
            detect_btn = page.get_by_role("button", name="Run Detection")
            detect_btn.scroll_into_view_if_needed()
            shot(page, "08_detect_ready")
            detect_btn.click()
            wait_streamlit(page)
            page.wait_for_timeout(2000)
            shot(page, "09_after_detection")
        except Exception as e:
            print(f"  detect skip: {e}")

        # ── 6. Results ────────────────────────────────────────────────
        print("6. Results...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        shot(page, "10_results_full", full_page=False)

        # click Cluster View tab
        try:
            page.get_by_role("tab", name="Cluster View").click()
            wait_streamlit(page)
            shot(page, "11_cluster_view")
        except Exception:
            pass

        # click Error Analysis tab
        try:
            page.get_by_role("tab", name="Error Analysis").click()
            wait_streamlit(page)
            shot(page, "12_error_analysis")
        except Exception:
            pass

        # ── 7. Scroll to top for sidebar shot ─────────────────────────
        print("7. Sidebar...")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(600)
        shot(page, "13_with_sidebar")

        browser.close()

    print(f"\nDone — screenshots saved to {OUT}")
    for f in sorted(OUT.glob("*.png")):
        print(f"  {f.name}")


if __name__ == "__main__":
    run()
