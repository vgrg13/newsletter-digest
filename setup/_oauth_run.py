import pathlib
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

import sys

CLIENT_SECRETS_FILE = "path/to/your-client-secret.json"  # Update this path

if CLIENT_SECRETS_FILE == "path/to/your-client-secret.json":
    sys.exit(
        "Update CLIENT_SECRETS_FILE to point to the JSON file you downloaded\n"
        "from Google Cloud Console → Credentials → your OAuth client → Download."
    )

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
creds = flow.run_local_server(
    port=8765,
    access_type="offline",
    prompt="consent",
    success_message="Authorized! You can close this tab and return to your terminal.",
)

token = creds.refresh_token
client_id = creds.client_id
client_secret = creds.client_secret

print(f"\n✓ Got refresh token: {token[:12]}...")

# Write secrets.env in the project root (two levels up from setup/)
env_path = pathlib.Path(__file__).parent.parent / "secrets.env"
env_path.write_text(
    f'GMAIL_CLIENT_ID="{client_id}"\n'
    f'GMAIL_CLIENT_SECRET="{client_secret}"\n'
    f'GMAIL_REFRESH_TOKEN="{token}"\n'
    f'GMAIL_ADDRESS="your@email.com"  # update this\n'
)
print(f"✓ secrets.env written to {env_path}")
print("Update GMAIL_ADDRESS in secrets.env, then you're done.")
