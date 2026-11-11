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

BUILD_DIR = "build_vampire_bat_401_450"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/game-descends-from-vampire-bat-to-loli-tyrant/chapter-401-kaje-star/",
    "novel_slug": "vampire-bat-tyrant",
    "start_chapter": 401,
    "end_chapter": 450,
    "default_topic": "From Vampire Bat to Loli Tyrant: Kaje Star & The Star Abyss Hunt",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate 5-Beat Intro Hook for Chapter 401
    "intro_hook": [
        # Beat 1: High-Stakes Teaser
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "authoritative_low",
            "lung_reset": False,
            "rate": "-3%",
            "pause_duration": 0.5,
            "display_text": '"What if it exceeds Emperor-tier?" Standing before the Interstellar Guild\'s strength tester, a silver-haired tyrant places her palm on the sensor—shattering the device into smoking electric debris as she claims an A-tier bounty to hunt the legendary Star Abyss Giant Worm!',
            "tts_text": '"What if it exceeds Emperor tier?" Standing before the Interstellar Guild\'s strength tester... a silver-haired tyrant places her palm on the sensor... shattering the massive device into smoking electric debris... as she claims an A-tier bounty to hunt the legendary Star Abyss Giant Worm!',
            "text": '"What if it exceeds Emperor-tier?" Standing before the Interstellar Guild\'s strength tester, a silver-haired tyrant places her palm on the sensor—shattering the device into smoking electric debris as she claims an A-tier bounty to hunt the legendary Star Abyss Giant Worm!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "explosion",
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
        # Beat 2: Trademark Channel Signature
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
        # Beat 3: In-Universe Call to Action
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Hunter Protocol: To fuel today's massive interstellar release and claim your Star Coins, hit that Like button and subscribe to the channel. Tearing through the void and hunting cosmic horrors requires supreme firepower.",
            "tts_text": "Hunter Protocol: To fuel today's massive interstellar release and claim your Star Coins, hit that Like button and subscribe to the channel. Tearing through the void and hunting cosmic horrors requires supreme firepower.",
            "text": "Hunter Protocol: To fuel today's massive interstellar release and claim your Star Coins, hit that Like button and subscribe to the channel. Tearing through the void and hunting cosmic horrors requires supreme firepower.",
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
        # Beat 4: Recap Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "-2%",
            "pause_duration": 0.4,
            "display_text": "From humble beginnings as a subterranean vampire bat to an evolved tyrant defying the galaxy, Ink Dance has reached the stars. Now, entering Chapters 401 through 450, spatial rifts tear open over Charon Star as interstellar hunts commence. Prepare yourselves, and let the cosmic hunt begin.",
            "tts_text": "From humble beginnings as a subterranean vampire bat to an evolved tyrant defying the galaxy... Ink Dance has reached the stars. Now, entering Chapters 401 through 450, spatial rifts tear open over Kair-on Star as interstellar hunts commence. Prepare yourselves, and let the cosmic hunt begin.",
            "text": "From humble beginnings as a subterranean vampire bat to an evolved tyrant defying the galaxy, Ink Dance has reached the stars. Now, entering Chapters 401 through 450, spatial rifts tear open over Charon Star as interstellar hunts commence. Prepare yourselves, and let the cosmic hunt begin.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "triumph"
        },
        # Beat 5: Lead-In Silence
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
    "final_audio": "output_vampire_bat_401_450.mp3",
    "final_video": "final_vampire_bat_401_450.mp4",
    "cover_image": "cover_vampire_bat_401_450.jpg",
    "timestamps_file": "youtube_timestamps_vampire_bat_401_450.txt",
    "subtitles_file": "subtitles_vampire_bat_401_450.srt",
    "payload_file": "youtube_upload_payload_vampire_bat_401_450.json",

    # Clean Branding Overlay Configuration
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "FROM VAMPIRE BAT TO TYRANT: THE INTERSTELLAR HUNTER! [Chapters 401-450] | Sci-Fi LitRPG Audiobook",
    "tags": [
        "From Vampire Bat to Loli Tyrant", "Vampire Bat", "Evolution LitRPG",
        "Sci-Fi Cultivation", "Audiobook", "Being A Bong", "Progression Fantasy"
    ],
    "desc_header": (
        "Welcome to 'Game Descends: From Vampire Bat to Loli Tyrant', covering Chapters 401 through 450!\n\n"
        "Stepping onto Kaje Star, Ink Dance shatters the Interstellar Guild's evaluation apparatus with beyond-Emperor "
        "energy before accepting an A-tier hunt against the Star Abyss Giant Worm on Charon Star. "
        "Experience multi-voice narration, spatial sound design, and broadcast audio mastering.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#VampireBatToTyrant #EvolutionLitRPG #SciFiAudiobook #BeingABong #FantasyAudiobook"
    ),

    # 4 High-CTR Thematic Visual Blocks for Chapters 401 to 450
    "blocks": [
        {
            "index": 1,
            "range": (401, 412),
            "title": ["INTERSTELLAR HUNTER", "SHATTERING THE EMPEROR TESTER"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "A cinematic wide 16:9 panoramic key visual inside a futuristic, bustling Interstellar Guild hall on Kaje Star, "
                "designed with maximum visual contrast for high CTR. "
                "In the radiant center limelight stands Ink Dance—a petite, formidable silver-haired tyrant girl under 1.3 meters tall, "
                "with twitching fluffy beast ears, long waist-length silver hair, and a dark gothic sci-fi coat with glowing crimson trim. "
                "Her outstretched small hand rests upon a massive shattered capsule-pod strength tester that has exploded into jagged metallic shards, "
                "leaping electric blue arc currents, and thick billows of black smoke scorching the metallic floor. "
                "Standing behind her in support are Li Zihuang with cold glowing purple eyes and young Su Li looking on curiously. "
                "In the shocked background, alien mercenary hunters, cyborgs, and receptionist staff stare wide-eyed as a colossal hexagonal hologram "
                "screen displays the mission details for hunting the Star Abyss Giant Worm. "
                "Dynamic chiaroscuro lighting (electric blue sparks and red aura contrasting against sleek steel interiors), glistening metallic reflections, "
                "intricate cloth and cybernetic textures, photorealistic sci-fi concept art, Unreal Engine 5 render style, 8k resolution --ar 16:9 --style raw --v 6.1"
            )
        },
        {
            "index": 2,
            "range": (413, 425),
            "title": ["TEARING THE VOID", "SPATIAL RIFT OVER CHARON"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "An epic 16:9 grand cinematic sci-fi action visual set on the high-tech spaceport launchpad overlooking a neon-lit alien metropolis. "
                "Center-stage in the limelight, Ink Dance raises her slender hand and easily rips open a pitch-black vertical dimensional rift in mid-air "
                "like tearing parchment, its jagged edges shimmering with brilliant silver and violet spatial law energy. "
                "Through the spatial tear, the desolate, crater-pocked crimson surface of Charon Star and distant swirling cosmic nebulae are revealed. "
                "Behind her, sleek silver-white interstellar dreadnoughts and guild flying boats hover above the launch bays under twin alien moons. "
                "Volumetric lighting streaming from the spatial anomaly, floating energy motes, photorealistic textures of polished titanium and void energy, "
                "trending on ArtStation, cinematic composition, sharp focus, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (426, 437),
            "title": ["STAR ABYSS GIANT WORM", "LEGENDARY BEAST HUNT"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "A dramatic wide 16:9 cosmic monster combat scene set on the stormy, obsidian-crag surface of Charon Star. "
                "In the intense foreground limelight, Ink Dance hovers airborne, surrounded by thousands of ethereal, crimson vampire bat phantoms "
                "and swirling void claws, directing a devastating storm of blood-red energy beams toward a titanic monster. "
                "Erupting from the cracked planetary crust is the Star Abyss Giant Worm—a colossal, ancient subterranean leviathan covered in "
                "armored chitin plates, glowing acid glands, and a cavernous maw lined with spiral rows of diamond-hard fangs. "
                "Li Zihuang unleashes purple kinetic shockwaves from the ridge, while cosmic lightning arcs across the dark sky. "
                "Dramatic rim lighting from planetary aurora, flying rock debris, photorealistic chitin and energy beam textures, "
                "masterwork sci-fi dark fantasy digital art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (438, 450),
            "title": ["COSMIC DOMINION", "ASCENT OF THE LOLI TYRANT"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "A breathtaking 16:9 climactic space visual of Ink Dance standing victorious atop a fractured asteroid ridge overlooking a vast cosmic battlefield. "
                "Her long silver hair and dark coat billow in the vacuum as massive ethereal vampire wings woven from pure celestial blood-light spread wide behind her. "
                "A translucent, intricate galaxy-class status interface floats beside her, detailing her ascended tyrant bloodline and 50 million Star Coin bounty rewards. "
                "In the cosmic background, distant starships cruise past glowing planetary rings and colorful spiral galaxies under radiant starlight. "
                "Stunning panoramic scale, deep volumetric contrast, photorealistic celestial reflections, cinematic matte painting, "
                "octane render, Unreal Engine 5 showcase, 8k resolution --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
