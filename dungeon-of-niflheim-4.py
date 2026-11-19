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
                if len(rows) < 8 or any(
                    "Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", ""))
                    for r in rows
                ):
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


BUILD_DIR = "build_dungeon_of_niflheim_106_140"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-of-niflheim/chapter-106",
    "novel_slug": "dungeon-of-niflheim",
    "start_chapter": 106,
    "end_chapter": 140,
    "is_start": False,
    "default_topic": "Dungeon of Niflheim: Frost's Ascension",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 106 to 140 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Luna)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Luna",
            "gender": "Female",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"His mana veins are overheated—he can\'t cast another third-circle spell! Strike now and shatter the ring on his left hand!"',
            "tts_text": '"His mana veins are overheated... he can\'t cast another third-circle spell! Strike now and shatter the ring on his left hand!"',
            "text": '"His mana veins are overheated—he can\'t cast another third-circle spell! Strike now and shatter the ring on his left hand!"',
            "voice": "en-US-AvaMultilingualNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
            "bgm_mood": "combat"
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
            "display_text": "Pushed to the brink outside his dungeon walls, Frost teams up with Leo and Luna in a brutal clash against the C-rank Baron Adam—enduring third-circle bombardment, shattering life-saving artifacts, and turning the tide before returning to expand the frozen realm of Niflheim!",
            "tts_text": "Pushed to the brink outside his dungeon walls, Frost teams up with Leo and Luna in a brutal clash against the C-rank Baron Adam... enduring third-circle bombardment, shattering life-saving artifacts, and turning the tide before returning to expand the frozen realm of Niflheim!",
            "text": "Pushed to the brink outside his dungeon walls, Frost teams up with Leo and Luna in a brutal clash against the C-rank Baron Adam—enduring third-circle bombardment, shattering life-saving artifacts, and turning the tide before returning to expand the frozen realm of Niflheim!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "combat"
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
            "display_text": "Niflheim Dungeon Decree: To harvest Dungeon Points and fuel this thirty-five-chapter marathon, hit that Like button and subscribe to the channel. In the frozen abyss, only the ruthless Dungeon Master commands destiny.",
            "tts_text": "Niflheim Dungeon Decree: To harvest Dungeon Points and fuel this thirty-five-chapter marathon, hit that Like button and subscribe to the channel. In the frozen abyss, only the ruthless Dungeon Master commands destiny.",
            "text": "Niflheim Dungeon Decree: To harvest Dungeon Points and fuel this thirty-five-chapter marathon, hit that Like button and subscribe to the channel. In the frozen abyss, only the ruthless Dungeon Master commands destiny.",
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
        # Beat 4: Continuation Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Your immersion resumes now, covering Chapter 106 through Chapter 140 of Dungeon of Niflheim. Channel your ice chakra, ready your glaive, and witness Frost's ruthless counterattack.",
            "tts_text": "Your immersion resumes now, covering Chapter 106 through Chapter 140 of Dungeon of Niflheim. Channel your ice chakra, ready your glaive, and witness Frost's ruthless counterattack.",
            "text": "Your immersion resumes now, covering Chapter 106 through Chapter 140 of Dungeon of Niflheim. Channel your ice chakra, ready your glaive, and witness Frost's ruthless counterattack.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "wonder"
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
            "sfx": "teleport",
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
    "final_audio": "output_dungeon_of_niflheim_106_140.mp3",
    "final_video": "final_dungeon_of_niflheim_106_140.mp4",
    "cover_image": "cover_dungeon_of_niflheim_106_140.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_of_niflheim_106_140.txt",
    "subtitles_file": "subtitles_dungeon_of_niflheim_106_140.srt",
    "payload_file": "youtube_upload_payload_dungeon_of_niflheim_106_140.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUNGEON OF NIFLHEIM! [Chapters 106-140] | Ice Dungeon Core LitRPG Progression Full Audiobook",
    "tags": [
        "Dungeon of Niflheim", "Dungeon of Niflheim Audiobook", "Frost", "Dungeon Core LitRPG",
        "Ice Magic Progression", "Fantasy Audiobook", "Monster Evolution", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dungeon of Niflheim', covering Chapters 106 through 140!\n\n"
        "Battered by C-rank Baron Adam's devastating third-circle spell, Frost rallies alongside Leo and Luna to exploit "
        "Adam's overheated mana veins—shattering his defenses, surviving life-saving magic barriers, and returning to Niflheim "
        "to spend hard-earned Dungeon Points on deadly new floors, monster evolutions, and winter defenses!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and dungeon system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DUNGEON CORE & LITRPG MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DungeonOfNiflheim #DungeonCore #LitRPG #ProgressionFantasy #IceMagic #BeingABong"
    ),

    # 10 Textless 2D/2.5D Frozen Dungeon & Ice-Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (106, 109),
            "fallback_color": (16, 24, 38),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy battle book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of silver-haired elf-eared warrior Frost wielding a gleaming ice-infused glaive in tattered leather armor, "
                "leaping forward beside a young knight with a fire-enchanted sword and a female mage casting healing light. "
                "UPPER-RIGHT BACKGROUND: Wounded C-rank noble mage Adam staggered amid scorched stone rubble and shattering translucent mana shields. "
                "High-contrast glacier-cyan, blazing-orange, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (110, 112),
            "fallback_color": (12, 22, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dungeon-core book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Frost standing inside the crystalline core sanctum of Niflheim, resting one hand on a levitating azure ice-crystal dungeon core "
                "while glowing translucent blue dungeon management menus and floor blueprints float in the frosty air. "
                "UPPER-RIGHT & BACKGROUND: Towering subterranean ice pillars, frozen waterfalls, and glowing frost runes etched into dark basalt. "
                "High-contrast frost-cyan, royal-sapphire, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (113, 116),
            "fallback_color": (14, 26, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital monster-evolution book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Frost channeling swirling glacial mist and silver-blue chakra into a roaring frost-armored polar bear monster, "
                "crystalline ice plates forming across its massive shoulders. "
                "UPPER-RIGHT & BACKGROUND: Cavernous snow-covered dungeon floor with glowing summoning circles and drifting ice crystals. "
                "High-contrast ice-blue, silver-white, and deep-teal palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (117, 119),
            "fallback_color": (20, 18, 34),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Frost forging a new rune-inscribed glaive and frost-forged armor plates at an enchanted ice-and-steel anvil, "
                "blue-white spirit sparks flying across the frozen workshop. "
                "UPPER-RIGHT SKY: Vaulted crystalline cavern ceiling shimmering with aurora-like blue and violet mana currents. "
                "High-contrast electric-cyan, aurora-violet, and charcoal-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (120, 123),
            "fallback_color": (18, 24, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted glacial labyrinth book-cover illustration in top-ranking webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Mercenary adventurers cautiously advancing through a treacherous mirror-ice dungeon corridor, "
                "ambushed by skeletal frost warriors and razor-sharp icicle traps erupting from the frozen walls. "
                "UPPER-RIGHT & BACKGROUND: Shadowy silhouette of Frost watching from an upper crystal balcony overlooking the labyrinth. "
                "High-contrast glacier-blue, crimson-spark, and deep-navy palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (124, 126),
            "fallback_color": (14, 24, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted winter-frontier town book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Cloaked Frost walking along a snow-dusted stone street in a bustling northern guild town at dusk, "
                "inspecting rare magic cores and enchanted trinkets at a lantern-lit merchant stall. "
                "UPPER-RIGHT & BACKGROUND: Steep timber-and-stone medieval roofs covered in snow beneath a twilight sky. "
                "High-contrast warm-lantern amber, frost-blue, and slate-grey palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (127, 130),
            "fallback_color": (26, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted arcane training book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic elemental contrast, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Frost practicing rapid glaive katas on a frozen underground lake, each sweep leaving trailing crescents of razor-sharp frost and blue chakra lightning. "
                "UPPER-RIGHT HORIZON: Towering glacial cliffs and shimmering ice spires reflecting the elemental aura. "
                "High-contrast sapphire-cyan, silver-frost, and midnight-purple palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (131, 133),
            "fallback_color": (28, 14, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted dungeon-raid defense book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Frost leading his elite Niflheim dungeon monsters—dire ice wolves, frost giants, and armored bears—against an invading C-rank strike force. "
                "UPPER-RIGHT SKY: Blinding collision of crimson fireballs and towering walls of unbreakable glacial ice. "
                "High-contrast inferno-red, blinding-cyan, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (134, 137),
            "fallback_color": (14, 22, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyssal-glacier depths book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Frost descending into a newly unlocked deep sub-floor of Niflheim, surrounded by ancient frozen ruins and glowing rune-etched monoliths. "
                "UPPER-RIGHT & BACKGROUND: Vast subterranean chasm filled with drifting snow, bioluminescent ice crystals, and deep blue mist. "
                "High-contrast deep-azure, emerald-glow, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (138, 140),
            "fallback_color": (22, 26, 38),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Dungeon Master ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Sovereign Dungeon Master Frost standing atop a towering glacial throne spire inside Niflheim, "
                "glaive planted in the ice as swirling blizzards and glowing blue system panels crown his expanding frozen domain. "
                "UPPER-RIGHT HORIZON: Endless tiers of crystalline ice caverns, guardian beasts, and radiant aurora light. "
                "High-contrast celestial-cyan, silver-white, and royal-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
