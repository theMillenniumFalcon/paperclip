# CLI gateway

Code: `paperclip/gateway/cli.py`

Interactive terminal chat: read a line, call `Paperclip.respond`, print the reply. Uses **Rich** (`Console`, `Panel`) for the banner and styled I/O.

## `main()`

1. Construct `Paperclip()` (default settings from `load_settings()`).
2. Set `paperclip.session.session_id = "terminal"`.
3. Print a cyan `Panel.fit` banner: product name, resolved `settings.home`, `settings.model`, and exit hint (Ctrl-D or `/quit`).
4. Loop until EOF, Ctrl+C, or `/quit` / `/exit`:
   - Skip empty lines.
   - Otherwise `paperclip.respond(user_message, observer=_observer, source="cli")`.
   - Print reply as `paperclip ›` (bold green) with a trailing blank line. The reply is escaped so Rich does not treat brackets in model text as style tags — `coming soon` stays visible.
5. On exit, print dim farewell (memory remains in `state.db`).

## `_observer(kind, event)`

Shared by [telegram](telegram.md) and [voice](voice.md). Dim stderr-style traces while the loop runs:

| `kind` | `event` fields used | Printed as |
| --- | --- | --- |
| `tool` | `tool`, `args`, `output` (first 80 chars) | `tool · name(args) → output…` |
| `gate` | `decision`, optional `reason` | `gate · decision — reason` |
| `consolidation` | `new_facts` | `memory · consolidated N fact(s)…` |

Tool names, arguments, output, the gate decision, and the gate reason are escaped the same way, so a stub description or a reason that contains brackets is printed literally.

Unknown kinds are ignored.

## Dependencies

- `paperclip.app.Paperclip`
- `rich`

## Run

```bash
python -m paperclip.gateway.cli
```
