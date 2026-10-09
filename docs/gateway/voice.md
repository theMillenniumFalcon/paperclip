# Voice gateway

Code: `paperclip/gateway/voice.py`

Speak to Paperclip; hear replies via TTS. Speech → **faster-whisper** → `Paperclip.respond(..., source="voice")` → **Mouth** (TTS). `session_id="voice"`. Harness: [`cli._observer`](cli.md).

Install: `pip install -e '.[voice]'` (`sounddevice`, `numpy`, `faster-whisper`). Missing extra: exit with install hint.

## Constants

| Name | Value | Meaning |
| --- | --- | --- |
| `SAMPLE_RATE` | 16000 | Mic capture rate (Hz) |
| `_BLOCK` | `SAMPLE_RATE // 10` | 100 ms audio blocks |
| `_WAKE_WINDOW_BLOCKS` | 25 | ~2.5 s of audio before wake scan |
| `_WAKE_TAIL_BLOCKS` | 5 | 0.5 s overlap so phrases can span chunk boundaries |
| `_DEFAULT_WAKE_WORD` | comma-separated phrases | See [Wake word](#wake-word) |

## `main()`

1. `Paperclip()`, `session_id="voice"`, `Mouth()`.
2. Read `PAPERCLIP_WAKE_WORD` (default `_DEFAULT_WAKE_WORD`). If non-empty after strip → `wake_loop` until Ctrl+C, then goodbye message.
3. If wake word env is empty → **push-to-talk** loop: Enter → `record_until_enter()` → transcribe → respond → speak; reject clips shorter than 250 ms.

## Push-to-talk: `record_until_enter()`

Opens `sounddevice.InputStream` with a callback that appends float32 mono frames. User presses Enter to stop. Returns concatenated audio or empty array.

## `Ears`

Wraps `faster_whisper.WhisperModel` (`compute_type="int8"`).

- Model size: constructor arg, or `PAPERCLIP_WHISPER_MODEL` (default `base`).
- `transcribe(audio, language=None)`: optional `PAPERCLIP_WHISPER_LANG`; joins segment text.

Wake loop uses `Ears("tiny")` for scanning and a full `Ears()` for commands.

## `Mouth` (TTS)

| `PAPERCLIP_TTS` | Behavior |
| --- | --- |
| empty, `kokoro` importable | `kokoro`, `KPipeline(lang_code="b")`, voice `PAPERCLIP_VOICE` or `bm_george` |
| empty, no kokoro | macOS `say`; voice from `PAPERCLIP_VOICE` or `_best_say_voice()` |
| `kokoro` | As above |
| `say` | macOS `say` only |

`speak(text)`: runs `_speakable(text)` first, then plays audio. Non-macOS without kokoro: print hint to set `PAPERCLIP_TTS=kokoro`.

### `_best_say_voice()`

Runs `say -v ?`, parses English voices, prefers `(Premium)` / `(Enhanced)`, else Serena / Kate / Daniel / Samantha, else first English or `Daniel`.

### `_speakable(text)`

Strips emoji (`_EMOJI` regex), markdown `*_`#>`, collapses spaces, trims lines—so TTS does not read emoji names aloud.

## Wake word

**Default:** hands-free `wake_loop` with phrases like `paperclip paperclip`, `paper clip`, etc. (`_DEFAULT_WAKE_WORD`).

**Push-to-talk:** set `PAPERCLIP_WAKE_WORD=""`.

### `matches_wake(text, wake_word)`

Pure function for tests and wake detection. `wake_word` is comma-separated variants. Normalize: lowercase, keep `a-z`, `0-9`, spaces. Match if:

- normalized variant is a substring of heard text, or
- variant without spaces appears in heard without spaces, or
- sliding window of `n` words has ≥ 0.7 `SequenceMatcher` ratio to variant.

Handles Whisper garbling (`paperclippaperclip`, `paper clip`, etc.).

### `wake_loop(paperclip, mouth, wake_word)`

Always-listening mode (Whisper-based wake, not openWakeWord):

1. **One** persistent `InputStream` for the whole session (re-opening per chunk can freeze on macOS when routing changes).
2. Accumulate `_WAKE_WINDOW_BLOCKS` → RMS vs `_mic_threshold()`; if quiet, status `· listening…`.
3. Else transcribe chunk with **tiny** model; language `PAPERCLIP_WAKE_LANG` or `en` if wake word is ASCII.
4. If no match: status line may show `heard: "…"`; non-matches logged via `paperclip.tracer.event("wake_scan", {heard, matched: false})`.
5. On match: print `[wake word]`, speak `PAPERCLIP_WAKE_ACK` (default `Yes?`), **drain** mic buffer (avoid hearing the ack).
6. **Conversation sub-loop:** `record_command` → transcribe with full model → respond → speak → drain → status with follow-up countdown → `wait_for_speech` for `PAPERCLIP_FOLLOWUP_SECONDS` (default 8). Break sub-loop on timeout → back to wake scanning.
7. After sub-loop, clear window buffer.

Status line: ANSI dim, 72-char padded `\r` overwrite.

### `record_command(stream, max_seconds=15, silence_after=1.2)`

Read 100 ms blocks from **same** stream until user spoke then went quiet for `silence_after` seconds, or `max_seconds` elapsed. Loud = RMS > `2 * _mic_threshold()`.

### `wait_for_speech(stream, timeout)`

Poll blocks until loud or timeout (follow-up window without repeating wake phrase).

### `_mic_threshold()`

`float(PAPERCLIP_MIC_THRESHOLD)` default `0.005`. Tune if wake is too sensitive or deaf.

## Environment

| Variable | Default | Role |
| --- | --- | --- |
| `PAPERCLIP_WHISPER_MODEL` | `base` | Command transcription model size |
| `PAPERCLIP_WHISPER_LANG` | (auto) | Force language on transcribe |
| `PAPERCLIP_WAKE_WORD` | `_DEFAULT_WAKE_WORD` | Comma-separated; empty → push-to-talk |
| `PAPERCLIP_WAKE_LANG` | `en` if ASCII wake word | Tiny-model scan language |
| `PAPERCLIP_WAKE_ACK` | `Yes?` | Spoken after wake |
| `PAPERCLIP_FOLLOWUP_SECONDS` | `8` | Open-mic after each reply |
| `PAPERCLIP_MIC_THRESHOLD` | `0.005` | RMS silence gate |
| `PAPERCLIP_TTS` | auto | `kokoro` or `say` |
| `PAPERCLIP_VOICE` | auto / `bm_george` | `say` voice name or Kokoro id |

## Run

```bash
python -m paperclip.gateway.voice
```

Ctrl-C quits; chat memory stays in `state.db`.
