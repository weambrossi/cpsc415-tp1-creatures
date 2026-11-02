"""Browser-driven check of the page (spec.md W11, and W12 with a key). Playwright drives Chromium.

    .venv/bin/playwright install chromium               # once
    .venv/bin/python -m pytest tests/test_browser.py -v # W11 on fakes: free, a few seconds
    HEADED=1 .venv/bin/python -m pytest tests/test_browser.py -v   # watch it work

The test starts the server itself, so nothing needs to be running first. The last assertions are
the point: a page that works can still leak the key, and only a real browser sees the requests
the page actually made.
"""
import importlib.util
import os
import threading

import pytest
from werkzeug.serving import make_server

from app import server
from tests.fakes import FakeCritic, FakeImageModel

# Skipped, not failed, on a machine without Playwright (the gate runs on every teammate's laptop).
playwright = pytest.importorskip("playwright.sync_api")


def run_page(app, description="a small forest fox kit holding an acorn", name="FERNKIT"):
    """Serve the app on a free port, drive the page once, return what the browser saw."""
    httpd = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with playwright.sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=not os.environ.get("HEADED"),
                                            slow_mo=400 if os.environ.get("HEADED") else 0)
            except playwright.Error as e:  # Chromium not downloaded on this machine
                pytest.skip(f"Chromium is not installed for Playwright: {e}")
            page = browser.new_page()
            requests = []
            page.on("request", lambda r: requests.append((r.url, r.headers.get("authorization"))))
            page.goto(f"http://127.0.0.1:{httpd.server_port}/")
            page.fill("#description", description)
            page.fill("#name", name)
            page.click("#generate")
            page.wait_for_selector("#image[src^='data:image/']", timeout=90_000)
            page.wait_for_selector("#verdict:not(:empty)", timeout=90_000)
            seen = {"content": page.content(), "verdict": page.inner_text("#verdict"),
                    "checks": page.locator("#checks li").all_inner_texts(),
                    "problems": page.locator("#problems li").all_inner_texts(),
                    "name_read": page.inner_text("#name-read"), "requests": requests}
            browser.close()
            return seen
    finally:
        httpd.shutdown()


def assert_key_stayed_on_the_server(seen):
    assert "sk-or" not in seen["content"]                                     # no key in the page
    assert all(auth is None for _, auth in seen["requests"])                  # no Authorization header left the browser
    assert all("openrouter" not in url for url, _ in seen["requests"])        # the browser never called the provider
    assert any(url.endswith("/api/generate") for url, _ in seen["requests"])  # it called our server
    assert any(url.endswith("/api/critique") for url, _ in seen["requests"])


def test_w11_type_a_description_see_the_image_and_the_critique_and_no_key():
    seen = run_page(server.create_app(FakeImageModel(), FakeCritic()))
    assert len(seen["checks"]) == 4                     # the four shared requirements, one line each
    assert "1 problem" in seen["verdict"]
    assert any("There is no text other than the name" in p for p in seen["problems"])  # the unmet one, named
    assert "FERNKIT" in seen["name_read"] and "match" in seen["name_read"].lower()
    assert_key_stayed_on_the_server(seen)


@pytest.mark.model
@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY"), reason="needs OPENROUTER_API_KEY (billed)")
@pytest.mark.skipif(importlib.util.find_spec("app.critic") is None, reason="app/critic.py is not merged yet")
def test_w12_the_same_check_against_the_real_generator_and_critic():
    """One FLUX image and one critique, about $0.016. Run by hand, once."""
    from openrouter import OpenRouter

    make_image, critique = server.real_functions(OpenRouter(api_key=os.environ["OPENROUTER_API_KEY"]))
    seen = run_page(server.create_app(make_image, critique))
    assert len(seen["checks"]) == 4
    assert_key_stayed_on_the_server(seen)
