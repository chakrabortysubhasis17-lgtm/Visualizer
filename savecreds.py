import os
import google_auth_oauthlib.flow

CLIENT_SECRETS_FILE = r"D:\Projects\visualer\client_secret.json"
TOKEN_LITRPG_FILE = r"D:\Projects\visualer\token_litrpg.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.upload"
]


def authorize_subchannel():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        raise FileNotFoundError(f"Cannot find {CLIENT_SECRETS_FILE}")

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES
    )
    print("Opening browser... Sign in with the @LitRPGStories Google account.")
    creds = flow.run_local_server(port=0)

    with open(TOKEN_LITRPG_FILE, "w", encoding="utf-8") as f:
        f.write(creds.to_json())

    print(f"Success! Saved sub-channel credentials to {TOKEN_LITRPG_FILE}")

if __name__ == "__main__":
    authorize_subchannel()
