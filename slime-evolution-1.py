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

BUILD_DIR = "build_slime_evolution_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "slime-evolution",
    "start_url": "https://freewebnovel.com/novel/slime-evolution/chapter-1",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Slime Evolution",

    # Concurrency Settings & Narrator Lock
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook (Premiere Episode)
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In a world where monsters are ranked by their lethal instincts and bloodline hierarchy, "
                "reincarnating as a lowly, translucent slime is widely regarded as a death sentence. "
                "Yet beneath this squishy, fragile exterior lies a limitless devour-and-assimilate evolutionary tree. "
                "By consuming deadly venom, elemental crystals, and slain dungeon predators, one overlooked creature begins "
                "a terrifying ascent to become the apex sovereign of the abyss."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "splash",
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
                "We are thrilled to bring you the premiere episode of this monster evolution fantasy saga, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the evolutionary core absorbs its first prey, adjust your volume, and let's begin today's episode."
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
    "final_audio": "output_slime_evolution_1_50.mp3",
    "final_video": "final_slime_evolution_1_50.mp4",
    "cover_image": "cover_slime_evolution_1_50.jpg",
    "timestamps_file": "youtube_timestamps_slime_evolution_1_50.txt",
    "subtitles_file": "subtitles_slime_evolution_1_50.srt",
    "payload_file": "youtube_upload_payload_slime_evolution_1_50.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DEVOURING MONSTERS & APEX EVOLUTION! [Ch 1-50] | Slime Evolution LitRPG Full Audiobook",
    "tags": [
        "Slime Evolution", "Monster Evolution", "LitRPG Audiobook", "Progression Fantasy",
        "Evolutionary Tree", "Dungeon Crawler", "Reincarnation", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere release of 'Slime Evolution' covering Chapters 1 through 50!\n\n"
        "Reborn into a dark fantasy cavern as the weakest possible monster, our protagonist discovers that his slime body "
        "has no evolutionary ceiling. By absorbing toxic flora, crystalline mana veins, and deadly dungeon predators, he unlocks "
        "unprecedented elemental forms, acidic mutations, and psychic mimicry skills. Experience this 50-chapter premiere marathon "
        "with multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, skill mutations, and evolutionary prompts).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and monster evolution sagas!\n\n"
        "#SlimeEvolution #MonsterEvolution #LitRPG #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 balanced thematic blocks across Ch 1 to 50: 1-12, 13-25, 26-38, 39-50)
    "blocks": [
        {
            "index": 1, "range": (1, 12),
            "title": ["CAVERN AWAKENING", "THE WEAKEST SLIME"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D fantasy illustration of a small, glowing azure translucent slime resting on a mossy cavern rock, "
                "pulsing with a gentle inner light while absorbing a glowing poisonous mushroom. "
                "Jagged stalactites, dripping water pools reflecting bioluminescent cave fungi, atmospheric cyan glow, 4k digital art."
            )
        },
        {
            "index": 2, "range": (13, 25),
            "title": ["PREDATOR DEVOURMENT", "ACIDIC MUTATION"],
            "fallback_color": (20, 35, 25),
            "prompt": (
                "Cinematic 3D dark fantasy action scene in a subterranean grotto, showing the evolved larger gelatinous slime "
                "engulfing a defeated giant fanged cave spider with corrosive acidic tendrils and emerald energy sparks. "
                "Cracked limestone floor, swirling mist, dramatic low-angle lighting, photorealistic liquid physics."
            )
        },
        {
            "index": 3, "range": (26, 38),
            "title": ["ELEMENTAL CRYSTALLIZATION", "CORROSIVE SOVEREIGN"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D render of an advanced crystal-armored slime creature surrounded by floating violet mana crystals, "
                "forming sharp spike appendages and an ominous glowing crimson core inside its dark translucent body. "
                "Ancient stone ruins background, volumetric cave lighting, dynamic particle effects, sharp 4k render."
            )
        },
        {
            "index": 4, "range": (39, 50),
            "title": ["APEX HORROR ASCENT", "RULER OF THE ABYSS"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D epic fantasy view of a towering, multi-faceted slime sovereign dominating a grand cavern throne hall, "
                "lesser cave beasts and goblins trembling around the perimeter while radiant prismatic aura wraps the massive translucent lord. "
                "Dramatic cavern illumination, majestic scale, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
