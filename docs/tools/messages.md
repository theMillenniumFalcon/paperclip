# Messages tool

Code: `paperclip/tools/messages.py`

`send_message` — **draft only**. Writes a text file under `{home}/outbox/`. Nothing is emailed, posted, or otherwise sent. The user reviews and sends it themselves.

`make_tool(home)` expects `home/outbox` to exist (`Settings.ensure_home()` creates it).

| Argument | Meaning |
| --- | --- |
| `to` | Recipient name or address (shown in the file as `To:`) |
| `body` | Message text |

Filename: `{UTC timestamp}-{safe_to}.txt`. `safe_to` is `to` with non-alphanumeric characters turned into `-`, max 40 chars. Contents:

```
To: {to}

{body}
```

The return string tells the model the file name and that **nothing was sent**.
