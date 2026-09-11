---
name: newsletter-daily-digest
description: Daily newsletter digest — fetches last 24h, analyzes, emails digest once per day
---

# Before using this file
# Replace YOUR_PROJECT_PATH with the absolute path to your cloned repo.
# Replace YOUR_EMAIL with the Gmail address you want to send/receive the digest.
# Place this file at: ~/.claude/scheduled-tasks/newsletter-daily-digest/SKILL.md
# Set cron to: 0 8,10,12,14,16 * * *  (fires 5x daily; sentinel prevents double-sends)

You are a scheduled agent delivering a daily newsletter digest. Complete every step in order without pausing for confirmation. If any step fails, jump to the Error handling section — do NOT stop silently.

---

## STEP 0 — Check if already sent today

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import os, datetime
today = datetime.date.today().isoformat()
sentinel = 'YOUR_PROJECT_PATH/output/sent_daily.txt'
if os.path.exists(sentinel):
    with open(sentinel) as f:
        last_sent = f.read().strip()
    if last_sent == today:
        print(f"ALREADY_SENT_TODAY={today}")
    else:
        print(f"NOT_YET_SENT (last={last_sent})")
else:
    print("NOT_YET_SENT (no sentinel)")
PYEOF
```

**If the output contains `ALREADY_SENT_TODAY`, stop immediately. Do not proceed further — the digest already went out today.**

---

## STEP 1 — Install dependencies

```bash
YOUR_PROJECT_PATH/.venv/bin/pip install --quiet beautifulsoup4 lxml google-auth google-auth-oauthlib google-api-python-client 2>&1 | tail -3
```

---

## STEP 2 — Fetch and print newsletters

Run the command below. The output is your source material — read every line carefully.

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import sys, json, os
os.chdir('YOUR_PROJECT_PATH')
sys.path.insert(0, '.')
import digest

newsletters = digest.fetch(since_hours=24, max_msgs=75)
print(f"FETCHED: {len(newsletters)} newsletters\n")

for i, n in enumerate(newsletters, 1):
    print(f"{'='*60}")
    print(f"[{i}] {n['source']}  |  {n['sender_email']}")
    print(f"SUBJECT: {n['subject']}")
    print(f"CONTENT:\n{n['content'][:1800]}")
    print()

meta = [{"source": n["source"], "sender_email": n["sender_email"],
         "subject": n["subject"], "received_at": n["received_at"]}
        for n in newsletters]
with open('YOUR_PROJECT_PATH/output/newsletters_daily.json', 'w') as f:
    json.dump(meta, f, indent=2)
print(f"{'='*60}")
print(f"Metadata saved. {len(newsletters)} newsletters ready for analysis.")
PYEOF
```

If 0 newsletters were fetched, jump to the **Fallback** section.

---

## STEP 3 — Layer 3 tiebreaker

Look at the newsletter content printed above. Silently discard anything that is clearly a receipt, account alert, password reset, or pure promotion that slipped through. Keep all genuine editorial newsletters.

---

## STEP 4 — Write analysis_daily.json

First remove the old analysis file:

```bash
rm -f YOUR_PROJECT_PATH/output/analysis_daily.json
```

Now use the **Write tool** to create `YOUR_PROJECT_PATH/output/analysis_daily.json` with your analysis as valid JSON matching this exact schema:

```json
{
  "big_picture": "<2-3 tight sentences. A thesis about today, not a recap. Name specific sources. Have an opinion.>",
  "top_stories": [
    {
      "source": "<newsletter brand name>",
      "sender_email": "<from address>",
      "headline": "<6-10 specific words>",
      "bullets": [
        "<specific fact with number or name — max 25 words>",
        "<another concrete data point — max 25 words>",
        "<a third — max 25 words>"
      ],
      "analysis": "<2-3 sentences MAX. Implication or contrarian angle. NOT a restatement of the bullets.>",
      "links": []
    }
  ],
  "also_today": [
    {
      "source": "<brand name>",
      "sender_email": "<from address>",
      "summary": "<one sentence, max 20 words, the single most useful fact>"
    }
  ],
  "stats": {"newsletters_count": 0, "key_points_count": 0}
}
```

You are a senior analyst writing "Daily Intelligence" for a sharp, time-poor reader who follows business, tech, finance, and policy. Match the register of Ben Thompson, Matt Levine, Jamin Ball: specific, opinionated, no filler.

Rules:
- 5 top_stories max; cross-coverage (same story in 2+ newsletters) = priority signal
- also_today = up to 8 best remaining newsletters, each ≤20 words
- Each bullet ≤25 words, no hedging language
- analysis is 2-3 sentences MAX
- No invented facts, no hallucinated figures
- newsletters_count = total analyzed; key_points_count = total bullets across top_stories

---

## STEP 5 — Send the digest

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import sys, json, os
os.chdir('YOUR_PROJECT_PATH')
sys.path.insert(0, '.')
import digest

with open('YOUR_PROJECT_PATH/output/analysis_daily.json') as f:
    analysis = json.load(f)

result = digest.send_digest('daily', analysis)
print(f"SUCCESS — sent message ID: {result.get('id')}")
PYEOF
```

After a successful send, mark today as done:

```bash
date +%Y-%m-%d > YOUR_PROJECT_PATH/output/sent_daily.txt
```

Done. The digest is in your inbox.

---

## Fallback (0 newsletters fetched)

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import sys, os
os.chdir('YOUR_PROJECT_PATH')
sys.path.insert(0, '.')
import digest
result = digest.send_digest('daily', {
    "big_picture": "No newsletters arrived in the last 24 hours.",
    "top_stories": [],
    "also_today": [],
    "stats": {"newsletters_count": 0, "key_points_count": 0}
})
print(f"Sent empty digest — ID: {result.get('id')}")
PYEOF
```

Then mark today as done:

```bash
date +%Y-%m-%d > YOUR_PROJECT_PATH/output/sent_daily.txt
```

## Error handling (unrecoverable exception in any step)

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import sys, os
os.chdir('YOUR_PROJECT_PATH')
sys.path.insert(0, '.')
import digest
digest.send_failure("REPLACE_THIS_WITH_A_BRIEF_DESCRIPTION_OF_WHAT_FAILED_AND_THE_ERROR_MESSAGE")
print("Sent failure notification")
PYEOF
```
