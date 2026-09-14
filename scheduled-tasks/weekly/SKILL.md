---
name: newsletter-weekly-digest
description: Weekly newsletter digest — fetches last 7 days, analyzes themes, emails every Sunday at 5 PM
---

# Before using this file
# Replace YOUR_PROJECT_PATH with the absolute path to your cloned repo.
# Place this file at: ~/.claude/scheduled-tasks/newsletter-weekly-digest/SKILL.md
# Set cron to: 0 17 * * 0  (Sundays at 5 PM local time)
# Pair with the daily task (scheduled-tasks/daily/SKILL.md) set to Mon–Sat only

You are a scheduled agent delivering a weekly newsletter digest. Complete every step in order without pausing for confirmation. If any step fails, jump to the Error handling section — do NOT stop silently.

---

## STEP 0 — Check if already sent this week

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import os, datetime
week_id = datetime.date.today().strftime("%Y-W%V")
sentinel = 'YOUR_PROJECT_PATH/output/sent_weekly.txt'
if os.path.exists(sentinel):
    with open(sentinel) as f:
        last_sent = f.read().strip()
    if last_sent == week_id:
        print(f"ALREADY_SENT_THIS_WEEK={week_id}")
    else:
        print(f"NOT_YET_SENT (last={last_sent})")
else:
    print("NOT_YET_SENT (no sentinel)")
PYEOF
```

**If the output contains `ALREADY_SENT_THIS_WEEK`, stop immediately. Do not proceed further — the digest already went out this week.**

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

newsletters = digest.fetch(since_hours=168, max_msgs=200)
print(f"FETCHED: {len(newsletters)} newsletters\n")

print("=== FULL INDEX (all newsletters) ===")
for i, n in enumerate(newsletters, 1):
    print(f"[{i:3d}] {n['received_at'][:10]} | {n['source'][:30]:30s} | {n['subject'][:80]}")

print(f"\n=== CONTENT EXCERPTS (first 35 of {len(newsletters)}) ===")
for i, n in enumerate(newsletters[:35], 1):
    print(f"\n{'='*60}")
    print(f"[{i}] {n['source']}  |  {n['sender_email']}")
    print(f"SUBJECT: {n['subject']}")
    print(f"DATE: {n['received_at'][:10]}")
    print(f"CONTENT:\n{n['content'][:400]}")

meta = [{"source": n["source"], "sender_email": n["sender_email"],
         "subject": n["subject"], "received_at": n["received_at"]}
        for n in newsletters]
with open('YOUR_PROJECT_PATH/output/newsletters_weekly.json', 'w') as f:
    json.dump(meta, f, indent=2)
print(f"\n{'='*60}")
print(f"Metadata saved. {len(newsletters)} newsletters ready for analysis.")
PYEOF
```

If 0 newsletters were fetched, jump to the **Fallback** section.

---

## STEP 3 — Layer 3 tiebreaker

Look at the newsletter content printed above. Silently discard anything that is clearly a receipt, account alert, password reset, or pure promotion. Keep all genuine editorial newsletters.

---

## STEP 4 — Write analysis_weekly.json

First remove the old analysis file:

```bash
rm -f YOUR_PROJECT_PATH/output/analysis_weekly.json
```

Now use the **Write tool** to create `YOUR_PROJECT_PATH/output/analysis_weekly.json` with your analysis as valid JSON matching this exact schema:

```json
{
  "week_in_review": "<3-5 sentences. The week's dominant narrative — not a list of events. What is the through-line? End with 1-2 specific things to watch next week.>",
  "themes": [
    {
      "title": "<5-8 word theme name — specific, not generic>",
      "covered_by": ["<newsletter brand 1>", "<brand 2>", "<brand 3>"],
      "bullets": [
        "<specific event or data point that defined this theme this week — concrete, with numbers or names>",
        "<another concrete development from this week>",
        "<the surprise, the connection across newsletters, or the contrarian read>"
      ],
      "analysis": "<3-5 sentences. What does this theme mean? Second-order effects? What changed this week vs before? What to watch?>"
    }
  ],
  "stats": {"themes_count": 5, "key_points_count": 0}
}
```

You are writing the "Weekly Intelligence" briefing. The reader has already seen daily digests all week — this is NOT a recap, it is a step back. Identify the 5 dominant themes of the week, connect events across days and newsletters, and explain what the week MEANT. Match the register of Ben Thompson, Matt Levine, Jamin Ball.

Rules:
- Exactly 5 themes — no more, no fewer
- Cross-cutting only: each theme must appear in 2+ newsletters across multiple days
- covered_by = real brand names from the data only
- Bullets must aggregate the whole week, not just one day
- analysis takes a position — no hedging language
- key_points_count = total bullets across all 5 themes
- No invented facts, no hallucinated figures

---

## STEP 5 — Send the digest

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import sys, json, os
os.chdir('YOUR_PROJECT_PATH')
sys.path.insert(0, '.')
import digest

with open('YOUR_PROJECT_PATH/output/analysis_weekly.json') as f:
    analysis = json.load(f)

result = digest.send_digest('weekly', analysis)
print(f"SUCCESS — sent message ID: {result.get('id')}")
PYEOF
```

After a successful send, mark this week as done:

```bash
python3 -c "import datetime; open('YOUR_PROJECT_PATH/output/sent_weekly.txt','w').write(datetime.date.today().strftime('%Y-W%V'))"
```

Done. The weekly digest is in your inbox.

---

## Fallback (0 newsletters fetched)

```bash
YOUR_PROJECT_PATH/.venv/bin/python3 - <<'PYEOF'
import sys, os
os.chdir('YOUR_PROJECT_PATH')
sys.path.insert(0, '.')
import digest
result = digest.send_digest('weekly', {
    "week_in_review": "No newsletters arrived in the last 7 days.",
    "themes": [],
    "stats": {"themes_count": 0, "key_points_count": 0}
})
print(f"Sent empty digest — ID: {result.get('id')}")
PYEOF
```

Then mark this week as done:

```bash
python3 -c "import datetime; open('YOUR_PROJECT_PATH/output/sent_weekly.txt','w').write(datetime.date.today().strftime('%Y-W%V'))"
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
