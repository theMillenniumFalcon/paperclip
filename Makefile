# paperclip-agent — one command per pillar.
PY := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python)

.PHONY: run voice telegram brief api trace eval eval-judge gate lint

run:            ## chat with Paperclip in the terminal
	$(PY) -m paperclip

voice:          ## talk to it — push-to-talk, or always-on with PAPERCLIP_WAKE_WORD
	$(PY) -m paperclip voice

telegram:       ## phone → laptop (needs TELEGRAM_BOT_TOKEN in .env)
	$(PY) -m paperclip telegram

brief:          ## morning briefing from calendar + mail + memory
	$(PY) -m paperclip brief

api:            ## local JSON API — http://localhost:7777
	$(PY) -m paperclip api

trace:          ## deep trace waterfalls (Phoenix) at http://localhost:6006
	$(PY) -m phoenix.server.main serve

eval:           ## deterministic evals (0/1, no judge involved)
	$(PY) -m pytest -q evals/deterministic

eval-judge:     ## LLM-as-judge evals (scored %, needs an API key)
	$(PY) -m pytest -q evals/judge

gate:           ## the release gate: deterministic must pass, judge must clear threshold
	$(PY) -m paperclip.ops.release_gate

lint:
	$(PY) -m ruff check paperclip evals
