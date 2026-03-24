#!/usr/bin/env python3
"""
Streamlit Community Cloud serves the same static HTML shell for plain HTTP GETs.
The Python process only starts after JS runs and opens a WebSocket — so curl is not a real visit.

This script uses headless Chromium to load the app and, if shown, click the sleep / wake CTA.
"""
import os
import re
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get(
    "STREAMLIT_APP_URL", "https://trump-actions-tracker.streamlit.app/"
).rstrip("/") + "/"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(5_000)

            wake = page.get_by_role(
                "button", name=re.compile(r"get this app back up|wake|open app", re.I)
            )
            if wake.count() > 0:
                wake.first.click()
                page.wait_for_timeout(90_000)
            else:
                page.wait_for_timeout(20_000)
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Keep-awake failed: {e}", file=sys.stderr)
        sys.exit(1)
