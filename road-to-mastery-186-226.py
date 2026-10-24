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


BUILD_DIR = "build_road_to_mastery_186_226"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-186",
    "start_chapter": 186,
    "end_chapter": 226,
    "default_topic": "Road to Mastery / LitRPG Apocalypse / Jackie / Brawler Pugilist / System Trials",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We rejoin Jackie as he unleashes explosive brawler arts across brutal apocalypse trials, shattering limits with pure grit and devastating fists.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_road_to_mastery_186_226.mp3",
    "final_video": "final_road_to_mastery_186_226.mp4",
    "cover_image": "cover_road_to_mastery_186_226.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_186_226.txt",
    "subtitles_file": "subtitles_road_to_mastery_186_226.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_186_226.json",

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
    "video_title": "Road to Mastery: A LitRPG Apocalypse | Ch 186 - 226 Full Marathon | Apex Brawler Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Road to Mastery", "Road to Mastery Audiobook", "LitRPG Apocalypse", "Jackie",
        "Brawler LitRPG", "Progression Fantasy", "System Apocalypse", "Pugilist",
        "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 41-chapter audio novel marathon of 'Road to Mastery: A LitRPG Apocalypse' (Chapters 186 to 226) — the Apex Brawler Arc.\n\n"
        "Follow Jackie as the System apocalypse forces humanity through ruthless tier trials and planetary conquests. "
        "Armed with unyielding determination, bare-knuckle pugilist techniques, and devastating kinetic momentum, Jackie shatters through "
        "monstrous bosses, high-tier adversaries, and deadly trial zones to forge his path toward true martial mastery.\n\n"
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
        "#RoadToMastery #LitRPG #SystemApocalypse #ProgressionFantasy #Brawler #AudiobookMarathon #BeingABong"
    ),

    # 4 Thematic Arc Visual Blocks for Chapters 186 to 226
    "blocks": [
        {
            "index": 1, "range": (186, 195),
            "title": ["KINETIC IMPACT", "THE BRAWLER'S TRIAL"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic 3D action shot of a muscular martial brawler with glowing mana wraps around his fists "
                "delivering an explosive shockwave punch into the armored chest of a towering demonic beast inside a ruined apocalyptic stadium, "
                "sparks and fractured concrete flying, volumetric dust motes, dramatic rim lighting, 4K resolution."
            )
        },
        {
            "index": 2, "range": (196, 205),
            "title": ["SYSTEM ESCALATION", "ZONE BREAKTHROUGH"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic high-detail fantasy vista of an apocalyptic wasteland littered with glowing alien monoliths and floating holographic system glyphs, "
                "a determined brawler warrior standing atop shattered stone rubble surveying an incoming horde of mutated trial fiends, "
                "stormy twilight sky, electric blue energy arcing across the battlefield."
            )
        },
        {
            "index": 3, "range": (206, 215),
            "title": ["IRON RESOLVE", "COLOSSAL CLASH"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic dynamic combat sequence in a volcanic dungeon cavern, a fierce human fighter clad in reinforced leather wraps "
                "ducking beneath the fiery cleave of a giant molten golem and countering with a blazing uppercut, "
                "crimson embers, intense heat distortion, dramatic action camera angle."
            )
        },
        {
            "index": 4, "range": (216, 226),
            "title": ["PATH TO APEX", "UNBREAKABLE BODY"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic wide heroic composition at dawn atop a towering peak overlooking a reclaimed post-apocalyptic realm, "
                "the victorious martial artist resting against a cracked boulder with golden morning light illuminating his scarred fists, "
                "fading translucent system level-up banners floating in the cool morning mist, masterpiece rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
