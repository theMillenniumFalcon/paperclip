"""Strip host secrets from delegate subprocess env. See docs/tools/env.md."""

from __future__ import annotations

import os

_DELEGATE_ENV_DENY_VAR = "PAPERCLIP_DELEGATE_ENV_DENY"


def delegate_env_denylist() -> frozenset:
    raw = os.getenv(_DELEGATE_ENV_DENY_VAR, "")
    return frozenset(name.strip() for name in raw.split(",") if name.strip())


def delegate_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in delegate_env_denylist():
        env.pop(key, None)
    return env
