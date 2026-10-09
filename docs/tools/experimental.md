# Experimental tools

Code: `paperclip/tools/experimental.py`

Registered only when `PAPERCLIP_EXPERIMENTAL` is `1`, `true`, or `yes`. Each tool returns a “coming soon” string and does not perform the action. Descriptions are prefixed `[coming soon]`.

| Name | Intended later |
| --- | --- |
| `delegate_task` | Sub-agent for a self-contained task |
| `run_command` | Sandboxed shell |
| `browse_web` | Open and interact with a page (`search_web` already does read-only lookup) |
| `schedule_task` | In-app recurring runs |

Schemas accept no properties.
