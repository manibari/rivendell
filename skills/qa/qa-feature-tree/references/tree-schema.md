# Feature tree schema

This file is the current contract of `docs/qa/feature-tree.json`. The design doc
(`docs/plans/2026-11-18-qa-feature-tree-skill.md` §3) has the history. When they differ,
this file is correct.

## Start file

`init` needs a file with only these three keys:

```json
{
  "schema": 1,
  "system": "rivendell-dashboard",
  "config": {
    "source_roots": ["apps/dashboard-web/src", "apps/dashboard-api/routes"],
    "route_style": "next-app",
    "route_files": ["apps/dashboard-web/src/app/**/page.tsx"],
    "e2e_dirs": ["apps/dashboard-web/e2e"],
    "e2e_report": "apps/dashboard-web/e2e/.results/report.json",
    "base_url": "http://127.0.0.1:3005"
  }
}
```

- Paths are relative to the repo root (`--repo`, default: the current directory).
- `config.ignore` (optional) is a list of globs to remove from the source files.
- `base_url` is the test instance. Never the production port.

## Levels and fields

| Level | Required fields | Optional fields |
|---|---|---|
| system | `schema` (= 1), `system`, `config` | - |
| module | `id`, `name_zh`, `paths` (globs) | `status: "planned"`, `blueprint_id` |
| screen | `id`, `route` (not for a layout screen) | `layout: true`, `sample`, `states` |
| control | `id`, `role`, `name`, `does`, `evidence`, `success`, `failure`, `cases` | `state`, `repeat: true` |
| case | `id`, `kind`, `expect` | `status: "na"` + `na_reason`, `boundary: "recorder"` |

- Each ID segment matches `^[a-z0-9]+(-[a-z0-9]+)*$` and is unique among its siblings.
- **Leaf ID** = `<module>.<screen>.<control>.<case>`. Do not reuse an ID after you remove a leaf.
- `name` is the accessible name. A name in the form `/.../` is a regular expression that must
  match the full name (use it for a repeated control, with `repeat: true`).
- `does: "unknown"` is red `UNKNOWN_PURPOSE`. An empty `evidence` is red `NO_EVIDENCE`.
- `evidence` is `file:line` of the handler, the start of the path control, then API, then store.
- `kind` is one of the seven kinds in [case-kinds.md](case-kinds.md). Each control has all seven.
- `boundary` is only `recorder`, and only on kind `side-effect`.
- Globs: `**` matches any number of folders; `*` does not cross `/`.

## Layout, states, and steps

- A screen with `"layout": true` holds the controls that show on every screen (sidebar, top
  bar). It has no `route`. The scan does not open it alone; its controls match on every screen.
- A control with no `state` belongs to the state `default`: the page right after it loads.
- `sample` gives one value for each dynamic segment: route `/agents/[label]`, sample
  `{"label": "com.sk.agent.demo"}`. A `[...x]` value can hold `/`.
- `route_style: "next-app"`: `app/<segments>/page.tsx` gives `/<segments>`. Route groups
  `(name)` are removed. `[x]`, `[...x]`, `[[...x]]` stay in the route text.

A step is one object with one key:

| Step | Value | Action |
|---|---|---|
| `click` | `{"role", "name"}` | Click `getByRole(role, {name, exact: true})` |
| `fill` | `{"role", "name", "value"}` | Type `value` into the element |
| `press` | `{"key"}` | Press one key, for example `Escape` |
| `goto` | `"/path"` | Open a path under `base_url` |
| `wait_for` | `{"role", "name"}` | Wait until the element is visible |

## Scan file (`scan.json`)

`screen_scan.mjs` writes it; `tree_check.py screens` and `adopt` read it.

```json
{
  "schema": 1,
  "base_url": "http://127.0.0.1:3005",
  "scanned_at": "2026-11-19T10:00:00+08:00",
  "screens": [
    {"module": "tokens", "screen": "main", "state": "default",
     "url": "http://127.0.0.1:3005/tokens", "reached": true, "error": null,
     "controls": [{"role": "button", "name": "重新整理"}, {"role": "link", "name": ""}]}
  ]
}
```

- One entry for each non-layout screen and state, including `default`.
- `reached: false` and a Chinese text in `error` when the page or a step fails; then
  `controls` is empty.
- `controls` lists each node with a role in: button, link, textbox, searchbox, combobox,
  checkbox, radio, switch, tab, menuitem, slider. A repeated control shows one time for each
  copy. A control with no name has `"name": ""`.

## Compare rules (check 2), for one entry (module, screen, state)

1. Matchers: the controls of this screen with this state, the controls of this screen with
   state `default`, and the controls of each layout screen.
2. A scanned control with an empty name is `UNLABELED`.
3. A scanned control that no matcher matches is `ORPHAN` (same role and same name).
4. A tree control of this screen with this state that matches no scanned control is `MISSING`.
5. A layout control is `MISSING` only when it matches no control in any reached `default` entry.
6. If `reached` is false, or the entry does not exist, each tree control of that screen and
   state is `NOT_REACHED` (yellow, never counts as passed).

## Test tags (check 3)

- A test names its leaf with `@leaf:<id>`, for example in Playwright:
  `test("儲存排程", { tag: "@leaf:agents.main.schedule.happy" }, async ({ page }) => { ... })`.
- Only files under `config.e2e_dirs` count. The last result of each test in the Playwright JSON
  report counts.
- Leaf status: `failed` (a tagged test failed, timed out, or was interrupted), else `passed`,
  else `not-run` (tag in files, no result; yellow), else `no-test` (red); `na` for a case with
  `status: "na"`. A tag whose ID is not a leaf is red `STALE`.
