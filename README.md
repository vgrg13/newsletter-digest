# newsletter-digest

Automated Gmail newsletter digest — fetches your inbox via the Gmail API, has Claude analyze and summarize the content, renders a styled HTML email, and sends it back to you. No Anthropic API costs, no third-party services.

- **Daily digest** — sent once per day Monday–Saturday (fires at 8, 10, 12, 2, and 4 PM local time; first successful send wins)
- **Weekly digest** — sent every Sunday at 5 PM, covering the full week

---

## How it works

1. A Claude Code scheduled task wakes up on a cron schedule
2. It runs `digest.py` to fetch newsletters from your Gmail inbox via OAuth (no IMAP)
3. Claude reads the content, identifies top stories and themes, and writes a structured JSON analysis
4. `renderer.py` turns the analysis into a styled HTML email
5. The email is sent back to you via the Gmail API

Claude is the analyst — there are no separate API calls or costs beyond your existing Claude plan.

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/vgrg13/newsletter-digest.git
cd newsletter-digest
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create a Gmail OAuth app

You need a Google Cloud project with a Gmail API OAuth client. This takes about 10 minutes:

1. Go to [console.cloud.google.com](https://console.cloud.google.com) and create a new project
2. Enable the **Gmail API** (APIs & Services → Enable APIs → search "Gmail API")
3. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
4. Choose **Desktop app**, give it a name, click Create
5. Download the JSON or note your **Client ID** and **Client Secret**

> If you're using a Google Workspace account (e.g. a university email) and Google blocks creating an OAuth app, create the Cloud project under a personal `@gmail.com` account instead. You'll still authenticate your real mailbox at the consent screen — the OAuth client just identifies the app, not the mailbox.

### 3. Get a refresh token

```bash
python get_refresh_token.py
```

Follow the prompts. The script opens your browser for the OAuth consent screen and prints your refresh token.

### 4. Create `secrets.env`

```bash
cp secrets.env.example secrets.env
```

Fill in the four values:

```
GMAIL_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GMAIL_CLIENT_SECRET="your-client-secret"
GMAIL_REFRESH_TOKEN="1//0g..."
GMAIL_ADDRESS="you@gmail.com"
```

`secrets.env` is gitignored — never commit it.

### 5. Test locally

```bash
source .venv/bin/activate
set -a; source secrets.env; set +a

# Fetch last 24 hours of newsletters
python3 -c "
import sys, json, os
os.chdir('.')
sys.path.insert(0, '.')
import digest
newsletters = digest.fetch(since_hours=24, max_msgs=50)
print(f'Fetched {len(newsletters)} newsletters')
for n in newsletters:
    print(f'  {n[\"source\"]:30s} | {n[\"subject\"][:60]}')
"
```

### 6. Wire up scheduled tasks

This project uses **Claude Code scheduled tasks** (requires Claude Code desktop app).

1. Copy the template SKILL.md files to the Claude Code tasks directory:

```bash
mkdir -p ~/.claude/scheduled-tasks/newsletter-daily-digest
mkdir -p ~/.claude/scheduled-tasks/newsletter-weekly-digest
cp scheduled-tasks/daily/SKILL.md ~/.claude/scheduled-tasks/newsletter-daily-digest/SKILL.md
cp scheduled-tasks/weekly/SKILL.md ~/.claude/scheduled-tasks/newsletter-weekly-digest/SKILL.md
```

2. In each copied file, replace every occurrence of `YOUR_PROJECT_PATH` with the absolute path to your repo (e.g. `/Users/yourname/newsletter-digest`).

3. Set the cron schedules in Claude Code:
   - Daily: `0 8,10,12,14,16 * * 1-6` (Mon–Sat, fires 5× per day; sentinel prevents double-sends)
   - Weekly: `0 17 * * 0` (Sundays at 5 PM local time)

The Claude Code app must be open at the scheduled time for tasks to fire. Missed fires are skipped, not retried — the multi-fire daily schedule compensates for this.

---

## Project structure

```
digest.py                        # Gmail fetch, OAuth, newsletter classification, send
renderer.py                      # HTML email renderer (daily + weekly templates)
requirements.txt
secrets.env.example              # Template — copy to secrets.env and fill in your values
data/
  senders_allowlist.txt          # Senders always included (edit to match your subscriptions)
  senders_blocklist.txt          # Senders always excluded (add your own noise)
scheduled-tasks/
  daily/SKILL.md                 # Claude Code scheduled task for the daily digest
  weekly/SKILL.md                # Claude Code scheduled task for the weekly digest
setup/
  get_refresh_token.py           # One-time helper to mint your Gmail OAuth refresh token
  _oauth_run.py                  # Alternative OAuth runner if you have the JSON file
samples/                         # Reference HTML showing what the digest looks like
output/                          # Gitignored — runtime artifacts (JSON analysis, sentinel files)
```

---

## Newsletter classification

Newsletters are filtered through four layers:

1. **Allowlist** — known senders always included (configured in `digest.py`)
2. **Header heuristics** — checks `List-Unsubscribe`, `List-Id`, `Precedence`
3. **Claude tiebreaker** — Claude reads ambiguous content and decides
4. **Blocklist** — known noise senders always excluded

---

## Cost

- **Anthropic API:** $0 — Claude runs as the scheduled task itself, no separate API calls
- **Gmail API:** free (well within daily quota)
- **Claude Code:** included in your existing plan

---

## Privacy

- Your Gmail inbox content is read locally by `digest.py` and passed to Claude during the scheduled task run
- `secrets.env` stays local and is gitignored
- Nothing is stored externally
