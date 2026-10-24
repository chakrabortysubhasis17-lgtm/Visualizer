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


BUILD_DIR = "build_shangrila_frontier_151_200"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "shangrila-frontier",
    "start_url": "https://freewebnovel.com/novel/shangriLa-frontier-shitty-games-hunter-challenges-godly-game/chapter-249",
    "start_chapter": 151,
    "end_chapter": 200,
    "default_topic": "Shangri-La Frontier / VRMMO / Sunraku / Kutanid of the Abyss / City of Lulurie",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We plunge deep into the ocean depths as Sunraku and his raid party navigate the inverted city of Lulurie to challenge Kutanid of the Abyss, one of the Seven Colossi.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_shangrila_frontier_151_200.mp3",
    "final_video": "final_shangrila_frontier_151_200.mp4",
    "cover_image": "cover_shangrila_frontier_151_200.jpg",
    "timestamps_file": "youtube_timestamps_shangrila_frontier_151_200.txt",
    "subtitles_file": "subtitles_shangrila_frontier_151_200.srt",
    "payload_file": "youtube_upload_payload_shangrila_frontier_151_200.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages to build/subtitles/)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "Shangri-La Frontier | Ch 151 - 200 Full Audio Novel Marathon | Kutanid of the Abyss Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Shangri-La Frontier", "Shangri La Frontier Audiobook", "Sunraku", "Rakuro Hizutome",
        "Kutanid of the Abyss", "City of Lulurie", "Seven Colossi", "Emul", "Arthur Pencilgon",
        "Oikatzo", "VRMMO Audiobook", "LitRPG Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Shangri-La Frontier' (Chapters 151 to 200) — the high-stakes Kutanid of the Abyss Arc.\n\n"
        "Descending into the unfathomable depths of the ocean, Sunraku, Emul, and an elite vanguard of explorers uncover the sunken, "
        "inverted metropolis of Lulurie. But clearing the ancient city's eight bell towers awakens an entity beyond mortal comprehension: "
        "Kutanid of the Abyss, a Colossus capable of twisting the very laws of reality. Witness mind-bending rule reversals, "
        "flawless aquatic parry combat, and the birth of new gaming legends.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#ShangriLaFrontier #Sunraku #Kutanid #SevenColossi #Lulurie #VRMMO #LitRPG #GamingAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 151 to 200 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (151, 160),
            "title": ["THE SUNKEN METROPOLIS", "GATES OF LULURIE"],
            "fallback_color": (10, 20, 30),
            "prompt": (
                "Cinematic underwater fantasy vista of a colossal ancient metropolis submerged beneath the sea inside an atmospheric air pocket, "
                "glowing cyan bioluminescent spires and spiraling stone towers, a shirtless adventurer wearing a blue bird mask "
                "and carrying dual jagged daggers standing on a bridge alongside an armored party, ethereal water reflections, hyper-detailed 4K."
            )
        },
        {
            "index": 2, "range": (161, 170),
            "title": ["TRIALS OF THE EIGHT BELLS", "CORAL GUARDIANS"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic dynamic fantasy battle scene in an ancient coral courtyard, armored guardians with barnacle-encrusted shields "
                "and trident spears clashing against agile player heroes, a female magician conjuring glowing water runes beside a towering brass bell spire, "
                "dramatic blue and gold volumetric lighting, dust particles, motion blur."
            )
        },
        {
            "index": 3, "range": (171, 180),
            "title": ["DESCENT OF KUTANID", "THE INVERTED REALM"],
            "fallback_color": (15, 10, 25),
            "prompt": (
                "Cinematic eldritch dark fantasy showdown, an immense cephalopod colossus floating above an inverted sea surface where water flows upward, "
                "massive tentacular appendages shifting reality with shimmering violet distorted space, the bird-masked rogue looking up in awe from shattered masonry, "
                "ominous chiaroscuro lighting, epic scale composition."
            )
        },
        {
            "index": 4, "range": (181, 190),
            "title": ["RULE OF REVERSAL", "PARRYING THE VOID"],
            "fallback_color": (25, 15, 20),
            "prompt": (
                "Cinematic high-octane anime action shot, the bird-masked protagonist executing an upside-down aerial parry across gravity-defying stone rubble, "
                "crimson and turquoise sparks flying as dagger edges deflect an invisible spatial distortion shockwave, "
                "glowing VR interface counters displaying reversed stat gauges, intense cinematic camera angle."
            )
        },
        {
            "index": 5, "range": (191, 200),
            "title": ["ABYSSAL CLEANSING", "DAWN OF THE DEEP"],
            "fallback_color": (20, 30, 30),
            "prompt": (
                "Cinematic breathtaking wide angle panoramic view as deep ocean waters part, brilliant divine rays of sunlight piercing thousands of leagues down "
                "onto the tranquil ruins of the underwater city, exhausted victorious heroes standing around a glowing ancient monument, "
                "particles of light ascending toward the distant surface, masterpiece 4K rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
