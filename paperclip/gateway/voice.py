"""Microphone + TTS gateway. See docs/gateway/voice.md."""

from __future__ import annotations

import os
import re
import subprocess
import sys

from paperclip.app import Paperclip
from paperclip.gateway.cli import _observer

SAMPLE_RATE = 16000
_BLOCK = SAMPLE_RATE // 10
_WAKE_WINDOW_BLOCKS = 25
_WAKE_TAIL_BLOCKS = 5
_DEFAULT_WAKE_WORD = (
    "paperclip paperclip,paperclippaperclip,paperclip,paper clip,paper-clip"
)
_EMOJI = re.compile(
    "[\U0001f300-\U0001faff"
    "\U00002600-\U000027bf"
    "\U0001f1e6-\U0001f1ff"
    "\U00002190-\U000021ff"
    "\U00002b00-\U00002bff"
    "\U0000fe00-\U0000fe0f"
    "\U0000200d\U000020e3\U0000fe0f]+"
)


def record_until_enter():
    import numpy as np
    import sounddevice as sd

    frames: list[np.ndarray] = []

    def collect(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", callback=collect):
        input("recording — press Enter when done… ")
    if not frames:
        return np.zeros(0, dtype="float32")
    return np.concatenate(frames)[:, 0]


def whisper_device() -> str:
    return os.getenv("PAPERCLIP_WHISPER_DEVICE", "cpu").strip().lower() or "cpu"


class Ears:
    def __init__(self, model_size: str | None = None):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(
            model_size or os.getenv("PAPERCLIP_WHISPER_MODEL", "base"),
            device=whisper_device(),
            compute_type="int8",
        )

    def transcribe(self, audio, language: str | None = None) -> str:
        segments, _ = self.model.transcribe(
            audio, language=language or os.getenv("PAPERCLIP_WHISPER_LANG")
        )
        return " ".join(seg.text.strip() for seg in segments).strip()


def _best_say_voice() -> str:
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=5).stdout
    except Exception:  # noqa: BLE001
        return "Daniel"
    english = []
    for ln in out.splitlines():
        m = re.match(r"^(.+?)\s{2,}([a-z]{2})_", ln)
        if m and m.group(2) == "en":
            english.append(m.group(1).strip())
    for tag in ("(Premium)", "(Enhanced)"):
        hit = next((n for n in english if tag in n), None)
        if hit:
            return hit
    for pref in ("Serena", "Kate", "Daniel", "Samantha"):
        if pref in english:
            return pref
    return english[0] if english else "Daniel"


