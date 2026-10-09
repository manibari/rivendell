# Native launcher (route B)

Source: AutoML `packaging/macos/launcher/` (Rust, winit 0.30.13 + libc, 431 KB binary).
Copy it and change the paths, ports and env. It has three files: `main.rs` (event loop),
`setup.rs` (paths, secrets, dialogs, log), `servers.rs` (start, watch, stop).

## Why it must be native

Dock Quit and Cmd+Q arrive as an Apple Event through AppKit. A shell script has no AppKit
event loop, so it never sees the event: the Dock shows "not responding" and the servers stay
up. The first AutoML launcher was bash and failed this way.

winit runs the AppKit event loop. On `applicationWillTerminate:` it calls
`ApplicationHandler::exiting()` before the process ends. Stop the servers there.
The app needs no window: the Dock icon and winit's default menu (with Quit) are enough.
`ApplicationHandler` requires `resumed` and `window_event`; leave both empty.

## What the launcher does, in order

1. Resolve `Resources` from `current_exe()`; create the data and log folders.
2. Refuse to start if a port is busy, with a dialog. macOS runs one instance per app, so a
   busy port means another program holds it.
3. First run: write `<data>/.env` with mode 0600, a random `SECRET_KEY` and admin password
   (`/dev/urandom`, a character set without look-alikes). The API reads `.env` from its
   working directory, so start the API in `<data>`.
4. Start each server with `env_clear()` plus an explicit env, stdin from `/dev/null`, output
   appended to `<logs>/<name>.log`. Python runs with `-I -B`.
5. Start the watchdog (below), write `<data>/launcher.pid`.
6. A plain thread polls both servers (HTTP/1.0 over `TcpStream`, no HTTP crate) and sends
   `Ready` through an `EventLoopProxy`. On `Ready`: open the browser, then show the first-run
   password next to the sign-in page. A dialog must never block the start.
7. `ControlFlow::WaitUntil(now + 1 s)` wakes `about_to_wait`, which calls `try_wait()` on each
   server. A server that stopped by itself ends the app with a dialog that names it.

## Stop: one grace period per server

Send SIGTERM to every server, then wait for each one up to its own grace period, then SIGKILL.
Log one line per server (`api: signal: 15 (SIGTERM) after 152ms`, `web: SIGKILL after 1s grace`).
The log line is how the 5 s hang below was found; keep it.

| Server | Grace | Reason |
|---|---|---|
| API (uvicorn + SQLite) | 5 s | It must commit. It needs about 0.2 s. |
| Web (Next.js standalone) | 1 s | It has no state. |

**The 5 s hang.** With one 5 s grace for both, Quit took 5.2 s. Node's graceful close waits
for every socket that has not sent a request yet. Chrome opens such pre-connected sockets and
keeps them while the tab is open. Reproduce it: connect a raw socket that sends nothing, then
SIGTERM node. It stays up until the socket closes. Shell tests miss this, because no browser
is connected. Result after the fix: Quit takes about 1.2 s.

## Watchdog for Force Quit

Force Quit sends SIGKILL; no code in the launcher runs after it. Start a detached shell in
its own process group (`process_group(0)`) that waits for the launcher to go, then stops the servers:

```sh
while kill -0 <launcher-pid> 2>/dev/null; do sleep 2; done; kill <api-pid> <web-pid>
```

Measured: both ports are free 2 s after SIGKILL.

## Build

`cargo build --release --locked` with `MACOSX_DEPLOYMENT_TARGET` equal to `LSMinimumSystemVersion`.
Commit `Cargo.lock`. Release profile: `opt-level = "s"`, `lto = true`, `strip = true`.
For a fast test loop, rebuild only the launcher, copy it to `Contents/MacOS/<App>`, and sign
the bundle again; the full package takes about 1.5 min.

## Known gaps

- Reopen (a click on the Dock icon while the app runs) does nothing. winit does not expose
  `applicationShouldHandleReopen:`; it needs an objc2 delegate method.
- Logout sends Quit, which works. A plain `kill` (SIGTERM) to the launcher skips `exiting()`;
  the watchdog then stops the servers.
