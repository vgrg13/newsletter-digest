# newsletter-digest (personal)

Personal newsletter digest for `vgarg13@berkeley.edu`. Reads your inbox via the Gmail API, has Claude do the analysis at zero API cost (the analyst is the routine itself), renders the HTML, and sends the digest back to you.

Runs as a scheduled remote agent on claude.ai — **no Anthropic API tokens, no GitHub Actions, no Mac uptime requirement**.

---

## Files

| File | What it is |
|---|---|
| `digest.py` | Fetch + filter + send. `fetch` mode outputs newsletter JSON; `send` mode renders + emails. |
| `renderer.py` | Pure-Python HTML renderer. Matches `sample_daily.html` / `sample_weekly.html` visually. |
| `get_refresh_token.py` | One-time local script to mint your Gmail OAuth refresh token. |
| `daily_prompt.md` | The instructions the daily routine executes at 7 AM ET. |
| `weekly_prompt.md` | The instructions the Sunday routine executes at 5 PM ET. |
| `requirements.txt` | Python deps (`beautifulsoup4`, `lxml`, google-auth-oauthlib). |
| `secrets.env.example` | Template for your local secrets file. |
| `sample_daily.html` / `sample_weekly.html` | Reference visuals for the renderer. |

---

## Setup — one-time, ~10 minutes

### 1. Get a Gmail refresh token

```bash
cd ~/Desktop/Newsletter_v2
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python get_refresh_token.py
```

The script prints step-by-step Google Cloud Console instructions, opens your browser for OAuth, and gives you three values. Paste them into `secrets.env` (copy from `secrets.env.example` first).

**Berkeley note:** if Google blocks creating an External OAuth app under your `@berkeley.edu` account, run the Google Cloud Console steps from a personal `@gmail.com` account. You'll still authenticate `vgarg13@berkeley.edu` at the consent screen — the OAuth client just identifies the *app*, not the *mailbox*.

### 2. Verify locally

Confirm the pipeline works end-to-end before wiring up the scheduled routine:

```bash
# Load your secrets into the shell
set -a; source secrets.env; set +a

# Pull last 24h of newsletters into a JSON file
python digest.py fetch --since-hours 24 > /tmp/newsletters.json
cat /tmp/newsletters.json | python -m json.tool | head -40

# Manually write a tiny analysis.json by hand (or use the fixture in renderer.py)
python3 renderer.py        # emits preview_daily.html + preview_weekly.html

# Or do a full dry-run send (renders to out.html, doesn't send)
echo '{"big_picture":"test","top_stories":[],"also_today":[],"stats":{"newsletters_count":0,"key_points_count":0}}' > /tmp/a.json
python digest.py send --kind daily --analysis-json /tmp/a.json --dry-run
open out.html
```

Open `out.html` (or `preview_daily.html`) in your browser. Should look like `sample_daily.html`.

### 3. Wire up the routines (BLOCKED — see Status)

When claude.ai's remote-trigger system is back online:

1. Create two routines on claude.ai (one daily 7am ET, one Sunday 5pm ET).
2. Paste the contents of `daily_prompt.md` into the first routine's prompt.
3. Paste `weekly_prompt.md` into the second.
4. Inject your env vars (`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_ADDRESS`) into both routines.
5. Decide how the routines access `digest.py` + `renderer.py` (see DEPLOYMENT NOTES below).
6. Fire each routine manually once to confirm the email arrives.

---

## Status

| Component | Status |
|---|---|
| Renderer | ✅ Done, verified |
| Fetch + filter (Layer 2 heuristics) | ✅ Done |
| OAuth helper | ✅ Done |
| Send via Gmail API | ✅ Done (untested live) |
| Daily prompt | ✅ Done |
| Weekly prompt | ✅ Done |
| Scheduled routine wiring | ⏸ Blocked — claude.ai remote-trigger system temporarily unreachable |

When remote triggers come back online, the only remaining work is wiring the two routines on claude.ai and firing one test run.

---

## DEPLOYMENT NOTES — getting `digest.py` and `renderer.py` to the routine

The routine runs on Anthropic's infrastructure, not your Mac. It can't read files from `~/Desktop/Newsletter_v2/`. Three options:

**Option A — Embed in prompt (simplest, self-contained)**

Prepend a heredoc block to each routine prompt that writes `digest.py` and `renderer.py` to `/tmp/` before running. Routine becomes ~25 KB, but no external dependencies.

**Option B — Public GitHub repo (cleanest for ongoing iteration)**

Push this directory to a public repo. Add a `git clone` step to each routine prompt. No secrets are in the repo (they live in routine env vars).

**Option C — Single GitHub Gist**

Put `digest.py` + `renderer.py` in one Gist (public). Each routine `curl`s the raw URLs. 5 min of setup, easy to update.

Pick whichever you prefer when we wire up the routines. I'd lean toward **B** if you might tweak the analysis voice over time, **A** if you want pure "set it and forget it."

---

## Costs

- **Anthropic API:** $0 (Claude IS the routine — no separate API calls).
- **Gmail API:** free under your daily quota.
- **claude.ai routine runs:** included in your existing claude.ai plan.

Total ongoing cost: $0.

---

## Privacy

- Your Gmail inbox content is read by the routine.
- Sender addresses, subjects, and body text pass through claude.ai during the run.
- Nothing is persisted by us — `secrets.env` stays local, the routine writes only to its ephemeral filesystem.
- `secrets.env` is gitignored; don't commit it if you ever push this directory anywhere.
