import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path("C:/Users/asus/AppData/Local/Temp/st_improved")
OUT.mkdir(parents=True, exist_ok=True)
DATASET = str(Path("data/raw/KDDTest+.txt").resolve())


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=60)
        ctx  = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()

        await page.goto("http://localhost:8501", wait_until="networkidle")
        await asyncio.sleep(3)
        await page.screenshot(path=str(OUT / "01_home.png"))

        # Upload
        uploader = page.locator('[data-testid="stFileUploaderDropzoneInput"]').first
        await uploader.set_input_files(DATASET)
        await page.wait_for_function(
            "document.body.innerText.includes('Dataset is valid')", timeout=30000
        )
        await asyncio.sleep(1)
        await page.screenshot(path=str(OUT / "02_uploaded.png"))

        # Scroll to preprocess
        await page.evaluate("window.scrollTo(0, 2500)")
        await asyncio.sleep(0.5)
        await page.locator("button", has_text="Run Preprocessing").first.click()
        await page.wait_for_function(
            "document.body.innerText.includes('Done')", timeout=60000
        )
        await asyncio.sleep(1)

        # Show step progress with 3 steps done
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.8)
        await page.screenshot(path=str(OUT / "03_step_progress_after_preprocess.png"))

        # Detect
        await page.evaluate("window.scrollTo(0, 3500)")
        await asyncio.sleep(0.5)
        await page.locator("button", has_text="Run Detection").first.click()
        await page.wait_for_function(
            "document.body.innerText.includes('Detection complete')", timeout=120000
        )
        await asyncio.sleep(2)

        # Step progress with all steps done
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(0.8)
        await page.screenshot(path=str(OUT / "04_step_progress_complete.png"))

        # Results — metric cards + interpretation banner
        await page.evaluate("window.scrollTo(0, 4800)")
        await asyncio.sleep(2)
        await page.screenshot(path=str(OUT / "05_results_with_interpretation.png"))

        # Cluster bar chart
        await page.evaluate("window.scrollTo(0, 6200)")
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(OUT / "06_cluster_bar.png"))

        # Cross-Tables with colour gradient
        try:
            ct = page.locator('button[role="tab"]', has_text="Cross-Tables").first
            await ct.click()
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, 5300)")
            await asyncio.sleep(1)
            await page.screenshot(path=str(OUT / "07_crosstab_gradient.png"))
        except Exception as e:
            print(f"Cross-tab: {e}")

        # Export section
        await page.evaluate("window.scrollTo(0, 9500)")
        await asyncio.sleep(2)
        await page.screenshot(path=str(OUT / "08_export_buttons.png"))

        await browser.close()
        print("Done — screenshots saved to", OUT)


asyncio.run(main())
