# Bundled runtimes (route B)

Source: AutoML `packaging/macos/package.sh` (2026-10-09). Every item here broke or nearly
broke that build.

## Why not the runtime you already have

| Candidate | Problem |
|---|---|
| A venv | `bin/python` is a link to the system or Homebrew Python. Every script has an absolute shebang. |
| Homebrew `node` | Links 16 libraries from `/opt/homebrew/opt/...` (openssl, icu4c, libuv, ...). |
| python-build-standalone | Portable. Links only `/usr/lib` and `/System`. **Use it.** |
| nodejs.org `node-vX-darwin-arm64.tar.xz` | Portable. Links only system frameworks. **Use it.** |

Pin the versions in the build script. Verify the downloads: python-build-standalone publishes
`SHA256SUMS` per release; nodejs.org publishes `SHASUMS256.txt` per version.
Only `node/bin/node` and its `LICENSE` go into the bundle.

## Python packages

- Install into the standalone Python directly: `python/bin/python3 -m pip install -r requirements-app.txt`.
  Remove test and lint tools from the requirements first.
- Delete `lib/python3.*/{test,idlelib,tkinter,turtledemo}`; the test suite is about 100 MB.
- Cache the result. Key the cache on the hash of the requirements file plus the Python archive name.

## Hidden dependencies: rpaths

`otool -L` shows `@rpath/libomp.dylib`, which looks fine. The rpath list (`otool -l`, `LC_RPATH`)
decides where `@rpath` points. The xgboost and lightgbm macOS wheels set it to
`/opt/homebrew/opt/libomp/lib`. On a Mac without Homebrew, `import xgboost` crashes.

The build machine has Homebrew, so every test there passes. That is why
`check-macho-deps.sh` reports an rpath that **exists** on this machine as an error.

Fix used in AutoML: point the library at a portable copy that is already in the bundle, and
delete the Homebrew rpath so the build machine cannot find the old one.

```bash
lib=site-packages/xgboost/lib/libxgboost.dylib
install_name_tool -delete_rpath /opt/homebrew/opt/libomp/lib "$lib"
install_name_tool -add_rpath "@loader_path/../../sklearn/.dylibs" "$lib"
```

The sklearn wheel carries a delocated `libomp.dylib`. Sharing one copy between sklearn,
xgboost and lightgbm also avoids OpenMP error #15 (two copies initialised). torch keeps its own.
`install_name_tool` changes the file, so do it before signing.

Prove it at run time, inside the bundled Python (the hardened runtime ignores `DYLD_*`):

```python
import os, subprocess, xgboost, lightgbm
out = subprocess.run(["lsof", "-p", str(os.getpid())], capture_output=True, text=True).stdout
print([l.split()[-1] for l in out.splitlines() if "libomp" in l])
```

Every path must be inside the bundle.

## Read the wrong-looking output carefully

- `otool -L` line 2 of a dylib is its own install name, not a dependency. Wheels repaired by
  `delocate` use `/DLC/<pkg>/...` names. Compare with `otool -D`.
- A universal (fat) file prints a `<file> (architecture arm64):` header line per slice.
- `/Users/runner/...` rpaths come from the wheel's CI build. They do not exist on a customer
  Mac, so dyld skips them. `--strict` reports them anyway.

## Server dependencies become local

Prefer settings that the app already has over code changes. AutoML needed none:

| Server | Local replacement (env) |
|---|---|
| Postgres | `DATABASE_URL=sqlite:///<data>/app.db` |
| Redis + Celery worker | `CELERY_EAGER=true` (+ `AUTOML_BACKGROUND=true` so a long job does not block a request) |
| MinIO | `STORAGE_BACKEND=local`, `LOCAL_STORAGE_DIR=<data>/storage` |

Check the cookie mode: a production setting that sends `Secure` cookies breaks sign-in on
`http://127.0.0.1`.

## Front end

- `NEXT_PUBLIC_*` values are compiled into the JavaScript. Build a separate web output for the
  app, with the app's API port. Check it: `grep -rl '127.0.0.1:<port>' .next/static`.
- Before you change a proxy rule, find how the browser really calls the API. In AutoML the
  browser calls `NEXT_PUBLIC_API_URL` directly; the `/api` rewrite in `next.config.mjs` was unused.
- Build from a copy (`cp -c` makes APFS clones, no extra disk), so the developer's `.next` stays intact.
- Bundle `.next/standalone`, then copy `.next/static` and `public` into it (same as the Dockerfile).
