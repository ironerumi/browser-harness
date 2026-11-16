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
    """Tests never see the host's ~/.config/automation-browser/config (ironerumi fork)."""
    from browser_harness import automation_browser

    monkeypatch.setattr(automation_browser, "CONFIG", tmp_path / "no-automation-browser-config")
