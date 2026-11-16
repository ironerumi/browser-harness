"""Identity -> automation browser endpoint (ironerumi fork)."""

import asyncio
import json
import os
from types import SimpleNamespace
from unittest.mock import Mock

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


@pytest.mark.parametrize("entry", ["ensure_daemon", "require_existing_daemon"])
@pytest.mark.parametrize("trailing_slash", [False, True])
@pytest.mark.parametrize("endpoint", [
    "ws://127.0.0.1:9223/devtools/browser/work",
    "ws://127.0.0.1:9222/devtools/browser/everyday",
    None,
])
def test_reuse_requires_selected_browser(config, monkeypatch, entry, endpoint, trailing_slash):
    from browser_harness import admin

    for key in automation_browser.EXPLICIT:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(automation_browser.SELECTED_ENDPOINT, "")
    automation_browser.apply(config=config)
    if trailing_slash:
        monkeypatch.setenv("BU_CDP_URL", os.environ["BU_CDP_URL"] + "/")
    monkeypatch.setattr(admin, "daemon_alive", lambda _name: True)
    sock = Mock()
    monkeypatch.setattr(admin.ipc, "connect", lambda _name, timeout: (sock, None))
    methods = []

    def request(_sock, _token, req):
        methods.append(req)
        if req == {"meta": "ping"}:
            return {"pong": True, "browser_ws_url": endpoint}
        assert req == {"method": "Target.getTargets", "params": {}}
        return {"result": {"targetInfos": []}}

    def urlopen(url, timeout):
        assert url == "http://127.0.0.1:9223/json/version"
        return SimpleNamespace(read=lambda: json.dumps({
            "webSocketDebuggerUrl": "ws://127.0.0.1:9223/devtools/browser/work"
        }).encode())

    monkeypatch.setattr(admin.ipc, "request", request)
    monkeypatch.setattr(admin.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(admin.subprocess, "Popen", lambda *a, **kw: pytest.fail("must not spawn"))
    if endpoint == "ws://127.0.0.1:9223/devtools/browser/work":
        getattr(admin, entry)(name="scoped")
        assert {"method": "Target.getTargets", "params": {}} in methods
    else:
        with pytest.raises(RuntimeError, match="stop that daemon.*--reload, then re-run"):
            getattr(admin, entry)(name="scoped")
        assert methods == [{"meta": "ping"}]
    sock.close.assert_called()


@pytest.mark.parametrize("entry", ["ensure_daemon", "require_existing_daemon"])
@pytest.mark.parametrize(("configured", "explicit"), [
    (False, None),
    (False, "BU_CDP_URL"),
    (False, "BU_CDP_WS"),
    (False, "BU_BROWSER_ID"),
    (True, "BU_CDP_URL"),
    (True, "BU_CDP_WS"),
    (True, "BU_BROWSER_ID"),
])
def test_upstream_reuse_without_config_selection(config, tmp_path, monkeypatch, entry, configured, explicit):
    from browser_harness import admin

    for key in (*automation_browser.EXPLICIT, automation_browser.SELECTED_ENDPOINT):
        monkeypatch.delenv(key, raising=False)
    if explicit:
        monkeypatch.setenv(explicit, "http://127.0.0.1:9333/" if explicit == "BU_CDP_URL" else "given")
    automation_browser.apply(config=config if configured else tmp_path / "missing")
    monkeypatch.setattr(admin, "daemon_alive", lambda _name: True)
    sock = Mock()
    monkeypatch.setattr(admin.ipc, "connect", lambda _name, timeout: (sock, None))

    def request(_sock, _token, req):
        assert req == {"method": "Target.getTargets", "params": {}}
        return {"result": {"targetInfos": []}}

    monkeypatch.setattr(admin.ipc, "request", request)
    monkeypatch.setattr(admin.urllib.request, "urlopen", lambda *a, **kw: pytest.fail("must not resolve endpoint"))
    monkeypatch.setattr(admin.subprocess, "Popen", lambda *a, **kw: pytest.fail("must not spawn"))
    getattr(admin, entry)(name="scoped")


@pytest.mark.parametrize("entry", ["ensure_daemon", "require_existing_daemon"])
@pytest.mark.parametrize("explicit", automation_browser.EXPLICIT)
def test_explicit_override_after_config_selection(config, monkeypatch, entry, explicit):
    from browser_harness import admin

    for key in automation_browser.EXPLICIT:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(automation_browser.SELECTED_ENDPOINT, "")
    automation_browser.apply(config=config)
    monkeypatch.setenv(explicit, "http://127.0.0.1:9333/" if explicit == "BU_CDP_URL" else "given")
    monkeypatch.setattr(admin, "daemon_alive", lambda _name: True)
    sock = Mock()
    monkeypatch.setattr(admin.ipc, "connect", lambda _name, timeout: (sock, None))

    def request(_sock, _token, req):
        assert req == {"method": "Target.getTargets", "params": {}}
        return {"result": {"targetInfos": []}}

    monkeypatch.setattr(admin.ipc, "request", request)
    monkeypatch.setattr(admin.urllib.request, "urlopen", lambda *a, **kw: pytest.fail("must not resolve endpoint"))
    getattr(admin, entry)(name="scoped")


def test_daemon_reports_connected_endpoint(monkeypatch):
    from browser_harness import daemon

    endpoint = "ws://127.0.0.1:9223/devtools/browser/work"
    monkeypatch.setattr(daemon, "get_ws_url", lambda: endpoint)
    monkeypatch.setattr(daemon, "BROWSER_KIND", "cdp")
    monkeypatch.setattr(daemon.ipc, "expected_token", lambda: None)

    async def noop(*args, **kwargs):
        pass

    client = SimpleNamespace(start=noop, _event_registry=SimpleNamespace(handle_event=noop))
    monkeypatch.setattr(daemon, "CDPClient", lambda url: client)
    instance = daemon.Daemon()
    monkeypatch.setattr(instance, "attach_first_page", noop)

    async def connect_and_ping():
        assert (await instance.handle({"meta": "ping"}))["browser_ws_url"] is None
        await instance.start()
        assert (await instance.handle({"meta": "ping"}))["browser_ws_url"] == endpoint

    asyncio.run(connect_and_ping())


@pytest.mark.parametrize("saved", [{}, {"disabled": False}])
def test_telemetry_controls_remain_off_without_writes(tmp_path, monkeypatch, capsys, saved):
    config_dir = tmp_path / "telemetry"
    monkeypatch.setattr(telemetry, "_config_dir", lambda: config_dir)
    if saved:
        config_dir.mkdir()
        (config_dir / "telemetry.json").write_text(json.dumps(saved))
    before = (config_dir / "telemetry.json").read_bytes() if saved else None
    for enabled in (True, False):
        result = telemetry.set_enabled(enabled)
        assert result["enabled"] is False
        assert result["install_id"] is None
    for command in ("status", "disable"):
        assert telemetry.run_telemetry_cli([command]) == 0
        result = json.loads(capsys.readouterr().out)
        assert result["enabled"] is False
        assert result["install_id"] is None
    assert telemetry.run_telemetry_cli(["enable"]) == 0
    assert "disabled in this fork" in capsys.readouterr().out
    if saved:
        assert (config_dir / "telemetry.json").read_bytes() == before
    else:
        assert not config_dir.exists()
