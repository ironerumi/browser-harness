"""Identity -> automation browser endpoint (ironerumi fork)."""

import pytest

from browser_harness import automation_browser, telemetry

CHROME = "kind=chrome\nbinary=/x\nwork.dir=/w\nwork.port=9223\nai-search.dir=/a\nai-search.port=9225\n"


@pytest.fixture
def config(tmp_path):
    path = tmp_path / "config"
    path.write_text(CHROME)
    return path


@pytest.mark.parametrize(
    ("name", "url"),
    [
        (None, "http://127.0.0.1:9223"),
        ("default", "http://127.0.0.1:9223"),
        ("work", "http://127.0.0.1:9223"),
        ("kit-check", "http://127.0.0.1:9223"),
        ("ai-search", "http://127.0.0.1:9225"),
        ("ai-search-perplexity", "http://127.0.0.1:9225"),
    ],
)
def test_bu_name_picks_identity_port(config, name, url):
    env = {} if name is None else {"BU_NAME": name}
    automation_browser.apply(env, config)
    assert env["BU_CDP_URL"] == url


@pytest.mark.parametrize("explicit", ["BU_CDP_URL", "BU_CDP_WS", "BU_BROWSER_ID"])
def test_explicit_endpoint_wins(config, explicit):
    env = {"BU_NAME": "ai-search", explicit: "given"}
    automation_browser.apply(env, config)
    assert env == {"BU_NAME": "ai-search", explicit: "given"}


def test_no_config_keeps_upstream_discovery(tmp_path):
    env = {"BU_NAME": "work"}
    automation_browser.apply(env, tmp_path / "missing")
    assert "BU_CDP_URL" not in env


def test_kind_none_stops(tmp_path):
    path = tmp_path / "config"
    path.write_text("kind=none\n")
    with pytest.raises(SystemExit, match="no automation browser on this machine"):
        automation_browser.apply({}, path)


def test_missing_identity_port_stops(tmp_path):
    path = tmp_path / "config"
    path.write_text("kind=chrome\nwork.port=9223\n")
    with pytest.raises(SystemExit, match="no ai-search.port"):
        automation_browser.apply({"BU_NAME": "ai-search"}, path)


def test_telemetry_is_off(monkeypatch):
    for name in telemetry.DISABLE_ENVS:
        monkeypatch.delenv(name, raising=False)
    assert telemetry.is_enabled() is False
