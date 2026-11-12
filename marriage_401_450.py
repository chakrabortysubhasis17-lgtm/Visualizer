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

BUILD_DIR = "build_national_fate_elf_queen_401_450"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/national-fate-marriage-the-elf-queen-is-pregnant-at-the-start/chapter-401-there-are-some-small-fry-ahead-kill-our-way-through/",
    "novel_slug": "national-fate-elf-queen",
    "start_chapter": 401,
    "end_chapter": 450,
    "default_topic": "National Fate Marriage: The Elf Queen is Pregnant at the Start",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Standard 5-Beat Intro Hook with Split Character Dialogue & Narrative Teaser
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Confident Hero Voice)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Xiao Haoyan",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+1%",
            "pause_duration": 0.3,
            "display_text": '"There are some small fry ahead—stand back, and watch me kill our way straight through!"',
            "tts_text": '"There are some small fry ahead... stand back, and watch me kill our way straight through!"',
            "text": '"There are some small fry ahead—stand back, and watch me kill our way straight through!"',
            "voice": "en-US-EricNeural",
            "pitch": "+0Hz",
            "sfx": "whoosh",
            "bgm_mood": "tension"
        },
        # Beat 1b: Narrative Teaser Hook (Christopher Anchor)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "authoritative_low",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Shattering a hundred-fold gravity trap with a single stomp and carving a spatial vacuum through soul-corroding abyssal gas, Xiao Haoyan leads Diana and Yingwu deep into a forbidden labyrinth to confront the threat of Upper Gods!",
            "tts_text": "Shattering a hundred-fold gravity trap with a single stomp and carving a spatial vacuum through soul-corroding abyssal gas... Shyow How-yahn leads Diana and Ying-woo deep into a forbidden labyrinth... to confront the threat of Upper Gods!",
            "text": "Shattering a hundred-fold gravity trap with a single stomp and carving a spatial vacuum through soul-corroding abyssal gas, Xiao Haoyan leads Diana and Yingwu deep into a forbidden labyrinth to confront the threat of Upper Gods!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
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
        # Beat 2: Channel Trademark Signature
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
            "display_text": "National Fate Decree: To fortify your divine territory and support today's massive release, hit that Like button and subscribe to the channel. Surviving the hegemony of ten thousand races and protecting the Hanging Gardens demands absolute divine power.",
            "tts_text": "National Fate Decree: To fortify your divine territory and support today's massive release, hit that Like button and subscribe to the channel. Surviving the hegemony of ten thousand races and protecting the Hanging Gardens demands absolute divine power.",
            "text": "National Fate Decree: To fortify your divine territory and support today's massive release, hit that Like button and subscribe to the channel. Surviving the hegemony of ten thousand races and protecting the Hanging Gardens demands absolute divine power.",
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
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, Xiao Haoyan sealed a demon god in the Wilderness of Buried Bones and safeguarded his queens inside the Hanging Gardens. Now, entering Chapters 401 through 450 of National Fate Marriage, the expedition into the star-guided ruins begins. Steel your spirit, and let the conquest unfold.",
            "tts_text": "Previously, Shyow How-yahn sealed a demon god in the Wilderness of Buried Bones and safeguarded his queens inside the Hanging Gardens. Now, entering Chapters 401 through 450 of National Fate Marriage... the expedition into the star-guided ruins begins. Steel your spirit, and let the conquest unfold.",
            "text": "Previously, Xiao Haoyan sealed a demon god in the Wilderness of Buried Bones and safeguarded his queens inside the Hanging Gardens. Now, entering Chapters 401 through 450 of National Fate Marriage, the expedition into the star-guided ruins begins. Steel your spirit, and let the conquest unfold.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
        },
        # Beat 5: Transition SFX & Lead-in Silence
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
    "final_audio": "output_national_fate_elf_queen_401_450.mp3",
    "final_video": "final_national_fate_elf_queen_401_450.mp4",
    "cover_image": "cover_national_fate_elf_queen_401_450.jpg",
    "timestamps_file": "youtube_timestamps_national_fate_elf_queen_401_450.txt",
    "subtitles_file": "subtitles_national_fate_elf_queen_401_450.srt",
    "payload_file": "youtube_upload_payload_national_fate_elf_queen_401_450.json",

    # Clean Branding Overlay Configuration
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "NATIONAL FATE MARRIAGE: THE ELF QUEEN IS PREGNANT AT THE START! [Chapters 401-450] | Fantasy Audiobook",
    "tags": [
        "National Fate Marriage", "The Elf Queen is Pregnant at the Start", "Xiao Haoyan",
        "Fantasy Cultivation", "Kingdom Building", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'National Fate Marriage: The Elf Queen is Pregnant at the Start', covering Chapters 401 through 450!\n\n"
        "In a cruel world ruled by the hegemony of ten thousand races, Xiao Haoyan leaves the sanctuary of the Hanging Gardens "
        "with Diana and Yingwu, following the Star Gloves through lethal subterranean traps and Upper God domains to secure "
        "the absolute power needed to protect his family and empire.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#NationalFate #ElfQueen #FantasyAudiobook #KingdomBuilding #BeingABong #Audiobook"
    ),

    # 4 High-CTR Thematic Visual Blocks for Chapters 401 to 450
    "blocks": [
        {
            "index": 1,
            "range": (401, 412),
            "title": ["LAWS OF SPACE & SHADOW", "THE ABYSSAL LABYRINTH"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "A cinematic wide 16:9 panoramic key visual inside a vast, mossy subterranean stone corridor shrouded in eerie light-purple "
                "Abyss Corrosive Poisonous Gas, designed with maximum visual contrast for high CTR. "
                "In the sharp radiant center limelight stands the hero, Xiao Haoyan—a commanding, handsome sovereign in ornate dark-and-gold celestial battle robes, "
                "wearing glowing blue Star Gloves that project a dark-pink directional light arrow, tearing the void with his right hand to create a crystal-clear "
                "spatial vacuum corridor while shattering a glowing underground gravity formation beneath his boots. "
                "Flanking him in equal limelight are Diana, radiating a golden-white screen of Light Divine Power, and Yingwu, a sleek shadow assassin "
                "with glowing purple eyes emerging from swirling black mist with a pitch-black dagger. "
                "Blocking the corridor ahead are dozens of armored undead scouts wielding bone spears with eerie green soul fires burning in their eye sockets. "
                "Dynamic chiaroscuro lighting (golden divine light and electric spatial rifts contrasting against violet poison mist and bioluminescent moss), "
                "intricate stone and silk textures, Unreal Engine 5 render style, 8k resolution --ar 16:9 --style raw --v 6.1"
            )
        },
        {
            "index": 2,
            "range": (413, 425),
            "title": ["ABSOLUTE ZERO", "SHATTERING THE FROZEN SEAL"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "An epic 16:9 grand cinematic elemental clash visual inside a colossal subterranean glacial chamber lined with ancient celestial runes. "
                "Center-stage in an intense spotlight, Xiao Haoyan unleashes a roaring ocean of golden, silver, and cyan divine power from his outstretched palms, "
                "forming a towering multi-layered sealing mandala that shatters walls of crystalline Absolute Zero frost into glittering diamond shards. "
                "Beside him, Diana channels sacred solar beams across the frozen cavern floor while shadow tendrils dart through the flying ice mist. "
                "Towering frost monoliths and ancient frozen war constructs crumble in the perimeter under the overwhelming pressure of divine laws. "
                "Volumetric ice reflections, dramatic rim lighting, photorealistic crystal refraction and energy particles, "
                "cinematic composition, sharp focus, 8k digital art --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (426, 437),
            "title": ["THE HANGING GARDENS", "QUEENS OF TEN THOUSAND RACES"],
            "fallback_color": (20, 30, 20),
            "prompt": (
                "A breathtaking wide 16:9 high-fantasy sanctuary visual set along the bluestone paths of the celestial Hanging Gardens beside the luminous Spring of Life. "
                "In the radiant limelight stand the queens of Xiao Haoyan's domain: Elf Queen Liuzhi in flowing emerald silk tending a glowing ten-thousand-year-old "
                "blood ginseng, Fiya with magnificent radiant golden angel wings refracting the Law of Light over crystal waters, Yun Shu holding an ornate folding fan "
                "beside floating ancient scriptures, and Medusa resting gracefully on a carved marble pavilion chair with mesmerizing serpent eyes. "
                "Surrounding the floating sky gardens are luminescent spiritual herbs, cascading waterfalls, and golden clouds drifting across a serene twilight sky. "
                "Rich bioluminescent botanical colors, delicate silk and feather textures, masterwork digital concept art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (438, 450),
            "title": ["UPPER GOD HEGEMONY", "ASCENSION OF THE SOVEREIGN"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "A monumental 16:9 climactic cosmic battle visual set atop a fractured dimensional sky-altar overlooking the battlefield of ten thousand races. "
                "Center-stage in an authoritative spotlight, Xiao Haoyan ascends surrounded by swirling rings of Space, Light, and Shadow Laws, "
                "wielding a blinding celestial formation to suppress a colossal, shadow-cloaked Upper God titan descending from a tear in the heavens. "
                "Golden lightning arcs and silver spatial fractures illuminate the stormy sky as divine shockwaves ripple across ancient floating ruins. "
                "High dynamic range, dramatic chiaroscuro lighting, photorealistic celestial energy and armor textures, "
                "cinematic matte painting, Unreal Engine 5 showcase, 8k resolution --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
