# Deterministic evals

Code: `evals/deterministic/`

Binary checks. No judge model. Offline tests always run. `test_dataset_case` is skipped without `ANTHROPIC_API_KEY`.

## `test_tool_trigger.py`

Offline, scripted client. The first model reply is usually the retrieval-gate JSON (`retrieve: false`), then the turn.

| Test | Asserts |
| --- | --- |
| `test_create_event_writes_db_and_ics` | One `create_event`, row in `calendar_events`, `SUMMARY:` in `calendar.ics` |
| `test_create_event_is_idempotent` | Same title+start twice in one turn → one row; second output contains `already exists`; one ICS summary |
| `test_history_records_tool_use` | Last assistant history line contains `[tools used: create_event` |
| `test_no_tool_turn_ends_loop_in_one_iteration` | Reply text, `iterations == 1`, no tools |
| `test_iteration_guardrail_stops_runaway_loop` | `max_iterations=3` stops a `save_note` loop; reply mentions `iteration limit` |

Live: each line of `evals/dataset.jsonl` is `{id, input, expect_tool, expect_in_args?, setup_fact?}`. `expect_tool: null` means no tools. Otherwise that tool name must appear, and each `expect_in_args` needle must be in the matching argument (case-insensitive). `setup_fact` is inserted before the turn.

## `test_wake_word.py`

`matches_wake` from `paperclip.gateway.voice`. Normalization keeps latin letters, digits, and spaces. Punctuation is dropped. A phrase with no spaces still matches the spaced form. One-character slips can pass the 0.7 similarity window (`paperclib paperclip`).

Kana and other non-latin text normalize to empty and do **not** wake, even if listed after a comma in the wake string.

## `test_speakable.py`

`_speakable` strips emoji (including flags) and markdown `*_`#`` before TTS. An all-emoji string becomes `""`.

## `test_apple_calendar.py`

`_applescript_date` sets day to 1 before month and year, then the real day, hour, and minute.

`sync_to_apple_calendar` on a non-macOS machine returns a string containing `not macOS`. Empty `create_event()` returns a message that includes `needs at least a title` and does not raise `TypeError`.

## `test_working_memory.py`

`Session.build_system` includes `Right now it is` and a `HH:MM` clock. A new `Session` uses `session_id` `"default"`. `start_new` sets the id and clears `history`. These two tests call `load_settings()` (the developer home), not `make_paperclip`.
