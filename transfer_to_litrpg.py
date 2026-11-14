import os
import re
import sys
import time
import urllib.request
import subprocess
import argparse
import gspread
import google.oauth2.credentials
import google.auth.transport.requests
import google.auth.exceptions
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# ----------------- CONFIGURATION -----------------
BASE_DIR = r"D:\Projects\visualer"
YOUTUBE_CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secret.json")

# Main account token (reads Google Sheet & fetches @beingabong metadata)
MAIN_TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

# Sub-channel account token (uploads to @LitRPGStories)
LITRPG_TOKEN_FILE = os.path.join(BASE_DIR, "token_litrpg.json")

TEMP_DIR = os.path.join(BASE_DIR, "temp_transfer")

# Exact spreadsheet URL from your reference script
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1E4W_poEdZXfu0-Xxizgh9rh_1JLYF8AzD142IOr24E0/edit?gid=0#gid=0"
WORKSHEET_NAME = "Videos"

MAIN_SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

LITRPG_SCOPES = [
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

CLIP_DURATION_SECONDS = 900   # 15 minutes
PRIVACY_STATUS = "public"     # Change to "unlisted" or "private" if needed
MAX_RETRIES = 3
COOLDOWN_SECONDS = 20


def log(msg):
    print(msg, flush=True)


def get_authenticated_credentials(token_path, scopes, account_label):
    creds = None
    if os.path.exists(token_path):
        try:
            creds = google.oauth2.credentials.Credentials.from_authorized_user_file(token_path, scopes)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                log(f"[*] Refreshing token for {account_label}...")
                creds.refresh(google.auth.transport.requests.Request())
            except google.auth.exceptions.RefreshError:
                log(f"[!] Refresh failed for {account_label}. Re-authenticating...")
                creds = None
                if os.path.exists(token_path):
                    os.remove(token_path)

        if not creds or not creds.valid:
            if not os.path.exists(YOUTUBE_CLIENT_SECRETS_FILE):
                raise FileNotFoundError(f"Missing OAuth secret file at: '{YOUTUBE_CLIENT_SECRETS_FILE}'.")
            log(f"[ACTION REQUIRED] Browser opening for {account_label}...")
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRETS_FILE, scopes
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())
        log(f"[+] Token saved to {token_path}")

    return creds


def extract_video_id(url):
    if not url:
        return None
    match = re.search(r"(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})", str(url))
    return match.group(1) if match else None


def find_video_url_in_row(row_dict):
    for key in ["Direct Watch URL", "Video URL", "Video Link", "URL", "Link", "Youtube Link", "YouTube Link", "Video"]:
        val = row_dict.get(key)
        if val and extract_video_id(str(val)):
            return str(val).strip()

    for _, val in row_dict.items():
        if val and ("watch?v=" in str(val) or "youtu.be/" in str(val)):
            if extract_video_id(str(val)):
                return str(val).strip()
    return None


def get_target_videos(sheets_creds, start_num, end_num):
    low, high = min(start_num, end_num), max(start_num, end_num)

    gc = gspread.authorize(sheets_creds)
    sheet = gc.open_by_url(SPREADSHEET_URL).worksheet(WORKSHEET_NAME)
    records = sheet.get_all_records()

    log(f"[+] Loaded {len(records)} records from '{WORKSHEET_NAME}'. Filtering # {low} to {high}...")

    targets = []
    for r in records:
        raw_num = str(r.get("#", "")).strip()
        if not raw_num.isdigit():
            continue

        vid_num = int(raw_num)
        if low <= vid_num <= high:
            url = find_video_url_in_row(r)
            vid_id = extract_video_id(url)
            if vid_id:
                targets.append({
                    "num": vid_num,
                    "url": url,
                    "video_id": vid_id
                })
            else:
                log(f"[!] Row #{vid_num} skipped: no valid YouTube URL found.")

    targets.sort(key=lambda x: x["num"])
    return targets

def fetch_source_metadata(youtube_main, video_id):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = youtube_main.videos().list(
                part="snippet",
                id=video_id
            ).execute()
            items = res.get("items", [])
            if not items:
                raise ValueError(f"Video ID {video_id} not found on @beingabong.")

            snippet = items[0]["snippet"]
            thumbnails = snippet.get("thumbnails", {})
            thumb_url = None
            for quality in ["maxres", "standard", "high", "medium", "default"]:
                if quality in thumbnails and "url" in thumbnails[quality]:
                    thumb_url = thumbnails[quality]["url"]
                    break

            return {
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "tags": snippet.get("tags", []),
                "categoryId": snippet.get("categoryId", "24"),
                "thumbnail_url": thumb_url
            }
        except Exception as e:
            if attempt < MAX_RETRIES:
                log(f"  [!] Metadata fetch error ({e}). Retrying in {COOLDOWN_SECONDS}s ({attempt}/{MAX_RETRIES})...")
                time.sleep(COOLDOWN_SECONDS)
            else:
                raise



def download_first_15_mins(video_url, output_video_path):
    os.makedirs(TEMP_DIR, exist_ok=True)
    if os.path.exists(output_video_path):
        os.remove(output_video_path)

    cmd = [
        "yt-dlp",
        "--download-sections", f"*0-{CLIP_DURATION_SECONDS}",
        "--force-keyframes-at-cuts",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", output_video_path,
        video_url
    ]
    log(f"  -> Downloading first 15 mins from {video_url}...")
    subprocess.run(cmd, check=True)


