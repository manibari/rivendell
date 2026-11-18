# Case kinds

Each control gets all seven kinds. Write each one as a case, or as `"status": "na"` with a
`na_reason` that a person can check. A kind that is not written is red `KIND_MISSING`. This
rule stops silent gaps: a gap must be a written decision, not a thing that nobody saw.

| Kind | Question | How the test proves it |
|---|---|---|
| `happy` | Does the normal action give the correct result on the screen and in the store? | Do the action. Assert the screen text and the stored record (file, row) in the fixture store. |
| `empty` | What does the screen show when there is no data? | Reset the fixture to the empty seed for this screen. Assert the empty-state text, and that no control is broken. |
| `invalid-input` | Does the app reject bad input with a clear message? | Type a value the API must refuse. Assert the Chinese message, and that the store did not change. |
| `no-permission` | Does the app stop a user without the right role? | Sign in as a user without the role. Assert that the control is hidden or refused, and that the API refuses a direct call. |
| `dependency-down` | What does the screen show when the API or a service fails? | Abort the request at the network layer (`page.route(url, r => r.abort())`). Assert an error message and that the page stays usable. |
| `repeat` | Is a double click or a second submit safe? | Click two times fast, or submit the same form again. Assert one stored record, or a clear refusal. |
| `side-effect` | Does the action call the correct outside system with the correct values? | With `boundary: recorder`, assert the recorder log line (command, arguments). Never run the real outside system. |

## When `na` is honest

| Kind | Honest reason (examples) | Not a reason |
|---|---|---|
| `empty` | The control is static (a nav link). | "There is always data." |
| `invalid-input` | The control takes no input (a plain button). | "Users do not type bad values." |
| `no-permission` | The system has no login: one local user. | "Only admins use this page." (Then test the refusal.) |
| `dependency-down` | The control does not call the API (a client-only toggle). | "The API is stable." |
| `repeat` | The action only reads (a tab, a filter). | "Nobody clicks two times." |
| `side-effect` | The action stays in the app and its store. | "The outside call is simple." |
| `happy` | Never `na`. If a control has no normal action, it has no purpose: `does: "unknown"`. | - |

## Notes

- One control can need more than one case of a kind. Give each one its own `id`
  (`invalid-input` for an empty value, `invalid-too-long` for a long one; both are kind
  `invalid-input`).
- A navigation link usually has `happy` (the target opens) and six `na` rows. That is fine:
  the reasons are short and true.
- A `failed` leaf is a bug report. Do not change the case to `na` to hide it.
