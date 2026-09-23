# Search tool

Code: `paperclip/tools/search.py`

`search_web` — public web search. Stdlib `urllib` only. Returns **plain text** (title, snippet, URL) for the model; it does not hand over HTML.

Typical loop: `search_web` → reason → other tools (e.g. calendar events for each match).

## Backends

| Condition | Backend |
| --- | --- |
| `TAVILY_API_KEY` or `PAPERCLIP_SEARCH_API_KEY` set | [Tavily](https://tavily.com) POST `/search`, 20s timeout, snippet capped at 400 chars |
| No key | DuckDuckGo HTML (`html.duckduckgo.com`), 20s timeout |

DuckDuckGo: scrape `result__a` / `result__snippet`. Result hrefs are often a DDG redirect; `uddg=` is unquoted to the real URL. User-Agent is a desktop Chrome string so the HTML endpoint is less likely to refuse.

## Failures

- **Tavily exception** → tell the model search failed; answer from knowledge or ask the user. Does not fall back to DDG.
- **DDG exception or empty** → often blocked as automation; tell the user to set a free `TAVILY_API_KEY`.
- **Tavily empty** → “No results found. Try a more specific query.”

`make_tool()` takes no args. Schema: `query` (required), `max_results` (default 5).
