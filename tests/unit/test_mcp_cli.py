"""Tests for the optional MCP console entry point."""

import builtins
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from browser_harness import mcp_cli


def test_main_explains_missing_mcp_extra(monkeypatch):
    real_import = builtins.__import__

    def import_without_mcp(name, *args, **kwargs):
        if name == "mcp_server":
            raise ModuleNotFoundError("No module named 'mcp'", name="mcp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_mcp)

    with pytest.raises(SystemExit, match=r"pip install 'browser-harness\[mcp\]'"):
        mcp_cli.main()


@pytest.mark.parametrize("kind", ["chrome", "none"])
@pytest.mark.parametrize(("setting", "expected"), [
    ("BU_CDP_URL=http://127.0.0.1:9333", {"BU_CDP_URL": "http://127.0.0.1:9333"}),
    ("BU_CDP_WS=ws://127.0.0.1:9333/devtools/browser/test", {
        "BU_CDP_WS": "ws://127.0.0.1:9333/devtools/browser/test",
    }),
    ("BU_BROWSER_ID=test-browser", {"BU_BROWSER_ID": "test-browser"}),
    ("BU_NAME=ai-search-canary", {"BU_CDP_URL": "http://127.0.0.1:9225"}),
    ("", {"BU_CDP_URL": "http://127.0.0.1:9223"}),
])
def test_mcp_loads_dotenv_before_browser_selection(tmp_path, kind, setting, expected):
    """The identity contract requires .env overrides before machine defaults."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".env").write_text(setting + "\n")
    config = tmp_path / "automation-config"
    config.write_text(f"kind={kind}\nwork.port=9223\nai-search.port=9225\n")
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith("BU_") and key != "_BH_AUTOMATION_BROWSER_ENDPOINT"
    }
    env.update(
        BH_HOME=str(tmp_path / "home"),
        BH_CONFIG_DIR=str(tmp_path / "home"),
        BH_AGENT_WORKSPACE=str(workspace),
        PYTHONPATH=str(Path(__file__).resolve().parents[2] / "src"),
    )
    result = subprocess.run(
        [sys.executable, "-c", """
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from browser_harness import automation_browser, mcp_cli

automation_browser.CONFIG = Path(sys.argv[1])
sys.modules['mcp_server'] = SimpleNamespace(main=lambda: print(json.dumps({
    key: os.environ[key] for key in ('BU_CDP_URL', 'BU_CDP_WS', 'BU_BROWSER_ID')
    if key in os.environ
})))
mcp_cli.main()
""", str(config)],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    if kind == "none" and not setting.startswith(("BU_CDP_URL=", "BU_CDP_WS=", "BU_BROWSER_ID=")):
        assert result.returncode != 0
        assert "no automation browser on this machine" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == expected
