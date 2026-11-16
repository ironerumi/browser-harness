---
name: browser-install
description: Install browser-harness and connect it to a browser fast.
---

# browser-harness install

Use once. For browser work, read `SKILL.md`.

## Fast Path

```bash
# From a durable checkout of this fork:
uv tool install --python 3.12 --editable .
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills/browser-use"
browser-harness skill > "${CODEX_HOME:-$HOME/.codex}/skills/browser-use/SKILL.md"
browser-harness <<'PY'
print(page_info())
PY
```

If `page_info()` prints, configure recording consent below, then stop.

Keep the editable checkout in place. Installing `browser-harness` or `browser-use`
from PyPI alone does not install this fork's browser-selection or telemetry policy.
Dependency versions are owned by `pyproject.toml`.

For Claude Code or other agents: install this fork, register a skill named `browser-use`, use `browser-harness skill` as the body, and use this trigger:

```text
Always use browser-harness for any web interaction: automation, scraping, testing, or site/app work.
```

Replace stale user-installed browser skills with this fork's skill. Do not edit bundled/vendor plugin caches.

## Automation browser selection

Both `browser-harness` and `browser-harness-mcp` read
`~/.config/automation-browser/config`, provisioned by dotfiles
`scripts/setup-automation-browser.sh`. With `kind=chrome`, a `BU_NAME` starting
with `ai-search` selects `ai-search.port`; every other name, including no name,
selects `work.port`. These ports are used on `127.0.0.1`.

An explicit `BU_CDP_URL`, `BU_CDP_WS`, or `BU_BROWSER_ID` overrides this selection.
Without the config file, upstream browser discovery is unchanged. With the file,
a non-Chrome kind or missing/non-numeric identity port stops with setup instructions
instead of falling back to everyday Chrome.

For config-selected endpoints, a reused daemon must prove it is attached to the
selected browser. A mismatched or unverifiable daemon is refused; stop it with
`BU_NAME=<same-name> browser-harness --reload`, then retry (use `default` when no
name was set).

## Telemetry

Telemetry is hard-disabled in this fork because upstream sends task scripts and
output tails to PostHog, while this fork drives logged-in work pages.
`browser-harness telemetry status` reports `enabled: false` without creating an
installation ID. `telemetry enable` cannot enable it; `telemetry disable` reports
the effective state without changing preferences. Local recording consent is
separate.

## Recording Consent

Run `browser-harness recordings`. If it reports `(default)`, ask the user once:

> Enable local browser recordings? This saves screenshots and action traces on
> this machine, which may include sensitive page content, so you can later ask
> “show me what you did” or request a video. Videos are never generated
> automatically. [y/N]

Default to no. Run `browser-harness recordings enable` only after yes; otherwise
run `browser-harness recordings disable`. Preserve an existing `(config)` or
`(BH_RECORD)` preference during upgrades instead of asking again.

## If Chrome Blocks It

In Chrome:

1. Open `chrome://inspect/#remote-debugging`.
2. Tick "Allow remote debugging for this browser instance".
3. Retry `page_info()`.

If that reports `permission-blocked` on macOS, handle the per-connection Allow
sheet without bringing Chrome to the foreground:

```bash
browser-harness mac-approve
```

Continue browser work when the helper returns `ready`; otherwise follow its
printed instruction. The first checkbox is intentionally a one-time manual
Chrome setup step; it is not exposed to the harness until CDP is available.

The helper requires Accessibility permission for the app launching the CLI
(for example Terminal, iTerm, Codex, or an IDE) in System Settings.

## Cloud Browsers

Cloud is optional. Local Chrome does not need a Browser Use API key.

Use any short made-up name; `r7k2` below is just a placeholder.

```bash
browser-harness auth login
browser-harness <<'PY'
start_remote_daemon("r7k2")
PY
```

Then use it by name:

```bash
BU_NAME=r7k2 browser-harness <<'PY'
print(page_info())
PY
```

## If Still Broken

```bash
browser-harness --doctor
```

Use the output:

- `chrome running` FAIL: ask the user to open Chrome, or use isolated/cloud browser.
- `daemon alive` FAIL: Chrome remote debugging permission is missing, Chrome is closed, or the CDP endpoint is not reachable.
- update available: update this fork's checkout deliberately. `--update` checks PyPI versions before updating; it pulls Git checkouts but upgrades PyPI installations from PyPI.

For a machine-readable health check, an orchestrator can set `BU_NAME` to an
already-provisioned daemon and run:

```bash
browser-harness doctor --json --require-existing-daemon
```

This prints a versioned JSON report and exits nonzero unless that exact daemon
has a live browser connection. It never starts or discovers another browser.

If this still fails, inspect `src/browser_harness/admin.py`, `src/browser_harness/daemon.py`, and `src/browser_harness/_ipc.py`.

Useful:

```bash
browser-harness telemetry status
```

State lives under `${XDG_CONFIG_HOME:-~/.config}/browser-harness` by default: auth, agent workspace, runtime sockets, logs, screenshots, and temp files. Override with `BH_HOME` or `BROWSER_HARNESS_HOME`.
