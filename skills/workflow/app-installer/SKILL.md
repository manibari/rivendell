---
name: app-installer
loop: dev
pdca: do
description: >
  Package a product as an installer a customer opens with no developer tools: a macOS .app
  in a DMG, a Windows MSI, Linux deb/rpm/AppImage. Two routes: a native single binary
  (Rust, like cadcraft) or an app that carries its own Python/Node runtimes and starts local
  servers (like AutoML.app). Owns check-macho-deps.sh, the clean-machine dependency check.
  TRIGGER: "安裝檔", "做成 dmg", "打包成一包", "桌面 app", "不用 docker 跑", "msi",
  "installer", "notarize", "codesign", or a .app that works here but fails on another Mac.
  SKIP: containers or docker-compose (docker-compose-setup); cloud hosting (deploy);
  CI test pipelines (ci-pipeline).
version: 1.0.0
tags: [packaging, installer, macos, release]
user_invocable: true
allowed-tools: "Read, Write, Edit, Bash, Grep, Glob"
---

# App Installer

The leading word is **clean machine**: a Mac or PC that has only the OS. No Homebrew, no
Python, no Node, no repo. An installer is done when it runs on a clean machine. The build
machine is the worst test machine, because it has every library and path the app forgot.

Reference implementations (read them before you copy a part):

| Route | Reference | What it shows |
|---|---|---|
| A. Native binary | `~/Code/Artcraft/cadcraft/packaging/` | .app/DMG, MSI (WiX), deb/rpm (nfpm), CI release with signing secrets |
| B. Bundled runtimes | `~/Code/Norns-Verdandi-AutoML/packaging/macos/` | Python + Node + 2 local servers, Rust launcher, data outside the bundle |

## Step 0: Pick the route

Ask what runs inside the product, then pick one row:

| Product | Route |
|---|---|
| One compiled binary (Rust, Go) | **A**. The binary is the app. |
| Python/Node services, one user per machine | **B**. Replace server dependencies with local ones through env (SQLite, in-process jobs, local folder), then bundle the runtimes. |
| Services shared by many users (Postgres, workers, SSO) | Not this skill. Ship an offline Docker bundle (`docker save` + compose + `install.sh`); use docker-compose-setup. |

For route B, first prove the single-machine mode without packaging: run the API from the
repo with the local env and do one full user flow (sign in, create, run a job).

**Done when:** the route is chosen, and for route B one user flow passed in single-machine mode.

## Step 1: Make the runtimes portable (route B)

Read [references/bundled-runtimes.md](references/bundled-runtimes.md). Then:

1. Use python-build-standalone and the nodejs.org build. Do not copy a venv or a Homebrew binary.
2. Install the app requirements into that Python (no venv). Leave out test and lint tools.
3. Build the web front end with the app's API address. `NEXT_PUBLIC_*` values are fixed at build time.
4. Run the clean-machine check on the runtime directories:

```bash
~/Code/rivendell/skills/workflow/app-installer/scripts/check-macho-deps.sh <runtime-dir>
```

**Done when:** the check exits 0. Every `RPATH ... EXISTS here` line is fixed, not ignored.

## Step 2: Assemble and sign the bundle

Read [references/macos-app-bundle.md](references/macos-app-bundle.md). Write `packaging/macos/package.sh`
that does every step again from nothing, with downloads cached and checksums verified.

**Done when:** `codesign --verify --strict --deep <App>.app` passes, and the check script
passes on the whole `.app`.

## Step 3: Launcher (route B)

Read [references/native-launcher.md](references/native-launcher.md). The launcher is
`Contents/MacOS/<App>`. It must be a native binary: a shell script cannot receive Dock Quit.

**Done when:** all five checks below pass.

## Step 4: Verify on behavior, not on build output

Run each check and record the result. Use a temporary `HOME` to simulate a first run.

| # | Check | Pass |
|---|---|---|
| 1 | First run | Servers answer; a random password appears; the browser opens |
| 2 | One real user flow | It completes, including every native library (for example xgboost, lightgbm) |
| 3 | Relaunch | Data and password stay; no first-run dialog |
| 4 | Dock Quit / Cmd+Q | The app is gone in about 1 s; both ports are free; the log shows each server's exit |
| 5 | Force Quit (SIGKILL) | The watchdog frees both ports in a few seconds |

Then tell the user what is still open. Typical items: Developer ID signing and notarization,
an upgrade path for the data schema, other CPU architectures, other platforms.

## Rules

- **Data lives outside the bundle**: `~/Library/Application Support/<App>`, logs in
  `~/Library/Logs/<App>`. A signed bundle is read-only, and an upgrade replaces it whole.
- **Each app gets its own ports**, registered in `~/Code/rivendell/data/ports.conf`, apart from the dev ports.
- **One build script, one source of truth.** The version comes from the repo, the ports
  from the launcher; the script reads them and does not copy them.
- **Commit with care when other sessions share the repo**: stage only the packaging files.

## Other platforms

Windows, Linux and the CI release are in [references/other-platforms.md](references/other-platforms.md).
They are read from cadcraft, not built and tested yet. Say so when you use them.
