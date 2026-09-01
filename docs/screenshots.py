"""Regenerate the README screenshots.

The app is behind a login, so a one-shot headless capture cannot reach the
interesting pages — this signs in first, then captures.

Uses the system Chrome (channel="chrome") rather than Playwright's bundled
browser, so no extra download is needed.

    pip install playwright
    python docs/screenshots.py [base_url]

Requires the backend on :8000 and the frontend on :5173, seeded via
`python -m app.seed`.
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173"
OUT = Path(__file__).parent
# A short viewport with full_page=True crops to the actual content height.
# full_page never captures less than the viewport, so a tall one leaves dead
# space below short pages.
VIEWPORT = {"width": 1280, "height": 600}

AGENT_EMAIL = "agent@helpdesk.example"
AGENT_PASSWORD = "agent123"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)

        page.goto(f"{BASE}/login", wait_until="networkidle")
        page.fill('input[type="email"]', AGENT_EMAIL)
        page.fill('input[type="password"]', AGENT_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE}/", timeout=15000)
        page.wait_for_load_state("networkidle")

        shots = {
            "dashboard.png": "/",
            "tickets.png": "/tickets",
            "ticket-detail.png": "/tickets/1",
        }

        for filename, path in shots.items():
            page.goto(f"{BASE}{path}", wait_until="networkidle")
            # The stat tiles and tables render after their fetch resolves.
            page.wait_for_timeout(700)
            page.screenshot(path=str(OUT / filename), full_page=True)
            print(f"wrote {filename}")

        browser.close()


if __name__ == "__main__":
    main()
