---
name: remote-chrome-devtools
description: Diagnose and set up Chrome DevTools MCP or a standalone Chrome DevTools Protocol endpoint on remote Linux. Use when chrome-devtools MCP cannot connect, when MCP is configured with --browserUrl or --browser-url for http://127.0.0.1:9222, when a remote desktop or headless Linux environment needs a controllable Chrome, or when Chrome is missing and the user may need native install guidance or a browser container fallback.
---

# Remote Chrome DevTools

## Purpose

Use this skill to make a remote Linux environment expose a controllable Chrome
instance. Support four common paths:

1. Existing agent MCP config connects to a running Chrome on `127.0.0.1:9222`.
2. No MCP config exists; start Chrome alone and verify the Chrome DevTools
   Protocol (CDP) endpoint.
3. No VNC or desktop exists; start headless Chrome.
4. Chrome is not installed; recommend native installation or a Chrome container.

## Inventory First

Collect enough facts to choose a path. Do not assume VNC, MCP config, or Chrome
is present.

```bash
rg -n 'mcp_servers\.chrome-devtools|chrome-devtools-mcp|browser(-url|Url)[= ]http://127\.0\.0\.1:9222' \
  ~/.codex/config.toml .mcp.json .vscode/mcp.json 2>/dev/null || true
command -v google-chrome google-chrome-stable chromium chromium-browser 2>/dev/null || true
pgrep -af 'chrome|chromium|Xtigervnc|Xvnc|x11vnc|vncserver|wayvnc|gnome-session|xfce4-session|startplasma|Xorg|Xwayland' || true
printf 'DISPLAY=%s WAYLAND_DISPLAY=%s\n' "${DISPLAY:-}" "${WAYLAND_DISPLAY:-}"
ls -1 /tmp/.X11-unix 2>/dev/null || true
ss -ltnp '( sport = :9222 )' || true
curl -fsS http://127.0.0.1:9222/json/version 2>/dev/null || true
```

Use the results to decide:

- `curl /json/version` works: reuse the running endpoint.
- MCP config exists with `--browserUrl` or `--browser-url`: ensure the browser
  endpoint is alive.
- Desktop or VNC exists: start visible Chrome in that session.
- No desktop/VNC: start native headless Chrome if a binary exists.
- No Chrome binary: offer install guidance or a Docker browser fallback.

## Native Chrome Command

Pick the first available binary instead of hard-coding one path:

```bash
CHROME_BIN="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser)"
: "${CHROME_BIN:?Chrome or Chromium is not installed}"
```

Always use a dedicated debugging profile. The remote debugging port gives local
processes browser control, so keep it bound to loopback unless a container or VM
boundary requires explicit port publishing.

```bash
CHROME_PROFILE=/tmp/chrome-devtools-profile
```

## Start With Desktop Or VNC

Use this when the user needs to see or interact with the browser through the
remote desktop.

```bash
printf 'DISPLAY=%s WAYLAND_DISPLAY=%s\n' "${DISPLAY:-}" "${WAYLAND_DISPLAY:-}"
ls -1 /tmp/.X11-unix 2>/dev/null || true
pgrep -af 'Xorg|Xvnc|Xtigervnc|Xwayland|gnome-session|xfce4-session|startplasma' || true
```

If `DISPLAY` is empty, infer it from the active X socket instead of defaulting
blindly:

```bash
export DISPLAY="${DISPLAY:-$(ls /tmp/.X11-unix/X* 2>/dev/null | sed -n 's#.*/X#:#p' | head -n1)}"
: "${DISPLAY:?No DISPLAY found; use the headless path instead}"
```

Start Chrome:

```bash
"$CHROME_BIN" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir="$CHROME_PROFILE"
```

If Chrome refuses to start because the profile is locked, inspect existing
processes first and only stop the stale debug browser for this dev environment.

```bash
pgrep -af 'google-chrome|chromium|remote-debugging-port=9222'
```

## Start Headless Without VNC

Use this when no desktop is running or the task only needs automation,
screenshots, logs, performance traces, or page inspection.

```bash
nohup "$CHROME_BIN" \
  --headless=new \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir="$CHROME_PROFILE" \
  --disable-gpu \
  about:blank > /tmp/chrome-devtools.log 2>&1 < /dev/null &
```

If running as root inside a disposable container and Chrome exits with the
sandbox error, retry with `--no-sandbox`. Do not add `--no-sandbox` by default on
normal hosts.

## No MCP Config

If the user only needs a browser endpoint, starting Chrome and verifying
`http://127.0.0.1:9222/json/version` is enough. This is useful for standalone
CDP clients, scripts, or manual debugging.

If they need Chrome DevTools MCP without a saved agent config, run the MCP server
as a one-off command in whatever client or proxy they are using:

```bash
npx -y chrome-devtools-mcp@latest --browserUrl http://127.0.0.1:9222
```

For a fully headless MCP-managed browser, an MCP client can also launch Chrome
itself with:

```bash
npx -y chrome-devtools-mcp@latest --headless=true --isolated=true
```

This still requires the MCP client to connect to that stdio server. Starting the
stdio command in a random terminal does not by itself expose tools to the agent.

## No Chrome Installed

When no Chrome or Chromium binary is found, do not keep debugging the MCP layer.
Pick one of these options:

- Native install: tell the user Chrome/Chromium is missing and offer to install
  with the host package manager if that is appropriate for the machine.
