# Delegate workspace

Code: `paperclip/tools/workspace.py`

Dated folders for **delegated coding** (pi / `delegate_task` writes real files). Artifacts are deliverables, not agent state — they live **outside** `.paperclip` (git-ignored by design).

```
<PAPERCLIP_WORKSPACE>/<YYYY-MM-DD>/<HHMMSS>-<model-slug>-<task-slug>/
    <files the delegate wrote>
    MANIFEST.md
    run.log
    pi-transcript.log
```

Default root: `./paperclip_workspace` (`PAPERCLIP_WORKSPACE`). Slugs: lowercase alphanumeric words, 2 from the model name, 4 from the task.

## Auto-run

After the delegate finishes, `autorun(folder)` runs one entry `.py` headless (`stdin=DEVNULL`, stdout/stderr captured), with `env=delegate_env()` ([env.md](env.md)).

Disabled if `PAPERCLIP_DELEGATE_AUTORUN` is `0` / `false` / `no`. Timeout: `PAPERCLIP_AUTORUN_TIMEOUT` seconds, read at **import** (default 30).

Entry pick: `main.py` → `app.py` → `run.py` → `game.py` → first `.py` containing `__main__` → the only `.py` if there is exactly one. Ignores `MANIFEST.md`, `run.log`, `pi-transcript.log`, `__pycache__`. Files listed newest first.

Returns `(entry_name, exit_code, output, seconds)`, or `None` if disabled / nothing to run. `exit_code is None` means timeout (treated as still running / interactive). Launch `OSError` → exit `-1`. Always writes `run.log`.

`write_manifest` records date (from the folder path), `provider:model`, task, relative file sizes, and a 2000-char auto-run excerpt.
