# Windows, Linux and the CI release

Status: **read from cadcraft, not built and tested in rivendell yet** (2026-10-09).
State this to the user when you use it, and test on the target OS before you call it done.
Source files: `~/Code/Artcraft/cadcraft/packaging/{windows,linux}/`, `.github/workflows/release.yml`,
`docs/releasing.md`.

## Windows: MSI with WiX v5

- Install: `dotnet tool install --global wix --version 5.0.2`. Build:
  `wix build <app>.wxs -arch x64 -d Version=X.Y.Z -d BinDir=... -o out.msi`.
- `UpgradeCode`: a fixed GUID. Set it once and never change it. A new code makes Windows treat
  the next version as a different product, and both stay installed.
- `<MajorUpgrade AllowSameVersionUpgrades="yes">`: MSI versions are numeric only, so
  `1.2.3-rc.1` and `1.2.3-rc.2` are both `1.2.3`. Without this flag the second one does not
  replace the first.
- Install per machine into `ProgramFiles6432Folder`, a Start Menu shortcut, and file
  associations through `HKLM\Software\Classes\.<ext>\OpenWithProgids` ("Open with", not the default app).
- Link the C runtime statically (`-C target-feature=+crt-static` for the MSVC target), so the
  customer needs no Visual C++ redistributable.
- Targets: x64, x86, arm64 (arm64 cross-compiles on the x64 runner). Signing: Azure Trusted
  Signing in `sign.ps1`; skipped with a warning when the secrets are missing.

## Linux: deb, rpm, AppImage, Flatpak

- `nfpm` builds deb and rpm from one `nfpm.yaml`: list runtime libraries in `depends`, and
  optional ones in `recommends`. A Rust GUI links only glibc and libgcc directly; windowing and
  GPU libraries load at run time, so they are package dependencies, not ELF `NEEDED` entries.
- `version_schema: semver` turns `0.2.0-rc.1` into `0.2.0~rc.1`, so a pre-release sorts before the release.
- Build on the oldest supported distro (ubuntu-22.04 runner = glibc 2.35). A binary built on a
  newer glibc does not start on an older one.
- `postinst.sh` refreshes the desktop, MIME and icon caches; each tool is optional.
- AppImage carries update information, and a `.zsync` file next to it gives delta updates.

## CI release (GitHub Actions)

- One `version` job reads the version from the repo and checks the format; all other jobs use its output.
- Only the jobs that sign (macOS, Windows) and the job that drafts the release use the
  `release` environment, which holds the secrets and deploys only from the `release` branch.
  Linux, web and FreeBSD jobs get no secrets. A manual run on another branch is then a safe dry run.
- Every secret is optional: a missing one gives an unsigned artifact and a warning.
- `concurrency` with `cancel-in-progress: false`: never cancel a run in the middle of notarization.
- The last job writes `SHA256SUMS.txt` and creates or updates a **draft** release. If that
  version is already published, it fails and asks for a version bump.