- Chrome for Testing or a pinned Chrome package: use when the environment needs a
  repeatable native binary path for `--executable-path`.
- Docker fallback: use when package installation is not allowed or the host is
  intentionally minimal.

Before installing packages or starting containers, check whether the user expects
persistent host changes.

## Docker Fallbacks

Use Docker only when the host has Docker access and native Chrome is unavailable
or undesirable. If the MCP server runs on the host, it must be able to reach the
Chrome debug endpoint from the host.

### Generic Headless Chrome Container

Some Chrome builds still advertise DevTools on `127.0.0.1` inside the container
even when passed `--remote-debugging-address=0.0.0.0`, which makes ordinary
Docker port publishing unusable. On Linux hosts, prefer `--network host` for a
CDP-only container and bind Chrome to host loopback. Use this only after checking
that host port `9222` is free, because host networking shares the host network
namespace and can conflict with local services.

```bash
docker run --rm -d --name chrome-cdp \
  --network host \
  --shm-size=1gb \
  --entrypoint /opt/google/chrome/google-chrome \
  kasmweb/chrome:1.18.0 \
  --headless=new \
  --no-sandbox \
  --disable-gpu \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-devtools-profile \
  about:blank
```

If host networking is unavailable, first prove that Chrome is actually listening
on a non-loopback container interface before using `-p 127.0.0.1:9222:9222`. If
the image entrypoint does not allow replacing the command cleanly, inspect the
image docs or shell into the container rather than guessing. For rootless or
locked-down Docker, permissions and sandboxing may require a different image or
runtime flags.

Do not combine `--network host` with the default Kasm browser UI entrypoint. The
default Kasm container starts UI/audio/upload/gamepad services in addition to the
browser, commonly including ports `6901`, `4901-4904`, and `8081`; exposing those
through host networking can collide with or expose host services unexpectedly.

### Browser-In-A-Container UI Images

`kasmweb/chrome` provides browser-accessible Chrome through KasmVNC and supports
passing Chrome arguments via `APP_ARGS`; its documented standalone deployment
publishes the web UI on `6901` with `VNC_PW`. Use it when the user wants a web
visible browser, and add remote debugging arguments through the image-supported
mechanism.

```bash
docker run --rm -d --name kasm-chrome \
  --shm-size=512m \
  -p 127.0.0.1:6901:6901 \
  -p 127.0.0.1:9222:9222 \
  -e VNC_PW=password \
  -e APP_ARGS='--remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-devtools-profile' \
  kasmweb/chrome:1.18.0
```

`linuxserver/chrome` provides a browser UI on ports `3000` and `3001` and uses a
persistent `/config` volume. Use it when linuxserver.io conventions fit the host,
especially when the user wants the browser UI rather than a minimal CDP-only
container. Its documented `CHROME_CLI` environment variable passes CLI flags to
Chrome, but do not assume `CHROME_CLI` plus `-p 127.0.0.1:9222:9222` exposes a
usable CDP endpoint; first verify `/json/version`.

```bash
docker run -d --name chrome \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e CHROME_CLI='--remote-debugging-address=0.0.0.0 --remote-debugging-port=9222' \
  -p 127.0.0.1:3000:3000 \
  -p 127.0.0.1:3001:3001 \
  -p 127.0.0.1:9222:9222 \
  -v /tmp/linuxserver-chrome:/config \
  --shm-size=1gb \
  lscr.io/linuxserver/chrome:latest
```

For a Linux `linuxserver/chrome` CDP-only fallback, bypass the UI entrypoint and
use the same host-network pattern as the generic headless path:

```bash
docker run --rm -d --name chrome-cdp \
  --network host \
  --shm-size=1gb \
  --entrypoint /opt/google/chrome/google-chrome \
  lscr.io/linuxserver/chrome:latest \
  --headless=new \
  --no-sandbox \
  --disable-gpu \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-devtools-profile \
  about:blank
```

Do not claim these UI containers expose CDP until `curl` proves port `9222` is
reachable.

## Verify

Verify the endpoint before using MCP tools:

```bash
curl -fsS http://127.0.0.1:9222/json/version
curl -fsS http://127.0.0.1:9222/json/list
```

Then call the Chrome DevTools MCP page-listing tool if the current agent has one.
A healthy setup returns at least one page, commonly `about:blank` or a new tab.

When MCP still fails, check:

- Chrome was started on the same host or container network reachable by the MCP
  server.
- The MCP `--browserUrl` port matches the Chrome `--remote-debugging-port`.
- Port `9222` is bound to `127.0.0.1` on the host, or deliberately published from
  Docker.
- The user data dir is writable and not locked by another Chrome process.
- Desktop-specific failures are not being diagnosed with the headless path, or
  vice versa.

## Sources

- Chrome DevTools MCP documents `chrome-devtools-mcp@latest`, `--headless`,
  `--browserUrl http://127.0.0.1:9222`, and that `--browserUrl` connects to an
  already-running browser: <https://github.com/ChromeDevTools/chrome-devtools-mcp>.
- Docker Hub documents the `kasmweb/chrome` standalone browser UI image:
  <https://hub.docker.com/r/kasmweb/chrome>.
- Docker Hub documents the `linuxserver/chrome` browser UI image:
  <https://hub.docker.com/r/linuxserver/chrome>.
