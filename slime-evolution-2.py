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

def purge_corrupt_cache(build_dir: str):
    """Purges placeholder dummy files from earlier connection dropouts."""
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
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
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

BUILD_DIR = "build_slime_evolution_51_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Source & Range Parameters
    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/slime-evolution/chapter-51",
    "novel_slug": "slime-evolution",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Slime Evolution",

    # Concurrency Settings & Hardcoded Narrator Lock
    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Mir-Style Dynamic Intro Sequence Passed in intro_hook (Chapters 51 to 100)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "From the lowly depths of the food chain to the pinnacle of apex predators, "
                "the devouring creature knows neither mercy nor limits. "
                "Witness the relentless cycle of consumption, skill acquisition, and body mutation, "
                "as a solitary slime evolves into an unstoppable calamity."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "gong",
            "bgm_mood": "wonder"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.4,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "wonder"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "We are thrilled to bring you chapters fifty-one through one hundred of Slime Evolution. "
                "Take a moment to hit that like button, subscribe if you are new to the channel, "
                "and drop your thoughts in the comments below. Your support is the engine that keeps these grand marathons alive. "
                "Adjust your volume, brace for the next tier of evolution, and let us descend."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_lead_in_pause",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 1.0,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_slime_evolution_51_100.mp3",
    "final_video": "final_slime_evolution_51_100.mp4",
    "cover_image": "cover_slime_evolution_51_100.jpg",
    "timestamps_file": "youtube_timestamps_slime_evolution_51_100.txt",
    "subtitles_file": "subtitles_slime_evolution_51_100.srt",
    "payload_file": "youtube_upload_payload_slime_evolution_51_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEVOURING MONSTERS & INFINITE SPECIES MUTATION! [Chapters 51-100] | Slime Evolution Full Audiobook",
    "tags": [
        "Slime Evolution", "Monster Evolution", "LitRPG Audiobook", "Devour System",
        "Dungeon Crawler", "Web Novel Audio", "Isekai Monster", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to the continuous evolution marathon of 'Slime Evolution', covering Chapters 51 through 100!\n\n"
        "Experience the next tier of biological warfare and dungeon domination: devouring higher-tier mutant beasts, unlocking rare "
        "elemental immunities, and mutating into terrifying apex evolutionary stages. Follow our monster protagonist through deadly cavern "
        "ambushes and boss encounters with multi-voice neural TTS, context-aware acoustic soundscapes, and synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more monster evolution and LitRPG sagas!\n\n"
        "#SlimeEvolution #MonsterEvolution #LitRPG #DungeonAudiobook #WebNovel #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Chapters 51 to 100: 51-63, 64-75, 76-88, 89-100)
    "blocks": [
        {
            "index": 1, "range": (51, 63),
            "title": ["SUBTERRANEAN HUNT", "THE ACIDIC DEVOURER"],
            "fallback_color": (15, 30, 25),
            "prompt": (
                "Cinematic 3D dark fantasy illustration inside a vast bioluminescent underground cavern, "
                "a colossal mutated translucent gelatinous slime entity glowing with corrosive emerald acidic energy, "
                "dissolving the armored carapace of a giant scorpion beast, glowing phosphorescent moss on rock ceilings, "
                "dramatic eerie lighting, highly detailed 4k digital masterpiece."
            )
        },
        {
            "index": 2, "range": (64, 75),
            "title": ["SYSTEM NOTIFICATIONS", "SKILL SYNTHESIS"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D LitRPG scene of a dungeon cavern bathed in blue magical interface light, "
                "holographic status panels floating in air showing skill evolution trees, "
                "the slime core pulsing with golden lightning as new genetic traits synthesize, "
                "intricate particle effects and reflections on wet cavern stones, sharp 4k render."
            )
        },
        {
            "index": 3, "range": (76, 88),
            "title": ["CLASH WITH THE FLOOR BOSS", "CORROSIVE AURA"],
            "fallback_color": (35, 15, 20),
            "prompt": (
                "Cinematic 3D action scene in a ruined subterranean amphitheater, "
                "a massive armored minotaur boss swinging an iron greataxe against an amorphous shape-shifting predator, "
                "acid tendrils whipping through the air sizzling against stone pillars, dynamic motion blur, "
                "hyper-detailed 4k digital art."
            )
        },
        {
            "index": 4, "range": (89, 100),
            "title": ["TIER BREAKTHROUGH", "THE CALAMITY AWAKENS"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D epic establishing view of the cavern floor illuminated by an explosive pillar of violet evolutionary energy, "
                "the evolved apex entity taking a terrifying multi-limbed crystalline form, "
                "cavern roof trembling with falling stalactites, supreme monstrous majesty, 4k digital masterpiece."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))