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

def purge_corrupt_cache(build_dir: str):
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
                if len(rows) < 8 or any("Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", "")) for r in rows):
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_vampire_bat_to_loli_tyrant_351_400"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/game-descends-from-vampire-bat-to-loli-tyrant/chapter-351/",
    "novel_slug": "game-descends-from-vampire-bat-to-loli-tyrant",
    "start_chapter": 351,
    "end_chapter": 400,
    "default_topic": "Game: Descends From Vampire Bat To Loli Tyrant",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

     "intro_hook": [
        # Beat 1: High-Stakes Teaser (0:00 - 0:12)
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "\"If you are not going to act, then get lost! The Apocalypse Empire does not welcome you.\" Facing the golden phantom of a Third-rank Martial Saint, Ink Dance unleashes twelve dragon wings across the void, fusing ancient dragon marrow before sealing herself in an immortal seven-day blood cocoon!",
            "tts_text": "\"If you are not going to act, then get lost! The Apocalypse Empire does not welcome you.\" Facing the golden phantom of a Third-rank Martial Saint, Ink Dance unleashes twelve dragon wings across the void, fusing ancient dragon marrow before sealing herself in an immortal seven-day blood cocoon!",
            "text": "\"If you are not going to act, then get lost! The Apocalypse Empire does not welcome you.\" Facing the golden phantom of a Third-rank Martial Saint, Ink Dance unleashes twelve dragon wings across the void, fusing ancient dragon marrow before sealing herself in an immortal seven-day blood cocoon!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "monster",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 2: Trademark Channel Signature (0:12 - 0:17)
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "engaged_alert",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "whoosh",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 3: In-Universe Lore-Bound CTA (0:17 - 0:27)
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Apocalypse Directive: To empower the Emperor's gene fusion and unlock chapter 351, strike the Like button and subscribe to the channel. Maintaining the Spirit-Forbidden Array protects the Night Capital from Central Continent retaliation.",
            "tts_text": "Apocalypse Directive: To empower the Emperor's gene fusion and unlock chapter 351, strike the Like button and subscribe to the channel. Maintaining the Spirit-Forbidden Array protects the Night Capital from Central Continent retaliation.",
            "text": "Apocalypse Directive: To empower the Emperor's gene fusion and unlock chapter 351, strike the Like button and subscribe to the channel. Maintaining the Spirit-Forbidden Array protects the Night Capital from Central Continent retaliation.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 4: Recap Bridge (0:27 - 0:40)
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, Ink Dance crushed hostile invaders and consolidated her dark empire. Now, covering chapters 351 through 400 of Game: Descends From Vampire Bat To Loli Tyrant, the Saint Lord of the Taixu Holy Dynasty retreats in humiliation while our tyrant enters a profound metamorphosis. Let us descend.",
            "tts_text": "Previously, Ink Dance crushed hostile invaders and consolidated her dark empire. Now, covering chapters 351 through 400 of Game: Descends From Vampire Bat To Loli Tyrant, the Saint Lord of the Taixu Holy Dynasty retreats in humiliation while our tyrant enters a profound metamorphosis. Let us descend.",
            "text": "Previously, Ink Dance crushed hostile invaders and consolidated her dark empire. Now, covering chapters 351 through 400 of Game: Descends From Vampire Bat To Loli Tyrant, Saint Lord of the Taixu Holy Dynasty retreats in humiliation while our tyrant enters a profound metamorphosis. Let us descend.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "triumph"
        },
        # Beat 5: Post-Intro Scene SFX & Transition Silence (0:40 - 0:42)
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.2,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "wind",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 1.0,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    "build_dir": BUILD_DIR,
    "final_audio": "output_vampire_bat_to_loli_tyrant_351_400.mp3",
    "final_video": "final_vampire_bat_to_loli_tyrant_351_400.mp4",
    "cover_image": "cover_vampire_bat_to_loli_tyrant_351_400.jpg",
    "timestamps_file": "youtube_timestamps_vampire_bat_to_loli_tyrant_351_400.txt",
    "subtitles_file": "subtitles_vampire_bat_to_loli_tyrant_351_400.srt",
    "payload_file": "youtube_upload_payload_vampire_bat_to_loli_tyrant_351_400.json",

    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    "video_title": "ABYSSAL MONARCH & LOLI TYRANT DOMINION! [Chapters 351-400] | LitRPG Full Audiobook",
    "tags": [
        "Game Descends From Vampire Bat To Loli Tyrant", "LitRPG Audiobook", "System Evolution",
        "Monster Evolution", "Web Novel Audiobook", "Gamer Audio", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Game: Descends From Vampire Bat To Loli Tyrant', covering Chapters 351 through 400!\n\n"
        "Witness the terrifying ascent of the loli tyrant as system rules shatter, divine evolution peaks, and hostile empires "
        "bow before supreme dark dominion. Experience this 50-chapter epic arc with multi-voice neural TTS, "
        "context-aware acoustic soundscapes, voice-aware prosody scaling, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#VampireBatToLoliTyrant #LitRPG #MonsterEvolution #GameDescends #Audiobook #BeingABong"
    ),

    "blocks": [
        {
            "index": 1, "range": (351, 362),
            "title": ["ABYSSAL AWAKENING", "THE TYRANT'S DOMAIN"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a powerful loli tyrant with crimson eyes and elegant gothic attire "
                "standing atop a obsidian throne in a shadowy subterranean palace, glowing magic interface screens floating around her, "
                "atmospheric fog, dramatic moody lighting, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (363, 375),
            "title": ["DUNGEON CONQUEST", "SYSTEM RULES SHATTERED"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D action fantasy scene of a massive subterranean dungeon battle against monstrous bosses, "
                "blazing dark-purple magic skills and digital system notifications flashing across the stone corridors, "
                "dynamic composition, high contrast ray-tracing, 4k."
            )
        },
        {
            "index": 3, "range": (376, 387),
            "title": ["GUILD EXPEDITION", "ABYSSAL MONARCH'S WRATH"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D epic fantasy illustration of armored hostile guild armies overwhelmed by dark abyssal bats and shadow beasts "
                "led by an imperious young tyrant floating above the battlefield, grand scale, volumetric lighting, masterpiece 4k."
            )
        },
        {
            "index": 4, "range": (388, 400),
            "title": ["SUPREME DOMINION", "THE ETERNAL THRONE"],
            "fallback_color": (20, 15, 25),
            "prompt": (
                "Cinematic 3D grandiose establishing shot of a vast dark empire stretching across a mystical fantasy continent under a blood-red moon, "
                "gothic towers and shadowy legions bowing in unison, majestic scenery, hyper-detailed cinematic render 4k."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
