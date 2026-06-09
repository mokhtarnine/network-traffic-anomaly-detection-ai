"""
Browser test — captures results, error analysis, cross-tables, and export sections.
Assumes the app is already running at http://localhost:8501 and the full pipeline
(upload → EDA → preprocess → detect) was already completed.

This script starts fresh: uploads KDDTest+.txt, runs the full pipeline, then
captures all remaining screenshots using scroll-based navigation.
"""
import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

APP_URL = "http://localhost:8501"
DATASET = str(Path("data/raw/KDDTest+.txt").resolve())
OUT = Path("C:/Users/asus/AppData/Local/Temp/st_results")
OUT.mkdir(parents=True, exist_ok=True)


async def wait_for_text(page, text, timeout=60000):
    await page.wait_for_function(
        f"document.body.innerText.includes({repr(text)})",
        timeout=timeout,
    )


async def scroll_to(page, y):
    await page.evaluate(f"window.scrollTo(0, {y})")
    await asyncio.sleep(0.8)


async def shot(page, name):
    path = str(OUT / f"{name}.png")
    await page.screenshot(path=path, full_page=False)
    print(f"  [screenshot] {name}.png")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=80)
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()

        # ── 0. Load app ────────────────────────────────────────────────────────
        print("0. Loading app...")
        await page.goto(APP_URL, wait_until="networkidle")
        await asyncio.sleep(3)
        await shot(page, "00_home")

        # ── 1. Upload file ─────────────────────────────────────────────────────
        print("1. Uploading KDDTest+.txt...")
        uploader = page.locator('[data-testid="stFileUploaderDropzoneInput"]').first
        await uploader.set_input_files(DATASET)
        await wait_for_text(page, "Dataset is valid", timeout=30000)
        await asyncio.sleep(1)
        await shot(page, "01_upload_valid")

        # ── 2. Scroll past EDA to Preprocess ──────────────────────────────────
        print("2. Running Preprocess...")
        await scroll_to(page, 2000)
        await asyncio.sleep(0.5)
        btn = page.locator("button", has_text="Run Preprocessing").first
        await btn.scroll_into_view_if_needed()
        await btn.click()
        await wait_for_text(page, "Done", timeout=60000)
        await asyncio.sleep(1)
        await shot(page, "02_preprocess_done")

        # ── 3. Run Detection ───────────────────────────────────────────────────
        print("3. Running K-Means detection...")
        await scroll_to(page, 3500)
        btn2 = page.locator("button", has_text="Run Detection").first
        await btn2.scroll_into_view_if_needed()
        await btn2.click()
        await wait_for_text(page, "Detection complete", timeout=120000)
        await asyncio.sleep(2)
        await shot(page, "03_detection_complete")

        # ── 4. Results — scroll down to results section ────────────────────────
        print("4. Scrolling to Results section...")
        await scroll_to(page, 5000)
        await asyncio.sleep(2)
        await shot(page, "04_results_top")

        # Try to click "Cluster View" tab if visible
        try:
            tab = page.locator("button[role='tab']", has_text="Cluster View").first
            await tab.wait_for(state="visible", timeout=5000)
            await tab.click()
            await asyncio.sleep(1.5)
        except PWTimeout:
            print("  (Cluster View tab not found, continuing)")

        await scroll_to(page, 6000)
        await asyncio.sleep(1.5)
        await shot(page, "05_cluster_view")

        # ── 5. Error Analysis tab ──────────────────────────────────────────────
        print("5. Error Analysis tab...")
        try:
            err_tab = page.locator("button[role='tab']", has_text="Error Analysis").first
            await err_tab.wait_for(state="visible", timeout=5000)
            await err_tab.click()
            await asyncio.sleep(1.5)
            await scroll_to(page, 5500)
            await asyncio.sleep(1)
            await shot(page, "06_error_analysis")
        except PWTimeout:
            print("  (Error Analysis tab not found)")
            await shot(page, "06_error_analysis_fallback")

        # ── 6. Cross-Tables tab ────────────────────────────────────────────────
        print("6. Cross-Tables tab...")
        try:
            ct_tab = page.locator("button[role='tab']", has_text="Cross-Tables").first
            await ct_tab.wait_for(state="visible", timeout=5000)
            await ct_tab.click()
            await asyncio.sleep(1.5)
            await scroll_to(page, 5500)
            await asyncio.sleep(1)
            await shot(page, "07_cross_tables")
        except PWTimeout:
            print("  (Cross-Tables tab not found)")
            await shot(page, "07_cross_tables_fallback")

        # ── 7. Export section ──────────────────────────────────────────────────
        print("7. Export section...")
        await scroll_to(page, 8000)
        await asyncio.sleep(2)
        await shot(page, "08_export_section")

        # Try Save to History button
        try:
            save_btn = page.locator("button", has_text="Save to History").first
            await save_btn.wait_for(state="visible", timeout=5000)
            await save_btn.scroll_into_view_if_needed()
            await save_btn.click()
            await asyncio.sleep(1.5)
            await shot(page, "09_after_save_history")
        except PWTimeout:
            print("  (Save to History button not found)")

        # ── 8. History section ─────────────────────────────────────────────────
        print("8. History section...")
        await scroll_to(page, 10000)
        await asyncio.sleep(2)
        await shot(page, "10_history_section")

        await browser.close()
        print(f"\nDone. Screenshots saved to: {OUT}")


asyncio.run(main())