def download_thumbnail(thumb_url, output_thumb_path):
    if not thumb_url:
        return None
    os.makedirs(TEMP_DIR, exist_ok=True)
    if os.path.exists(output_thumb_path):
        os.remove(output_thumb_path)
    urllib.request.urlretrieve(thumb_url, output_thumb_path)
    return output_thumb_path


def format_subchannel_description(original_description):
    snippet_250 = original_description[:250].strip()
    cta = (
        "\n\nSubscribe to our main channel https://youtube.com/@beingabong "
        "for full episodes and complete audiobook marathons!"
    )
    return f"{snippet_250}{cta}"


def upload_video_and_thumbnail(youtube_litrpg, video_path, thumb_path, meta, new_description):
    body = {
        "snippet": {
            "title": meta["title"],
            "description": new_description,
            "tags": meta["tags"],
            "categoryId": meta["categoryId"]
        },
        "status": {
            "privacyStatus": PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        video_path,
        chunksize=10 * 1024 * 1024,
        resumable=True,
        mimetype="video/mp4"
    )

    request = youtube_litrpg.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    log(f"  -> Uploading '{meta['title'][:60]}' to @LitRPGStories...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log(f"     Upload progress: {int(status.progress() * 100)}%")

    new_video_id = response["id"]
    log(f"  [+] Video uploaded! New URL: https://youtu.be/{new_video_id}")

    if thumb_path and os.path.exists(thumb_path):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                youtube_litrpg.thumbnails().set(
                    videoId=new_video_id,
                    media_body=MediaFileUpload(thumb_path, mimetype="image/jpeg")
                ).execute()
                log("  [+] Thumbnail copied and applied successfully.")
                break
            except googleapiclient.errors.HttpError as e:
                if e.resp.status == 403:
                    log("  [!] Thumbnail upload blocked (403): Ensure phone verification is enabled on @LitRPGStories.")
                    break
                if attempt < MAX_RETRIES:
                    log(f"  [!] Thumbnail upload error ({e}). Retrying in {COOLDOWN_SECONDS}s ({attempt}/{MAX_RETRIES})...")
                    time.sleep(COOLDOWN_SECONDS)
                else:
                    log(f"  [-] Failed to set thumbnail after {MAX_RETRIES} attempts: {e}")
            except Exception as e:
                if attempt < MAX_RETRIES:
                    log(f"  [!] Thumbnail upload error ({e}). Retrying in {COOLDOWN_SECONDS}s ({attempt}/{MAX_RETRIES})...")
                    time.sleep(COOLDOWN_SECONDS)
                else:
                    log(f"  [-] Failed to set thumbnail after {MAX_RETRIES} attempts: {e}")

    return new_video_id


def main():
    parser = argparse.ArgumentParser(description="Transfer 15-min clips and thumbnails from @beingabong to @LitRPGStories.")
    parser.add_argument("start", type=int, help="Starting Video # from Column A")
    parser.add_argument("end", type=int, help="Ending Video # from Column A")
    args = parser.parse_args()

    log("=== @beingabong -> @LitRPGStories 15-Min Transfer (With Thumbnails) ===")

    main_creds = get_authenticated_credentials(MAIN_TOKEN_FILE, MAIN_SCOPES, "Main Account (@beingabong)")
    litrpg_creds = get_authenticated_credentials(LITRPG_TOKEN_FILE, LITRPG_SCOPES, "Sub-Channel (@LitRPGStories)")

    youtube_main = googleapiclient.discovery.build("youtube", "v3", credentials=main_creds)
    youtube_litrpg = googleapiclient.discovery.build("youtube", "v3", credentials=litrpg_creds)

    targets = get_target_videos(main_creds, args.start, args.end)

    if not targets:
        log(f"[-] No videos found in range #{args.start} to #{args.end}.")
        sys.exit(0)

    log(f"[+] Found {len(targets)} video(s) to transfer.\n")

    for item in targets:
        vid_num = item["num"]
        vid_id = item["video_id"]
        vid_url = item["url"]

        temp_video = os.path.join(TEMP_DIR, f"vid_{vid_num}_{vid_id}.mp4")
        temp_thumb = os.path.join(TEMP_DIR, f"thumb_{vid_num}_{vid_id}.jpg")

        log(f"=== Processing Video #{vid_num} | Source ID: {vid_id} ===")
        try:
            meta = fetch_source_metadata(youtube_main, vid_id)
            new_desc = format_subchannel_description(meta["description"])

            download_first_15_mins(vid_url, temp_video)
            saved_thumb = download_thumbnail(meta["thumbnail_url"], temp_thumb)

            upload_video_and_thumbnail(youtube_litrpg, temp_video, saved_thumb, meta, new_desc)

            log(f"=== Completed Video #{vid_num} ===\n")
            time.sleep(2)

        except Exception as e:
            log(f"[-] Error processing Video #{vid_num} ({vid_id}): {e}\n")

        finally:
            for f_path in [temp_video, temp_thumb]:
                if os.path.exists(f_path):
                    try:
                        os.remove(f_path)
                    except OSError:
                        pass

    log("=== Batch Transfer Finished ===")


if __name__ == "__main__":
    main()
