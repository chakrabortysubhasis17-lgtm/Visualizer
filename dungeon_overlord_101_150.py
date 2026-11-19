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


BUILD_DIR = "build_dungeon_overlord_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-overlord-monster-girl-harem/chapter-101",
    "novel_slug": "dungeon-overlord-monster-girl-harem",
    "start_chapter": 101,
    "end_chapter": 150,
    "is_start": False,
    "default_topic": "Dungeon Overlord: Monster Girl Harem",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 101 to 150 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Leonhardt)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Leonhardt",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"Hold on to my voice, Sylvie—no matter how fierce the frost turns, I will channel every ounce of my flame until your bloodline awakens!"',
            "tts_text": '"Hold on to my voice, Sylvie... no matter how fierce the frost turns, I will channel every ounce of my flame until your bloodline awakens!"',
            "text": '"Hold on to my voice, Sylvie—no matter how fierce the frost turns, I will channel every ounce of my flame until your bloodline awakens!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
            "bgm_mood": "warmth"
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
            "display_text": "Channeling his scalding Chimera mana to temper Sylvie's freezing bloodline awakening, Leonhardt deepens his bonds, unlocks formidable new monster evolutions, and fortifies his subterranean domain against rising surface threats!",
            "tts_text": "Channeling his scalding Chimera mana to temper Sylvie's freezing bloodline awakening, Leonhardt deepens his bonds, unlocks formidable new monster evolutions, and fortifies his subterranean domain against rising surface threats!",
            "text": "Channeling his scalding Chimera mana to temper Sylvie's freezing bloodline awakening, Leonhardt deepens his bonds, unlocks formidable new monster evolutions, and fortifies his subterranean domain against rising surface threats!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "warmth"
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
            "display_text": "Dungeon Master Decree: To temper your bloodline core and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the dark depths, only the true Overlord commands destiny.",
            "tts_text": "Dungeon Master Decree: To temper your bloodline core and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the dark depths, only the true Overlord commands destiny.",
            "text": "Dungeon Master Decree: To temper your bloodline core and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the dark depths, only the true Overlord commands destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Dungeon Overlord. Awaken the frost-elven core, expand your subterranean floors, and witness Leonhardt's continued rise.",
            "tts_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Dungeon Overlord. Awaken the frost-elven core, expand your subterranean floors, and witness Leonhardt's continued rise.",
            "text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Dungeon Overlord. Awaken the frost-elven core, expand your subterranean floors, and witness Leonhardt's continued rise.",
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
    "final_audio": "output_dungeon_overlord_101_150.mp3",
    "final_video": "final_dungeon_overlord_101_150.mp4",
    "cover_image": "cover_dungeon_overlord_101_150.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_overlord_101_150.txt",
    "subtitles_file": "subtitles_dungeon_overlord_101_150.srt",
    "payload_file": "youtube_upload_payload_dungeon_overlord_101_150.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUNGEON OVERLORD: MONSTER GIRL HAREM! [Chapters 101-150] | Dark Fantasy LitRPG Audiobook",
    "tags": [
        "Dungeon Overlord", "Monster Girl Harem", "Dungeon Overlord Audiobook", "Dark Fantasy Audiobook",
        "LitRPG Progression", "Leonhardt", "Sylvie", "Dungeon Master Novel", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dungeon Overlord: Monster Girl Harem' (Part 3), covering Chapters 101 through 150!\n\n"
        "As Sylvie undergoes a perilous frost-elven bloodline transformation inside the sanctuary, Leonhardt pours his "
        "blazing Chimera mana into stabilizing her core—forging an unbreakable bond before leading his evolving monster "
        "legions into deeper subterranean conquests and surface clashes!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK FANTASY & LITRPG MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DungeonOverlord #MonsterGirl #DarkFantasy #LitRPG #Leonhardt #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Fantasy Dungeon Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (101, 105),
            "fallback_color": (16, 22, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-haired Chimera Overlord Leonhardt channeling warm golden-crimson fire mana "
                "to balance swirling glacial-blue frost magic surrounding a silver-haired frost-elf maiden inside a crystalline sanctuary chamber. "
                "UPPER-RIGHT BACKGROUND: Towering obsidian pillars covered in glowing blue frost runes and floating translucent system evolution windows. "
                "High-contrast glacier-blue, molten-gold, and obsidian-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (106, 110),
            "fallback_color": (14, 26, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dungeon-sanctuary book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Newly awakened frost-elf companion Sylvie standing beside Leonhardt in an underground crystal grotto, "
                "ice-blue elven mana swirling gracefully around her while glowing translucent dungeon management screens hover nearby. "
                "UPPER-RIGHT & BACKGROUND: Subterranean hot springs, glowing amethyst crystals, and carved stone balconies. "
                "High-contrast frost-cyan, warm-amber, and deep-teal palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (111, 115),
            "fallback_color": (28, 14, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital subterranean-forge book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Leonhardt forging enchanted weapons and dark-steel armor plates "
                "using Ifrit's crimson flames and glowing golden pentagram runes inside his dungeon workshop. "
                "UPPER-RIGHT & BACKGROUND: Floating monster cores, glowing runic anvils, and sparks illuminating dark basalt arches. "
                "High-contrast inferno-orange, celestial-gold, and charcoal-black palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (116, 120),
            "fallback_color": (22, 16, 32),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking dark-fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic battle pose of Leonhardt wielding his blazing greatsword alongside his frost-elf and dragonkin companions, "
                "unleashing intertwined waves of hellfire and glacial ice shards down a cavern corridor. "
                "UPPER-RIGHT SKY: Vast underground cavern ceiling lit by shimmering magical rifts and glowing crystal clusters. "
                "High-contrast ruby-crimson, electric-cyan, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (121, 125),
            "fallback_color": (16, 26, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted dungeon-floor expansion book-cover illustration in top-ranking webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dungeon Overlord Leonhardt standing atop an elevated obsidian overlook directing the construction of a massive new subterranean floor, "
                "holographic dungeon blueprints and glowing mana conduits spreading across the cavern below. "
                "UPPER-RIGHT & BACKGROUND: Towering stone fortresses, underground waterfalls, and patrolling monster guardians. "
                "High-contrast emerald-jade, royal-purple, and dark-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (126, 130),
            "fallback_color": (26, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted frontier raid book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Leonhardt emerging from a shadowed mountain pass at twilight with his elite monster girl vanguard, "
                "glowing blue Arachne Eyes scanning an enemy kingdom encampment in the valley below. "
                "UPPER-RIGHT & BACKGROUND: Jagged mountain peaks, mist-shrouded pine forests, and distant flickering war-camp fires. "
                "High-contrast amber-dusk, steel-slate, and crimson-accent palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (131, 135),
            "fallback_color": (24, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted monster-evolution ritual book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt standing before a glowing purple-and-gold dungeon core altar, channeling high-tier monster cores "
                "to evolve his subordinate commanders into formidable B-Rank forms. "
                "UPPER-RIGHT HORIZON: Swirling mana vortexes, floating rune rings, and towering obsidian spires. "
                "High-contrast celestial-gold, demonic-violet, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (136, 140),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted nocturnal siege defense book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt defending the outer gates of his mountain dungeon against an invading knightly crusade, "
                "unleashing dual-cast Cinderblast firestorms and adhesive shadow-webbing across the gorge. "
                "UPPER-RIGHT SKY: Stormy night clouds pierced by falling fireballs and glowing defensive barrier domes. "
                "High-contrast mystic-cyan, blazing-orange, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (141, 145),
            "fallback_color": (30, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted royal harem sanctuary book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt relaxing in his opulent subterranean throne hall surrounded by his devoted monster girl companions—Asuka, Sylvie, and his inner court, "
                "warm crystal lantern light illuminating rich silk draperies and golden goblets. "
                "UPPER-RIGHT & BACKGROUND: Vaulted obsidian arches, glowing mana fountains, and crimson banners. "
                "High-contrast royal-crimson, molten-gold, and dark-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (146, 150),
            "fallback_color": (32, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic overlord dominion book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Sovereign Chimera Overlord Leonhardt standing atop a colossal subterranean citadel overlooking his vast multi-tiered underground realm, "
                "wreathed in golden pentagram light and blazing Ifrit flames as his loyal legions assemble below. "
                "UPPER-RIGHT HORIZON: Endless illuminated crystal caverns, fortresses, and swirling elemental rivers. "
                "High-contrast empire-gold, inferno-crimson, and midnight-purple palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))