"""Attach to this machine's automation browser by identity (ironerumi fork).

The machine's automation browser is declared in ~/.config/automation-browser/config
(dotfiles scripts/setup-automation-browser.sh): one Chrome per identity, each on a
fixed loopback port. The identity comes from BU_NAME: a name starting with
`ai-search` attaches to the `ai-search` Chrome, any other name (or none) to `work`.
An explicit BU_CDP_URL / BU_CDP_WS / BU_BROWSER_ID wins, and a machine without the
config file keeps upstream's local Chrome discovery.
"""
from __future__ import annotations

import os
from collections.abc import MutableMapping
from pathlib import Path

CONFIG = Path.home() / ".config" / "automation-browser" / "config"
EXPLICIT = ("BU_CDP_URL", "BU_CDP_WS", "BU_BROWSER_ID")
SELECTED_ENDPOINT = "_BH_AUTOMATION_BROWSER_ENDPOINT"


def identity_for(name: str) -> str:
    return "ai-search" if name.startswith("ai-search") else "work"


def read_config(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip()] = value.strip()
    return values


def apply(env: MutableMapping[str, str] = os.environ, config: Path | None = None) -> None:
    """Set BU_CDP_URL for BU_NAME's identity; exit naming the fix when that is impossible."""
    config = config or CONFIG
    if any(env.get(name) for name in EXPLICIT) or not config.is_file():
        return
    values = read_config(config)
    kind = values.get("kind", "")
    if kind != "chrome":
        raise SystemExit(
            f"no automation browser on this machine (kind={kind or 'missing'} in {config}); "
            "run dotfiles scripts/setup-automation-browser.sh on a chrome host, or set BU_CDP_URL"
        )
    identity = identity_for(env.get("BU_NAME") or "default")
    port = values.get(f"{identity}.port", "")
    if not port.isdigit():
        raise SystemExit(f"no {identity}.port in {config}; re-run dotfiles scripts/setup-automation-browser.sh")
    env["BU_CDP_URL"] = f"http://127.0.0.1:{port}"
    env[SELECTED_ENDPOINT] = env["BU_CDP_URL"]
