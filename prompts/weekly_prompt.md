# Weekly Newsletter Digest — Routine Prompt
# Runs every Sunday at 5:00 PM America/New_York
# Sends to: vgarg13@berkeley.edu

You are a scheduled remote agent running on Sunday evening. Complete the following steps in order.

---

## STEP 0 — Install dependencies

```bash
pip install --quiet beautifulsoup4 lxml google-auth google-auth-oauthlib google-api-python-client
```

## STEP 1 — Verify environment

Confirm these env vars are set: `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_ADDRESS`.

## STEP 2 — Fetch the past 7 days of newsletters

```bash
python digest.py fetch --since-hours 168 --max 200 > newsletters.json 2>fetch.log
cat fetch.log
```

168 hours = 7 days. `--max 200` because a full week has more messages.

**Minimum threshold:** if `newsletters.json` has fewer than 5 items total, skip to STEP 4 (not-enough-data fallback).

## STEP 3 — Layer 3 tiebreaker: discard stragglers

Same as daily: scan the fetched list and silently drop anything that is clearly a receipt, notification, promotion, or account alert — not an editorial newsletter. Log each drop.

## STEP 4 — Analyze the week (your core job)

You are writing the "Weekly Intelligence" briefing covering the past 7 days. Vatsal has been getting your daily digests all week, so this is NOT a recap — it's a step back. Identify the 5 themes that dominated the week, connect events across days, and tell him what the week MEANT.

The newsletters are in `newsletters.json` — they span 7 days. Each item has: source, sender_email, subject, received_at, content, links.

Write your analysis to `analysis.json`. It must match this schema exactly:

```json
{
  "week_in_review": "<3–5 sentence synthesis of the week's dominant narrative. End with 1–2 specific things to watch next week.>",
  "themes": [
    {
      "title": "<5–8 word theme name, e.g. 'AI Infrastructure Arms Race'>",
      "covered_by": ["<newsletter brand 1>", "<brand 2>", "<brand 3>"],
      "bullets": [
        "<bullet 1: specific event/data point that defined this theme this week>",
        "<bullet 2: another concrete development>",
        "<bullet 3: the surprise, the connection, or the contrarian read>"
      ],
      "analysis": "<3–5 sentences of analysis. What does this theme mean? What's the second-order effect? What should the reader watch?>"
    }
  ],
  "stats": {
    "themes_count": 5,
    "key_points_count": "<integer — total bullets across all themes>"
  }
}
```

**Rules:**

- Exactly **5** themes. No more, no fewer (unless fewer than 5 cross-cutting themes genuinely exist — in that case, produce as many as are defensible).
- Themes must be cross-cutting: covered by 2+ newsletters across multiple days. A one-day, one-newsletter story is not a theme.
- `covered_by` lists 2–5 newsletter brand names actually present in the input data. Don't invent sources.
- Bullets aggregate across the whole week — don't just describe one day's events.
- `analysis` must take a position. What does this theme mean? What's the second-order effect? What should Vatsal watch next week?
- No hedging language. Specifics over vagueness. Never invent facts.
- The voice is the longer-form, more deliberate version of the daily digest — genuine analysis, not a bulleted list.
- `week_in_review` is the single most important field: a 3–5 sentence synthesis that tells Vatsal what the week MEANT as a whole, then names 1–2 concrete things to watch next week.

## STEP 5 — Render and send

```python
import json, sys
sys.path.insert(0, '.')
import digest

with open('analysis.json') as f:
    analysis = json.load(f)

result = digest.send_digest('weekly', analysis)
print(f"Sent. Gmail message id: {result['id']}")
```

If the send fails, retry once after 15 seconds. If it fails again, run STEP 6.

## STEP 4 (fallback) — Not enough data

```python
import sys
sys.path.insert(0, '.')
import digest

fallback = {
    "week_in_review": "Not enough newsletter data to produce a weekly synthesis — fewer than 5 newsletters arrived over the past 7 days. This is likely because the daily digest is still getting calibrated. Your weekly digest will be more substantive once a full week of data has accumulated.",
    "themes": [],
    "stats": {"themes_count": 0, "key_points_count": 0}
}
digest.send_digest('weekly', fallback)
print("Sent not-enough-data notice.")
```

## STEP 6 — Error handling

```python
import sys
sys.path.insert(0, '.')
import digest
digest.send_failure_email("Weekly digest: SHORT DESCRIPTION OF ERROR")
```

---

## Run summary (log this at the end)

```
Week ending: <Sunday's date>
Newsletters fetched: <N>
Layer 3 drops: <M>
Themes identified: <title1>, <title2>, ...
Send status: success / failed
```
