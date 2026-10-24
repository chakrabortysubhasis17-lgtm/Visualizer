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


BUILD_DIR = "build_shangrila_frontier_001_050"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "shangrila-frontier",
    "start_url": "https://freewebnovel.com/novel/shangriLa-frontier-shitty-games-hunter-challenges-godly-game/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Shangri-La Frontier / VRMMO / Sunraku / Kusoge Hunter / Lycagon",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Intelligently extracted for this novel)
    "intro_hook": "We will meet a veteran trash-game hunter who spends his life conquering the most broken, bug-ridden games in existence.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_shangrila_frontier_001_050.mp3",
    "final_video": "final_shangrila_frontier_001_050.mp4",
    "cover_image": "cover_shangrila_frontier_001_050.jpg",
    "timestamps_file": "youtube_timestamps_shangrila_frontier_001_050.txt",
    "subtitles_file": "subtitles_shangrila_frontier_001_050.srt",
    "payload_file": "youtube_upload_payload_shangrila_frontier_001_050.json",

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
    "video_title": "Shangri-La Frontier | Ch 1 - 50 Full Audio Novel Marathon | Lycagon & Rabituza Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Shangri-La Frontier", "Shangri La Frontier Audiobook", "Sunraku", "Rakuro Hizutome",
        "Lycagon the Nightslayer", "Emul", "Rabituza", "VRMMO Audiobook", "LitRPG Audiobook",
        "Progression Fantasy", "Audiobook Marathon", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Shangri-La Frontier: Shitty Games Hunter Challenges Godly Game' (Chapters 1 to 50).\n\n"
        "Meet Rakuro Hizutome, a veteran 'kusoge hunter' who thrives on beating the most glitch-ridden, unbalanced trash games in existence. "
        "When he finally dives into the undisputed god-tier VRMMO 'Shangri-La Frontier', he spawns wearing nothing but short trousers and a blue bird mask—selling all his armor for agility stats. "
        "Follow Sunraku as he parries his way through deadly starter bosses, clashes with the Unique Monster Lycagon the Nightslayer, receives the dreaded Wolf Curse, "
        "and triggers the legendary Unique Scenario: 'An Invitation from Rabituza'.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Baritone Delivery).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#ShangriLaFrontier #Sunraku #VRMMO #LitRPG #GamingAudiobook #ProgressionFantasy #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 1 to 50 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (1, 10),
            "title": ["TRASH-GAME HUNTER", "FIRST STEP INTO GOD-TIER"],
            "fallback_color": (20, 25, 30),
            "prompt": (
                "Cinematic high-action anime scene inside a vibrant fantasy VRMMO meadow under bright sunlight, "
                "a nimble young male adventurer wearing a comical blue bird mask, bare chest, and simple dark shorts "
                "dual-wielding curved iron daggers while executing a lightning-fast acrobat dodge around a giant charging horned monster, "
                "dynamic motion streaks, glowing VR HUD interface elements, 4K rendering."
            )
        },
        {
            "index": 2, "range": (11, 20),
            "title": ["NIGHTSLAYER ENCOUNTER", "THE CURSE OF LYCAGON"],
            "fallback_color": (15, 15, 25),
            "prompt": (
                "Cinematic dark fantasy night battle inside a foggy clearing under a blood-red moon, "
                "a colossal pitch-black shadow wolf with four glowing crimson eyes and living dark mist fur towering over "
                "the bird-masked dual-wielding fighter standing defenseless, dark cursed energy marks branding his torso, "
                "dramatic volumetric fog, chiaroscuro lighting, epic scale."
            )
        },
        {
            "index": 3, "range": (21, 30),
            "title": ["KINGDOM OF RABITUZA", "VORPAL BLADE TRAINING"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic fantasy scene inside an underground cavernous kingdom of stone warrens, "
                "a cute white rabbit girl in a miniature magician coat and top hat standing beside the bird-masked protagonist, "
                "facing a massive scar-faced bipedal rabbit blacksmith hammering a glowing red vorpal cleaver over an anvil, "
                "warm forge embers, detailed dust motes, whimsical yet gritty atmosphere."
            )
        },
        {
            "index": 4, "range": (31, 40),
            "title": ["POISONOUS SWAMPS", "CLASH OF THE OUTLAWS"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "Cinematic atmospheric scene inside a murky twilight swamp with twisted glowing toxic flora, "
                "the bird-masked dual-blade mercenary sprinting across sinking mossy logs, evading giant serpentine predators "
                "alongside an armored player party armed with heavy halberds, neon purple water reflections, high-detail dynamic action."
            )
        },
        {
            "index": 5, "range": (41, 50),
            "title": ["GATHERING OF TRASH-GAMERS", "ASHURA-KAI STANDOFF"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic wide angle showdown in an ancient ruined arena of crumbling stone pillars at sunset, "
                "the shirtless bird-mask fighter flanked by a tall silver-haired female spear warrior and a monk-like brawler, "
                "facing off against a notorious guild of heavily armed red-named player killers, dramatic sunset lens flare, 4K composition."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
