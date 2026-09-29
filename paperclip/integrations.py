"""Integration status types (no I/O). See docs/integrations.md."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IntegrationState(StrEnum):
    NOT_CONFIGURED = "not_configured"
    INSTALLED_BUT_UNCONFIGURED = "installed_but_unconfigured"
    CONFIGURED = "configured"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass(frozen=True)
class IntegrationStatus:
    state: IntegrationState
    message: str = ""
    checked_at: str | None = None
