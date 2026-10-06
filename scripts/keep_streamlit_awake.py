#!/usr/bin/env python3
"""
Streamlit Community Cloud serves the same static HTML shell for plain HTTP GETs.
The Python process only starts after JS runs and opens a WebSocket — so curl is not a real visit.

This script uses headless Chromium to load the app, click the sleep / wake CTA if shown,
and then verify the app actually rendered. It exits non-zero if the app never came up, so
a dead app surfaces as a failed workflow run (and a GitHub notification) instead of silence.

Note on frames: community.streamlit.app wraps the running app in an iframe (path "/~/+/"),
so the app's DOM is NOT in the main frame. Everything below searches all frames rather than
assuming which one holds the content.
"""
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

URL = os.environ.get(
    "STREAMLIT_APP_URL", "https://trump-actions-tracker.streamlit.app/"
).rstrip("/") + "/"

# Text that only appears once the Streamlit script has actually executed.
# Must match real rendered copy in app.py, or this check will false-alarm.
MARKER = os.environ.get("WAKE_MARKER", "Institutional Health Diagnostic")

WAKE_BUTTON = re.compile(r"get this app back up|wake|open app", re.I)

RENDER_TIMEOUT_S = int(os.environ.get("WAKE_TIMEOUT_S", "300"))


def click_wake_cta(page) -> bool:
    """Click the sleep-screen CTA if present in any frame. Returns True if clicked."""
    for frame in page.frames:
        try:
            button = frame.get_by_role("button", name=WAKE_BUTTON)
            if button.count() > 0:
                button.first.click(timeout=15_000)
                print(f"Clicked wake CTA in frame: {frame.url or '(main)'}")
                return True
        except Exception:
            continue
    return False


def marker_visible(page) -> bool:
    """True if MARKER is present in any frame."""
    for frame in page.frames:
        try:
            if frame.get_by_text(MARKER, exact=False).count() > 0:
                return True
        except Exception:
            continue
    return False


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
            page.wait_for_timeout(5_000)

            if click_wake_cta(page):
                print("Sleep screen was shown; waiting for cold start.")
            else:
                print("No sleep CTA found; app container may already be running.")

            # Cold starts can take well over a minute. Poll until the app renders.
            deadline = time.time() + RENDER_TIMEOUT_S
            while time.time() < deadline:
                if marker_visible(page):
                    print(f"OK: app is awake and rendered {MARKER!r} at {URL}")
                    return 0
                # The CTA can appear late, or a first click can be missed.
                click_wake_cta(page)
                page.wait_for_timeout(5_000)

            frames = [f.url for f in page.frames]
            print(
                f"FAILED: {MARKER!r} did not render within {RENDER_TIMEOUT_S}s at {URL}. "
                f"The app may be crashed, stuck booting, or the marker text may have "
                f"changed in app.py. Frames seen: {frames}",
                file=sys.stderr,
            )
            return 1
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Keep-awake failed: {e}", file=sys.stderr)
        sys.exit(1)
