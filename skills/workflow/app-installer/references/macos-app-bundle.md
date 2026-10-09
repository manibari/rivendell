# macOS app bundle, signing and DMG

Source: cadcraft `packaging/macos/package.sh` and AutoML `packaging/macos/package.sh`.

## The .app is a folder

```
<App>.app/Contents/
  Info.plist              identity: name, bundle id, version, minimum macOS, file types
  PkgInfo                 the 8 bytes "APPL????"
  MacOS/<App>             the executable (CFBundleExecutable); for route B, the launcher
  Resources/<App>.icns    the icon (CFBundleIconFile, no extension)
  Resources/...           runtimes, code, assets
  _CodeSignature/         written by codesign; a hash of every file
```

Info.plist keys that matter:

- `CFBundleIdentifier`: a reverse domain you own. Set it before the first release and never
  change it. macOS keys permissions and preferences on it.
- `CFBundleShortVersionString` / `CFBundleVersion`: numeric `X.Y.Z`. Fill them from the repo
  version with `sed` on an `Info.plist.in` template. Run `plutil -lint` on the result.
- `LSMinimumSystemVersion`: keep it equal to `MACOSX_DEPLOYMENT_TARGET` of the build.

Icon: `sips -s format png -z N N <src.svg|png>` for N in 16 32 128 256 512 and the `@2x`
sizes into `<App>.iconset/icon_NxN[@2x].png`, then `iconutil -c icns`.

## Signing levels

| Level | Command | Result |
|---|---|---|
| Ad-hoc | `codesign --sign -` | Runs on the build Mac only. `spctl --assess` says `rejected`. |
| Developer ID | `codesign --sign "Developer ID Application: ..." --timestamp` | Has an identity. Gatekeeper still wants notarization. |
| Notarized | `xcrun notarytool submit --wait`, then `xcrun stapler staple` | Gatekeeper accepts it, offline too (the ticket is stapled). |

A missing certificate is a warning, not a failure: fall back to ad-hoc so local builds work.

Sign inside-out: every nested Mach-O first, then the bundle. Do not use `--deep` for the
final signature. Find the nested files with `file -b | grep Mach-O` over
`*.so`, `*.dylib` and executables; route B has about 560 of them.

Verify: `codesign --verify --strict --deep <App>.app`, then `spctl --assess --type execute -vv`.

## Hardened runtime and entitlements

Notarization requires `--options runtime`. It blocks some behaviour unless the
`entitlements.plist` allows it. Give each exception a reason in a comment.

| Entitlement | Needed by |
|---|---|
| none | A pure Rust app (cadcraft) |
| `com.apple.security.cs.allow-jit` | Node (V8), numba/llvmlite |
| `com.apple.security.cs.allow-unsigned-executable-memory` | V8, llvmlite |
| `com.apple.security.cs.disable-library-validation` | Python loading wheel libraries with no shared Team ID. Check again after Developer ID signing. |

Side effect: the hardened runtime ignores every `DYLD_*` variable. `DYLD_PRINT_LIBRARIES`
prints nothing. To see which libraries a process loaded, run `lsof -p <pid>` from inside it.

## The bundle is read-only

Any write into the bundle breaks the signature. Python writes `.pyc` files by default, so:
precompile at build time (`python -m compileall -j 0`), and run with `-B`.

## DMG

```bash
mkdir -p stage && ditto <App>.app stage/<App>.app && ln -s /Applications stage/Applications
hdiutil makehybrid -hfs -hfs-volume-name "<App> <version>" -hfs-openfolder stage -o raw.dmg stage
hdiutil convert raw.dmg -format UDZO -imagekey zlib-level=9 -o <app>-<version>-macos-<arch>.dmg
codesign --sign <identity> <app>.dmg      # then notarize and staple the DMG too
```

Use `makehybrid` + `convert`, not `hdiutil create -srcfolder`: `create` attaches a device and
fails on CI runners with "Resource busy".

Sizes measured: cadcraft 28 MB app, 11 MB DMG. AutoML 1.6 GB app (torch 437 MB), 451 MB DMG.
