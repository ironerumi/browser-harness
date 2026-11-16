# browser-harness CLI — one-time install prerequisite

This is a **one-time prerequisite**, not part of the regular AI workflow. Do it once; after `browser-harness` prints page info, never repeat install/connection steps during normal browser work.

## Install the command and register the skill

Follow [the fork's installation guide](../../../install.md#fast-path), which owns
checkout installation and skill registration.

## Connect to a browser

See [automation browser selection](../../../install.md#automation-browser-selection)
for the configured identity and explicit-endpoint rules. Quick check:

```bash
browser-harness <<'PY'
print(page_info())
PY
```

If that prints page info, you're done. If not, run `browser-harness --doctor`.
On hosts without the automation-browser config, the two local connection methods are:

- **Way 1 (real browser):** open Chrome normally, then open `chrome://inspect/#remote-debugging` and tick "Allow remote debugging for this browser instance". On Chrome 144+, click Allow on the first-attach popup. Inherits your logins/extensions — best when the agent acts in your everyday browser.
- **Way 2 (isolated profile, no popups):** launch Chrome with `--remote-debugging-port=9222 --user-data-dir=<non-default path>`, then set `BU_CDP_URL=http://127.0.0.1:9222`. Best for unattended automation.

If the quick path fails after `--doctor`, inspect `src/browser_harness/admin.py`, `src/browser_harness/daemon.py`, and `src/browser_harness/_ipc.py`.

## Keeping current

See [installation troubleshooting](../../../install.md#if-still-broken) for fork
updates and state locations, and [telemetry policy](../../../install.md#telemetry).
