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

BUILD_DIR = "build_slime_evolution_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/slime-evolution/chapter-101",
    "novel_slug": "slime-evolution",
    "start_chapter": 101,
    "end_chapter": 150,
    "default_topic": "Slime Evolution: From Small Slime to Mythic Devourer",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate Universal 5-Beat Intro Hook for Chapter 101 (Lohan, Parallel Processing, Elite Beetle Shatter)
    "intro_hook": [
        # Beat 1: High-Stakes Teaser (0:00 - 0:12)
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": '"Now... let\'s test what so many evolutions have brought me!" Ascending into the fossilized tree\'s third floor, Lohan activates his Parallel Processing Core—splitting his consciousness into multiple autonomous combat tracks as ice spikes shatter metallic armor and raw mana recharges his core in real time!',
            "tts_text": '"Now... let us test what so many evolutions have brought me!" Ascending into the fossilized tree\'s third floor, Lohan activates his Parallel Processing Core... splitting his consciousness into multiple autonomous combat tracks as ice spikes shatter metallic armor, and raw mah-nuh recharges his core in real time!',
            "text": '"Now... let\'s test what so many evolutions have brought me!" Ascending into the fossilized tree\'s third floor, Lohan activates his Parallel Processing Core—splitting his consciousness into multiple autonomous combat tracks as ice spikes shatter metallic armor and raw mana recharges his core in real time!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "swish",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Neutral",
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
            "gender": "Neutral",
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
            "gender": "Neutral",
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
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Mythic Evolution System Directive: To feed your biomass reserves for today's massive release, smash the Like button and subscribe to the channel. Digesting dungeon cores and evolving new genetic pathways is the only way to conquer the hive.",
            "tts_text": "Mythic Evolution System Directive: To feed your biomass reserves for today's massive release, smash the Like button and subscribe to the channel. Digesting dungeon cores and evolving new genetic pathways is the only way to conquer the hive.",
            "text": "Mythic Evolution System Directive: To feed your biomass reserves for today's massive release, smash the Like button and subscribe to the channel. Digesting dungeon cores and evolving new genetic pathways is the only way to conquer the hive.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Neutral",
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
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, Lohan adapted through brutal battles, forming a symbiotic bond with Lisa while harvesting exotic traits across the depths. Now, entering chapters 101 through 150 of Slime Evolution, they confront the Queen's elite vanguard in the upper canopies. Brace yourselves, and let the devourer's ascent begin.",
            "tts_text": "Previously, Lohan adapted through brutal battles, forming a symbiotic bond with Lisa while harvesting exotic traits across the depths. Now, entering chapters 101 through 150 of Slime Evolution, they confront the Queen's elite vanguard in the upper canopies. Brace yourselves... and let the devourer's ascent begin.",
            "text": "Previously, Lohan adapted through brutal battles, forming a symbiotic bond with Lisa while harvesting exotic traits across the depths. Now, entering chapters 101 through 150 of Slime Evolution, they confront the Queen's elite vanguard in the upper canopies. Brace yourselves, and let the devourer's ascent begin.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "triumph"
        },

        # Beat 5: Post-Intro Scene SFX & Transition Silence (0:40 - 0:42)
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Neutral",
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
            "gender": "Neutral",
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

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_slime_evolution_101_150.mp3",
    "final_video": "final_slime_evolution_101_150.mp4",
    "cover_image": "cover_slime_evolution_101_150.jpg",
    "timestamps_file": "youtube_timestamps_slime_evolution_101_150.txt",
    "subtitles_file": "subtitles_slime_evolution_101_150.srt",
    "payload_file": "youtube_upload_payload_slime_evolution_101_150.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MYTHIC SLIME EVOLUTION & PARALLEL PROCESSING! [Chapters 101-150] | LitRPG Full Audiobook",
    "tags": [
        "Slime Evolution", "Monster Evolution", "LitRPG Audiobook", "Dungeon Crawler",
        "Parallel Processing", "Isekai Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Slime Evolution', covering Chapters 101 through 150!\n\n"
        "Pushing into the third floor of the ancient fossilized dungeon tree, Lohan unlocks the game-changing "
        "Parallel Processing Core, eliminating latency between his main slime body and combat clones. As giant elite "
        "beetles and biological puppet horrors assault the wounded spirit fox Lisa, witness an unstoppable cycle of "
        "ice spike bombardment, living armor hardening, and real-time mana core harvesting.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#SlimeEvolution #MonsterEvolution #LitRPG #Audiobook #BeingABong #FantasyAudiobook"
    ),

    # Visual Prompts (4 Balanced Thematic Blocks covering Chapters 101 to 150)
    "blocks": [
        {
            "index": 1, "range": (101, 112),
            "title": ["PARALLEL PROCESSING", "THE THIRD FLOOR"],
            "fallback_color": (15, 25, 40),
            "prompt": (
                "Cinematic 3D fantasy illustration of an iridescent translucent blue slime splitting into multiple autonomous clones, "
                "firing crystallized ice spikes at massive glowing metallic rhinoceros beetles inside a cavernous fossilized tree hollow, "
                "a wounded white spirit fox with nine-tail potential fighting alongside it, glowing blue mana trails, volumetric dungeon lighting, "
                "octane render, unreal engine 5 style, hyper-detailed 4k digital art."
            )
        },
        {
            "index": 2, "range": (113, 125),
            "title": ["HIVE QUEEN OBSIDIAN", "LIVING ARMOR"],
            "fallback_color": (35, 15, 25),
            "prompt": (
                "Cinematic 3D fantasy scene of a slime creature forming obsidian living armor over a fierce white fox, "
                "confronting a towering swarm of armored insectoid warriors hanging from glowing silk cocoons, "
                "deep subterranean cave, pulsating purple bioluminescence, dynamic motion blur, high contrast 4k."
            )
        },
        {
            "index": 3, "range": (126, 137),
            "title": ["MANA CORE EXTRACTION", "BIOMASS HARVEST"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "Cinematic 3D dark fantasy depiction of a mythic slime organism extracting radiant glowing mana stones "
                "from defeated armored carapace beasts, intricate glowing magic circle runes, blue tentacles weaving defensive barriers, "
                "atmospheric fog, sharp rim lighting, masterpiece digital render."
            )
        },
        {
            "index": 4, "range": (138, 150),
            "title": ["MYTHIC DEVOURER", "CONQUEST OF THE DUNGEON"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D epic climax shot of a massive ascended slime entity and an empowered blazing spirit fox standing victorious "
                "at the apex of an ancient hollow world-tree, overlooking a sprawling mystical fantasy landscape through the cracked canopy, "
                "golden hour sunbeams, sparkling mana dust, photorealistic textures, masterpiece 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
