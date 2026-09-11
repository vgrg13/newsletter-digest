#!/usr/bin/env python3
"""
One-time helper to mint a long-lived Gmail refresh token.

Run this on your Mac:
    python get_refresh_token.py

It walks you through the Google Cloud setup (printing exactly what to click),
opens your browser to authorize, then prints three values you paste into
secrets.env:
    GMAIL_CLIENT_ID
    GMAIL_CLIENT_SECRET
    GMAIL_REFRESH_TOKEN

The refresh token is long-lived as long as you authorize the same Gmail account
you added as a Test User in the OAuth consent screen.
"""
from __future__ import annotations

import sys
import textwrap
from getpass import getpass

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit(
        "Missing dependency. Run:\n"
        "    pip install -r requirements.txt\n"
        "then re-run this script."
    )

# Read + send is everything we need. Compose, modify, settings — not requested.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

SETUP_INSTRUCTIONS = """
================================================================================
Gmail OAuth Setup — one-time, ~10 minutes
================================================================================

You only have to do this once. The refresh token you get at the end goes into
secrets.env and stays valid as long as you don't revoke access in your Google
account.

STEP 1 — Create a Google Cloud project
  1. Open: https://console.cloud.google.com/
  2. Top bar → project dropdown → "New Project"
     Name: newsletter-digest   (anything works)
  3. Wait ~30 seconds for it to provision, then select the new project.

STEP 2 — Enable the Gmail API
  1. Left sidebar → "APIs & Services" → "Library"
  2. Search for "Gmail API" → click it → click "Enable"

STEP 3 — Configure the OAuth consent screen
  1. Left sidebar → "APIs & Services" → "OAuth consent screen"
  2. User type → "External" → "Create"
  3. App name: newsletter-digest
     User support email: vgarg13@berkeley.edu
     Developer contact email: vgarg13@berkeley.edu
     → "Save and Continue"
  4. Scopes page → "Save and Continue" (we'll request scopes at runtime; no
     need to pre-declare here unless Google nags you. If it does, add
     /auth/gmail.readonly and /auth/gmail.send.)
  5. Test users → "+ Add Users" → vgarg13@berkeley.edu → "Save and Continue"
  6. Summary page → "Back to Dashboard"

STEP 4 — Create the OAuth client
  1. Left sidebar → "APIs & Services" → "Credentials"
  2. "+ Create Credentials" → "OAuth client ID"
  3. Application type: "Desktop app"
  4. Name: newsletter-digest-desktop
  5. "Create"
  6. A popup shows your Client ID + Client Secret. Copy both — you'll paste
     them in this script in a moment.

  BERKELEY NOTE: if Google blocks creating External OAuth apps under your
  @berkeley.edu account, run this whole flow using a personal @gmail.com
  Google Cloud account instead — you'll still authenticate vgarg13@berkeley.edu
  at the consent step. The Client ID/Secret just identify the *app*, not the
  *account* whose mail you're reading.

STEP 5 — Paste the values below, then authorize
================================================================================
"""


def main() -> None:
    print(SETUP_INSTRUCTIONS)

    client_id = input("Paste your Client ID and press Enter:\n> ").strip()
    client_secret = getpass("Paste your Client Secret and press Enter (input hidden):\n> ").strip()

    if not client_id or not client_secret:
        sys.exit("Client ID and Client Secret are both required. Aborting.")

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    print(
        "\nOpening your browser to authorize. Sign in as vgarg13@berkeley.edu\n"
        "when prompted. You'll see a 'Google hasn't verified this app' warning\n"
        "— click 'Advanced' → 'Go to newsletter-digest (unsafe)' to continue.\n"
        "This is expected for an unverified personal-use app.\n"
    )

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        authorization_prompt_message="Browser opening... if it didn't, visit:\n  {url}",
        success_message="Authorized! You can close this browser tab and return to the terminal.",
    )

    if not creds.refresh_token:
        sys.exit(
            "Google did not return a refresh token. This usually means you've\n"
            "already authorized this Client ID before. Fix: revoke access at\n"
            "https://myaccount.google.com/permissions, then re-run this script."
        )

    print(
        textwrap.dedent(
            f"""
            ================================================================================
            Success. Paste these three lines into secrets.env:
            ================================================================================

            GMAIL_CLIENT_ID="{client_id}"
            GMAIL_CLIENT_SECRET="{client_secret}"
            GMAIL_REFRESH_TOKEN="{creds.refresh_token}"

            (Also keep GMAIL_ADDRESS="vgarg13@berkeley.edu" in secrets.env.)

            Keep these values private — anyone with all three can read and send
            mail as you. secrets.env is gitignored already.
            ================================================================================
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
