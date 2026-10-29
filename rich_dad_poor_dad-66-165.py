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


BUILD_DIR = "build_rich_dad_poor_dad_66_165"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source: Local PDF path and Page range
    "novel_slug": "rich-dad-poor-dad",
    "start_url": r"D:\Projects\visualer\ebooks\Rich Dad Poor Dad eBook.pdf",
    "start_chapter": 66,
    "end_chapter": 165,
    "is_start": False,  # Continues from previous episode; suppresses start-of-series greeting and unneeded title prepend
    "default_topic": "Rich Dad Poor Dad / Personal Finance / Financial Literacy / Robert Kiyosaki / Corporations and Taxes / Investing",

    # Concurrency & Hard-locked Narrator Voice
    "batch_size": 4,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story / Premise Hook
    "intro_hook": "Mastering the legal power of corporations, understanding how the tax code incentivizes asset builders, and training your mind to invent money transforms ordinary earners into financially sovereign investors.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_rich_dad_poor_dad_66_165.mp3",
    "final_video": "final_rich_dad_poor_dad_66_165.mp4",
    "cover_image": "cover_rich_dad_poor_dad_66_165.jpg",
    "timestamps_file": "youtube_timestamps_rich_dad_poor_dad_66_165.txt",
    "subtitles_file": "subtitles_rich_dad_poor_dad_66_165.srt",
    "payload_file": "youtube_upload_payload_rich_dad_poor_dad_66_165.json",

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
    "video_title": "Rich Dad Poor Dad | Full Audiobook Marathon (Pages 66 - 165) | Mind Your Own Business & The Power of Corporations",
    "privacy_status": "unlisted",
    "tags": [
        "Rich Dad Poor Dad", "Robert Kiyosaki", "Rich Dad Poor Dad Audiobook",
        "Personal Finance", "Financial Literacy", "Corporations and Taxes", "Inventing Money",
        "Cash Flow", "Investing Strategies", "Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "This episode, we step right back into the story, continuing exactly where we left off in our previous episode of this series.\n\n"
        "Experience 'Rich Dad Poor Dad' by Robert Kiyosaki (Pages 66 to 165) — Corporate Power & The Science of Inventing Money.\n\n"
        "Delving deeper into financial mastery, this volume explores Lesson Three through Lesson Six: "
        "minding your own business, the history of taxes, why corporations protect wealth, the four pillars of financial IQ, and learning to work to learn rather than work for money.\n\n"
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
        "#RichDadPoorDad #RobertKiyosaki #PersonalFinance #FinancialLiteracy #CashFlowQuadrant #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Visual Arc Blocks across Pages 66 to 165 (100 pages partitioned)
    "blocks": [
        {
            "index": 1, "range": (66, 90),
            "title": ["LESSON THREE", "MIND YOUR OWN BUSINESS"],
            "fallback_color": (22, 24, 30),
            "prompt": (
                "Cinematic high-angle view of a sophisticated corner executive office overlooking illuminated financial district towers at night, "
                "minimalist mahogany desk with architectural blueprints, financial ledgers, and a fountain pen resting on parchment, dramatic warm and cool lighting, 4K digital photography."
            )
        },
        {
            "index": 2, "range": (91, 115),
            "title": ["THE HISTORY OF TAXES", "THE POWER OF CORPORATIONS"],
            "fallback_color": (26, 20, 16),
            "prompt": (
                "Cinematic classical judicial and corporate library with towering dark walnut bookshelves, emerald banker lamps glowing on polished oak tables, "
                "gilded legal codes and parchment contracts, representing institutional wealth protection and corporate structure, 4K resolution."
            )
        },
        {
            "index": 3, "range": (116, 140),
            "title": ["LESSON FIVE", "THE RICH INVENT MONEY"],
            "fallback_color": (16, 24, 26),
            "prompt": (
                "Cinematic conceptual shot of a glowing brass compass and golden geometric ratio compasses resting on antique trade maps and real estate surveys, "
                "subtle golden volumetric light rays cutting through misty atmosphere, representing financial foresight and creative deal-making, 4K masterpiece."
            )
        },
        {
            "index": 4, "range": (141, 165),
            "title": ["WORK TO LEARN", "DON'T WORK FOR MONEY"],
            "fallback_color": (24, 18, 22),
            "prompt": (
                "Modern architectural pavilion with floor-to-ceiling glass looking out over a sunrise horizon, "
                "a confident visionary strategist in sharp tailoring observing a stylized architectural model of commercial buildings, golden hour reflections, 4K concept art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