def _speakable(text: str) -> str:
    if not text:
        return ""
    text = _EMOJI.sub("", text)
    text = re.sub(r"[*_`#>]", "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return "\n".join(ln.strip() for ln in text.splitlines()).strip()


class Mouth:
    def __init__(self):
        self.engine = os.getenv("PAPERCLIP_TTS", "").strip().lower()
        self.voice = os.getenv("PAPERCLIP_VOICE", "")
        if not self.engine:
            try:
                import kokoro  # noqa: F401

                self.engine = "kokoro"
            except ImportError:
                self.engine = "say"
        if self.engine == "kokoro":
            from kokoro import KPipeline

            self.pipeline = KPipeline(lang_code="b")
            self.voice = self.voice or "bm_george"
        elif self.engine == "say" and not self.voice:
            self.voice = _best_say_voice()

    def speak(self, text: str) -> None:
        text = _speakable(text)
        if not text:
            return
        if self.engine == "kokoro":
            import sounddevice as sd

            for _, _, audio in self.pipeline(text, voice=self.voice):
                sd.play(audio, 24000)
                sd.wait()
        elif sys.platform == "darwin":
            subprocess.run(["say", "-v", self.voice or "Daniel", text], check=False)
        else:
            print("(no TTS engine on this platform — set PAPERCLIP_TTS=kokoro)")


def matches_wake(text: str, wake_word: str) -> bool:
    import difflib

    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

    heard = norm(text)
    if not heard:
        return False

    for variant in (v for v in (norm(v) for v in wake_word.split(",")) if v):
        if variant in heard or variant.replace(" ", "") in heard.replace(" ", ""):
            return True
        words, n = heard.split(), len(variant.split())
        if any(
            difflib.SequenceMatcher(None, " ".join(words[i : i + n]), variant).ratio() >= 0.7
            for i in range(max(0, len(words) - n + 1))
        ):
            return True
    return False


def _mic_threshold() -> float:
    return float(os.getenv("PAPERCLIP_MIC_THRESHOLD", "0.005"))


def record_command(stream, max_seconds: float = 15.0, silence_after: float = 1.2):
    import numpy as np

    frames, quiet, spoke = [], 0, False
    for _ in range(int(max_seconds * 10)):
        data, _ = stream.read(_BLOCK)
        frames.append(data.copy())
        loud = float(np.sqrt((data**2).mean())) > _mic_threshold() * 2
        spoke = spoke or loud
        quiet = 0 if loud else quiet + 1
        if spoke and quiet >= int(silence_after * 10):
            break
    return np.concatenate(frames)[:, 0]


def wait_for_speech(stream, timeout: float) -> bool:
    import numpy as np

    for _ in range(int(timeout * 10)):
        data, _ = stream.read(_BLOCK)
        if float(np.sqrt((data**2).mean())) > _mic_threshold() * 2:
            return True
    return False


def wake_loop(paperclip: Paperclip, mouth: Mouth, wake_word: str) -> None:
    import numpy as np
    import sounddevice as sd

    scout = Ears(model_size="tiny")
    ears = Ears()
    ack = os.getenv("PAPERCLIP_WAKE_ACK", "Yes?")
    followup = float(os.getenv("PAPERCLIP_FOLLOWUP_SECONDS", "8"))
    wake_lang = os.getenv("PAPERCLIP_WAKE_LANG") or ("en" if wake_word.isascii() else None)
    print(f'Listening for "{wake_word}" — Ctrl-C to quit.')

    def status(msg: str) -> None:
        sys.stdout.write(f"\r\x1b[2m{msg[:72]:<72}\x1b[0m")
        sys.stdout.flush()

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=_BLOCK) as stream:

        def drain() -> None:
            while stream.read_available >= _BLOCK:
                stream.read(_BLOCK)

        window: list = []
        while True:
            data, _ = stream.read(_BLOCK)
            window.append(data.copy())
            if len(window) < _WAKE_WINDOW_BLOCKS:
                continue
            chunk = np.concatenate(window)[:, 0]
            window = window[-_WAKE_TAIL_BLOCKS:]

            if float(np.sqrt((chunk**2).mean())) < _mic_threshold():
                status("· listening…")
                continue
            heard_scan = scout.transcribe(chunk, language=wake_lang)
            if not matches_wake(heard_scan, wake_word):
                status(f'· heard: "{heard_scan}"' if heard_scan else "· listening…")
                if heard_scan:
                    paperclip.tracer.event("wake_scan", {"heard": heard_scan, "matched": False})
                continue

            print("\n[wake word]")
            mouth.speak(ack)
            drain()

            while True:
                heard = ears.transcribe(record_command(stream))
                if heard:
                    print(f"you › {heard}")
                    result = paperclip.respond(heard, observer=_observer, source="voice")
                    print(f"paperclip › {result.reply}")
                    mouth.speak(result.reply)
                else:
                    print("(didn't catch that)")
                drain()
                status(f"· still here — just talk, or I'll rest in {followup:.0f}s")
                if not wait_for_speech(stream, followup):
                    break
            window = []


def main() -> None:
    try:
        import sounddevice  # noqa: F401
    except ImportError:
        raise SystemExit("Voice extra not installed: pip install -e '.[voice]'")

    paperclip = Paperclip()
    paperclip.session.session_id = "voice"
    mouth = Mouth()
    wake_word = os.getenv("PAPERCLIP_WAKE_WORD", _DEFAULT_WAKE_WORD).strip()
    if wake_word:
        try:
            wake_loop(paperclip, mouth, wake_word)
        except KeyboardInterrupt:
            pass
        print("\nbye — your memory stays in state.db")
        return

    ears = Ears()
    print("Voice Paperclip ready. Press Enter to talk, Ctrl-C to quit.")
    while True:
        try:
            input("\npress Enter to talk… ")
            audio = record_until_enter()
        except (EOFError, KeyboardInterrupt):
            break
        if audio.size < SAMPLE_RATE // 4:
            print("(too short, try again)")
            continue

        heard = ears.transcribe(audio)
        if not heard:
            print("(didn't catch that)")
            continue
        print(f"you › {heard}")

        result = paperclip.respond(heard, observer=_observer, source="voice")
        print(f"paperclip › {result.reply}")
        mouth.speak(result.reply)

    print("bye — your memory stays in state.db")


if __name__ == "__main__":
    main()
