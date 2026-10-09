# Web search

Code: `paperclip/tools/search.py`

## `search_web`

`make_tool()`. Args: `query` (required), `max_results` (default 5).

| Key | Backend |
| --- | --- |
| `TAVILY_API_KEY` or `PAPERCLIP_SEARCH_API_KEY` | POST `https://api.tavily.com/search`, snippets capped at 400 chars, 20s timeout |
| neither | DuckDuckGo HTML (`html.duckduckgo.com`), unwrap `uddg=` redirects |

Tavily failure → error string asking the model to answer from knowledge. DuckDuckGo empty or blocked → hint to set `TAVILY_API_KEY`. Tavily empty → “try a more specific query.”

Output is numbered title, snippet, and URL lines. Stdlib only (`urllib`).
