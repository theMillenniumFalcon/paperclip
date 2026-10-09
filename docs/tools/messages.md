# Messages

Code: `paperclip/tools/messages.py`

## `send_message`

`make_tool(home)`. Writes `{home}/outbox/{UTC-stamp}-{safe-recipient}.txt` with `To:` and body.

Does **not** send email, Telegram, or Slack. Return text says the file name and that nothing was sent.

Recipient filename: non-alphanumeric → `-`, max 40 chars.
