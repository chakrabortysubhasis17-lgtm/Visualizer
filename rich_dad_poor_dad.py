import os
import json
import asyncio
from pipeline_orchestrator import run_audiobook_pipeline

CREDENTIALS_FILE = "api_credentials.json"


def load_credentials(file_path: str = CREDENTIALS_FILE) -> dict:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to parse '{file_path}': {e}", flush=True)
    return {}


creds = load_credentials()

# Credential resolution with multi-key/account fallback
gemini_key = creds.get("gemini_api_key")
if not gemini_key and creds.get("gemini_api_keys"):
    for k in creds["gemini_api_keys"]:
        if k and not k.startswith("PASTE_") and not k.startswith("YOUR_"):
            gemini_key = k
            break
gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY", "")

cf_id = creds.get("cloudflare_account_id")
cf_token = creds.get("cloudflare_api_token")
if (not cf_id or not cf_token) and creds.get("cloudflare_accounts"):
    for acc in creds["cloudflare_accounts"]:
        if isinstance(acc, dict) and acc.get("account_id") and not acc.get("account_id").startswith("PASTE_"):
            cf_id = cf_id or acc.get("account_id")
            cf_token = cf_token or acc.get("api_token")
            break
cf_id = cf_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
cf_token = cf_token or os.environ.get("CLOUDFLARE_API_TOKEN", "")


def purge_corrupt_or_fallback_cache(build_dir: str):
    """
    Purges placeholder files, corrupt manifests, and rule-based fallback files
    staged during earlier runs without Gemini credentials.
    """
    if not os.path.exists(build_dir):
        return
    removed = 0
    for fname in os.listdir(build_dir):
        if fname.startswith("ch_") and fname.endswith("_staged.json"):
            fpath = os.path.join(build_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rows = data.get("rows", [])

                is_dummy = len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows)
                is_fallback_only = not any(r.get("speaker") not in ["Narrator", "Mc", "System"] for r in rows)

                if is_dummy or is_fallback_only:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [OK] Purged {removed} invalid/fallback staged files. Gemini Director will parse cleanly.", flush=True)


BUILD_DIR = "build_rich_dad_poor_dad_16_65"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range
    "novel_slug": "rich-dad-poor-dad",
    "start_url": r"D:\Projects\visualer\ebooks\Rich Dad Poor Dad eBook.pdf",
    "start_chapter": 16,
    "end_chapter": 65,
    "is_start": True,
    "default_topic": "Rich Dad Poor Dad / Personal Finance / Financial Literacy / Robert Kiyosaki / Assets vs Liabilities",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story / Premise Hook
    "intro_hook": "Examining the contrasting philosophies of two father figures—one highly educated yet financially constrained, the other an eighth-grade dropout building an empire—unveils the fundamental difference between laboring for money and making money work for you.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_rich_dad_poor_dad_16_65.mp3",
    "final_video": "final_rich_dad_poor_dad_16_65.mp4",
    "cover_image": "cover_rich_dad_poor_dad_16_65.jpg",
    "timestamps_file": "youtube_timestamps_rich_dad_poor_dad_16_65.txt",
    "subtitles_file": "subtitles_rich_dad_poor_dad_16_65.srt",
    "payload_file": "youtube_upload_payload_rich_dad_poor_dad_16_65.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "Rich Dad Poor Dad | Full Audiobook (Pages 16 - 65) | What The Rich Teach Their Kids About Money",
    "privacy_status": "unlisted",
    "tags": [
        "Rich Dad Poor Dad", "Robert Kiyosaki", "Rich Dad Poor Dad Audiobook",
        "Personal Finance", "Financial Literacy", "Money Mindset", "Assets vs Liabilities",
        "Cash Flow", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Rich Dad Poor Dad' by Robert Kiyosaki (Pages 16 to 65) — Foundations of Financial Independence.\n\n"
        "Contrasting the mindsets of two paternal guides, this segment unpacks foundational principles: "
        "why the rich do not work for money, the vital necessity of financial literacy, and the critical distinction between real assets and liabilities.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audio presentation is an educational and commentary reading produced for literature review, personal finance education, and study purposes.\n\n"
        "#RichDadPoorDad #RobertKiyosaki #PersonalFinance #FinancialLiteracy #Audiobook #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Pages 16 to 65
    "blocks": [
        {
            "index": 1, "range": (16, 28),
            "title": ["THE RAT RACE", "FEAR AND DESIRE"],
            "fallback_color": (20, 22, 28),
            "prompt": (
                "Cinematic high-contrast photograph of a sleek modern city skyline at dusk with commuters moving like shadows beneath towering glass skyscrapers, "
                "warm amber office windows contrasting with deep twilight blues, subtle geometric architectural composition, 4K resolution."
            )
        },
        {
            "index": 2, "range": (29, 41),
            "title": ["LESSON ONE", "THE RICH DON'T WORK FOR MONEY"],
            "fallback_color": (24, 20, 16),
            "prompt": (
                "Cinematic vintage study room illuminated by warm afternoon sunlight through tall Venetian blinds, "
                "a polished dark mahogany desk with classic ledger books, fountain pen, and financial charts, sophisticated atmosphere, 4K digital photography."
            )
        },
        {
            "index": 3, "range": (42, 53),
            "title": ["LESSON TWO", "WHY TEACH FINANCIAL LITERACY"],
            "fallback_color": (16, 24, 22),
            "prompt": (
                "Minimalist architectural composition of an expansive modern library with marble pillars and tall windows overlooking a misty green courtyard, "
                "geometric interplay of clean lines, light, and shadow, representing clarity and structured knowledge, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (54, 65),
            "title": ["ASSETS VS LIABILITIES", "THE FLOW OF WEALTH"],
            "fallback_color": (22, 18, 26),
            "prompt": (
                "Cinematic conceptual render of a pristine chessboard crafted from dark smoked glass and polished brass, "
                "dramatic side rim-lighting casting sharp cast shadows across a polished stone floor, symbolic of strategic long-term planning, 4K."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
