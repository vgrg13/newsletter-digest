import pathlib
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

CLIENT_SECRETS_FILE = "/Users/vatsalgarg/Downloads/client_secret_2_56532551274-9n190aoc64gdd3sh1r9godahumqsblkf.apps.googleusercontent.com.json"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
creds = flow.run_local_server(
    port=8765,
    access_type="offline",
    prompt="consent",
    success_message="✓ Authorized! You can close this tab and return to Claude Code.",
)

token = creds.refresh_token
client_id = creds.client_id
client_secret = creds.client_secret

print(f"\n✓ Got refresh token: {token[:12]}...")

# Write secrets.env
env_path = pathlib.Path("/Users/vatsalgarg/Desktop/Newsletter_v2/secrets.env")
env_path.write_text(
    f'GMAIL_CLIENT_ID="{client_id}"\n'
    f'GMAIL_CLIENT_SECRET="{client_secret}"\n'
    f'GMAIL_REFRESH_TOKEN="{token}"\n'
    f'GMAIL_ADDRESS="vgarg13@berkeley.edu"\n'
)
print("✓ secrets.env written.")
print("Done — all credentials saved.")
