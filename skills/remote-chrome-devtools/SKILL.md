---
name: remote-chrome-devtools
description: Diagnose and set up Chrome DevTools MCP on remote Linux desktops. Use when Codex detects a chrome-devtools MCP server configured with --browser-url=http://127.0.0.1:9222, when VNC/X11 desktop services are running, when Chrome DevTools MCP cannot connect to Chrome, or when a remote Linux environment needs a controllable browser for Chrome DevTools MCP.
---

# Remote Chrome DevTools

## Purpose

Use this skill to recognize the remote-Linux-with-desktop pattern and make
Chrome DevTools MCP usable by starting Chrome with a remote debugging endpoint.

## Detection

Check for both conditions before treating this as the remote desktop path:

1. A local MCP config contains a `chrome-devtools` server using
   `--browser-url=http://127.0.0.1:9222`.
2. A remote desktop is running, usually VNC plus X11/Wayland.

Useful checks:

```bash
rg -n 'mcp_servers\\.chrome-devtools|chrome-devtools-mcp|browser-url=http://127\\.0\\.0\\.1:9222' \
  ~/.codex/config.toml .mcp.json .vscode/mcp.json 2>/dev/null || true
pgrep -af 'Xtigervnc|Xvnc|x11vnc|vncserver|wayvnc|gnome-session|xfce4-session|startplasma|Xorg|Xwayland' || true
ss -ltnp '( sport = :9222 )' || true
```

If MCP is configured for `127.0.0.1:9222` and VNC/desktop processes are
present, assume Chrome must be started inside that remote desktop session with
remote debugging enabled. The MCP server will not launch that browser for this
configuration; it connects to the browser that is already listening on port
9222.

## Start Chrome

Prefer the stable Chrome binary and a dedicated temporary profile:

```bash
/usr/bin/google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile-stable
```

Run the command in the remote desktop environment, not in a headless SSH-only
context. If DISPLAY is not inherited, inspect the running desktop and export it
before starting Chrome:

```bash
echo "$DISPLAY"
pgrep -af 'Xorg|Xvnc|Xtigervnc|Xwayland'
export DISPLAY="${DISPLAY:-:1}"
```

If an old Chrome instance blocks startup, first inspect it. Only kill Chrome
after deciding it is the stale debug browser for this dev environment:

```bash
pgrep -af 'google-chrome|chrome.*remote-debugging-port=9222'
```

## Verify

Verify the debugging endpoint before using MCP tools:

```bash
curl -fsS http://127.0.0.1:9222/json/version
```

Then call the Chrome DevTools MCP page-listing tool. A healthy setup returns at
least one page, commonly `chrome://new-tab-page/`.

When the MCP tool still fails, check:

- Chrome was started on the same remote Linux host as the MCP server.
- Port `9222` is listening on `127.0.0.1`.
- The user data dir is writable and not locked by another Chrome process.
- VNC/desktop session is still alive.

## Source

The Chrome DevTools MCP README documents `chrome-devtools-mcp@latest`, the
`--browser-url=http://127.0.0.1:9222` mode, and that this mode connects to an
already-running browser instead of starting one automatically:
<https://github.com/ChromeDevTools/chrome-devtools-mcp>.
