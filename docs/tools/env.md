# Delegate environment

Code: `paperclip/tools/_env.py`

Shared helper for **subprocess** env when Paperclip delegates work (`workspace.autorun`; also meant for `delegate_task` / pi). The child would otherwise inherit the parent’s full `os.environ`, including secrets it should not see.

## `PAPERCLIP_DELEGATE_ENV_DENY`

Comma-separated names to strip from the copy. Read **on each call**, not at import, so a host can set the policy after importing Paperclip.

Names match `os.environ` keys **exactly** (case-sensitive). On Windows the OS is case-insensitive, but `dict.pop` on the copy is not — the deny list must use the same casing as the host used when setting the variable.

`PAPERCLIP_DELEGATE_ENV_DENY` itself is **not** stripped, so a nested Paperclip in the child keeps the same policy.

## API

| Function | Returns |
| --- | --- |
| `delegate_env_denylist()` | `frozenset` of names |
| `delegate_env()` | `os.environ.copy()` with those keys removed |
