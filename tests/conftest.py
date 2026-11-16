import base64
import io

import pytest
from PIL import Image


def make_png(width, height):
    buf = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def fake_png():
    return make_png


@pytest.fixture(autouse=True)
def no_host_automation_browser(tmp_path, monkeypatch):
    """Tests never see the host's ~/.config/automation-browser/config (ironerumi fork),
    and the endpoint variables apply() writes into os.environ never leak into later tests."""
    from browser_harness import automation_browser

    monkeypatch.setattr(automation_browser, "CONFIG", tmp_path / "no-automation-browser-config")
    for key in (*automation_browser.EXPLICIT, automation_browser.SELECTED_ENDPOINT):
        # setenv first so monkeypatch records the original state, absent included, and restores it.
        monkeypatch.setenv(key, "")
        monkeypatch.delenv(key)
