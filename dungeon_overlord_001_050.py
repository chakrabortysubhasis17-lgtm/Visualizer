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


BUILD_DIR = "build_dungeon_overlord_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-overlord-monster-girl-harem/chapter-1",
    "novel_slug": "dungeon-overlord-monster-girl-harem",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Dungeon Overlord: Monster Girl Harem",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 1 to 50 Premiere)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Leon)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Leon",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"A cracked blue crystal, a ticking timer, and a monster girl harem waiting in the dark... let the dungeon conquest begin!"',
            "tts_text": '"A cracked blue crystal, a ticking timer, and a monster girl harem waiting in the dark... let the dungeon conquest begin!"',
            "text": '"A cracked blue crystal, a ticking timer, and a monster girl harem waiting in the dark... let the dungeon conquest begin!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
            "bgm_mood": "dread"
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
            "display_text": "Awakening atop a ruined throne in a suffocating underground cavern as an Inferior Chimera, Leon accepts the role of Dungeon Master, unlocking magic copy skills, expanding his subterranean domain, and building an unstoppable monster girl harem!",
            "tts_text": "Awakening atop a ruined throne in a suffocating underground cavern as an Inferior Chimera, Leon accepts the role of Dungeon Master, unlocking magic copy skills, expanding his subterranean domain, and building an unstoppable monster girl harem!",
            "text": "Awakening atop a ruined throne in a suffocating underground cavern as an Inferior Chimera, Leon accepts the role of Dungeon Master, unlocking magic copy skills, expanding his subterranean domain, and building an unstoppable monster girl harem!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
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
            "display_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
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
            "display_text": "Dungeon Master Decree: To expand your subterranean lair and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the dark depths, only absolute overloads command destiny.",
            "tts_text": "Dungeon Master Decree: To expand your subterranean lair and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the dark depths, only absolute overloads command destiny.",
            "text": "Dungeon Master Decree: To expand your subterranean lair and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the dark depths, only absolute overloads command destiny.",
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
        # Beat 4: Series Premiere Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dungeon Overlord. Step into the ruined throne room, survive the monster attack, and watch Leon build his legendary empire.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dungeon Overlord. Step into the ruined throne room, survive the monster attack, and watch Leon build his legendary empire.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dungeon Overlord. Step into the ruined throne room, survive the monster attack, and watch Leon build his legendary empire.",
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
            "sfx": "impact",
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
    "final_audio": "output_dungeon_overlord_001_050.mp3",
    "final_video": "final_dungeon_overlord_001_050.mp4",
    "cover_image": "cover_dungeon_overlord_001_050.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_overlord_001_050.txt",
    "subtitles_file": "subtitles_dungeon_overlord_001_050.srt",
    "payload_file": "youtube_upload_payload_dungeon_overlord_001_050.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUNGEON OVERLORD: MONSTER GIRL HAREM! [Chapters 1-50] | Dark Fantasy LitRPG Audiobook",
    "tags": [
        "Dungeon Overlord", "Monster Girl Harem", "Dungeon Overlord Audiobook", "Dark Fantasy Audiobook",
        "LitRPG Progression", "Dungeon Master Novel", "Monster Girl Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Dungeon Overlord: Monster Girl Harem' (Part 1), covering Chapters 1 through 50!\n\n"
        "Waking up with fragmented memories atop a broken throne in a suffocating underground cavern, Leon cuts his finger on a cracked blue crystal, "
        "accepts the role of Dungeon Master, and evolves into an Inferior Chimera. With magic copy skills, a ticking timer, and low-level monsters attacking his domain, "
        "he must survive the initial onslaught and build an ultimate subterranean empire!\n\n"
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
        "#DungeonOverlord #MonsterGirl #DarkFantasy #LitRPG #DungeonMaster #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Fantasy Dungeon Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (18, 12, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy dungeon book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of young dark-haired Dungeon Master Leon with dull red eyes, sitting atop a broken jagged stone throne in a dark cavern, "
                "pale hands dripping blood onto a cracked glowing blue crystal shard on the floor, purple chimera mist swirling around his boots. "
                "UPPER-RIGHT BACKGROUND: Dripping stalactites and glowing violet dungeon moss casting eerie light across ancient black slates. "
                "High-contrast obsidian-purple, ethereal-blue, and dark-stone palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (22, 16, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy progression book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Explosive action shot of Leon in his newly evolved Inferior Chimera form, claws crackling with orange-red fire sparks, "
                "defending a subterranean throne room against low-level cave monsters emerging from the shadows. "
                "UPPER-RIGHT & BACKGROUND: Cracking cavern walls, floating blue holographic system notification windows, and glowing red monster eyes in dark tunnels. "
                "High-contrast flame-orange, dark-obsidian, and toxic-purple palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (12, 24, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dungeon-management book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Leon inspecting expanding subterranean trap corridors, "
                "fingers glowing with sticky adhesive webbing and magical sigils as dungeon core energy pulses around him. "
                "UPPER-RIGHT & BACKGROUND: Carved stone tunnels, glowing mana veins in the cavern walls, and shimmering portal crystals. "
                "High-contrast mystic-teal, dark-charcoal, and violet-glow palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (32, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking dark-fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic casting pose of Leon hurling a blazing fire-bolt spell down a subterranean corridor, flames illuminating his sharp red eyes and clawed hands. "
                "UPPER-RIGHT SKY: Vast subterranean cavern ceiling adorned with glowing crystals and creeping spider-silk webs. "
                "High-contrast crimson-fire, electric-violet, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (20, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted monster-girl sanctuary book-cover illustration in top-ranking dark-fantasy webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dungeon Master Leon standing proudly in an expanded underground hall surrounded by newly summoned monster girls (arachne and fae silhouettes), "
                "holding a glowing magical core while system attribute screens hover in the air. "
                "UPPER-RIGHT & BACKGROUND: Beautiful subterranean grotto with glowing crystal pillars, underground pools, and carved stone balconies. "
                "High-contrast royal-violet, golden-amber, and dark-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (14, 28, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted dungeon expansion book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Leon examining dungeon blueprint holograms and architectural room expansions in a newly excavated cavern sector, "
                "claws glowing with faint magic copy energy. "
                "UPPER-RIGHT & BACKGROUND: Expanding underground chambers, goblin workshops, and reinforced obsidian walls under magical torchlight. "
                "High-contrast emerald-glow, dark-slate, and mystic-blue palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (28, 20, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted monster-girl harem chamber book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leon seated upon an upgraded obsidian throne flanked by loyal and devoted monster girl generals, "
                "surrounded by luxurious dungeon chambers filled with treasures and magical artifacts. "
                "UPPER-RIGHT HORIZON: Vaulted stone ceilings, hanging crystal lanterns, and rich velvet drapery. "
                "High-contrast molten-gold, ruby-red, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted dungeon defense battle book-cover illustration in top-ranking dark-fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leon leading his monster forces in repelling an invading adventurer party at the dungeon gates, "
                "unleashing web traps and fire magic as enemy swords clash against reinforced obsidian barricades. "
                "UPPER-RIGHT SKY: Smoky cavern tunnels lit by magical fireballs and glowing trap glyphs on the stone floor. "
                "High-contrast mystic-cyan, blazing-orange, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (30, 12, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted mystical subterranean grotto book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leon resting in a private crystal grotto with elite monster companions, "
                "surrounded by glowing spiritual flora and underground hot springs under a vaulted crystalline roof. "
                "UPPER-RIGHT & BACKGROUND: Sparkling stalactites, floating mana wisps, and cascading subterranean waterfalls. "
                "High-contrast amethyst-purple, celestial-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (34, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic dungeon empire triumph book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Sovereign Dungeon Overlord Leon standing triumphantly atop a massive obsidian citadel overlooking a vast underground kingdom, "
                "flanked by his loyal monster girl army and glowing dungeon core pillars. "
                "UPPER-RIGHT HORIZON: Endless tiers of illuminated cavern cities and glowing magical skies stretching across the subterranean realm. "
                "High-contrast empire-gold, ruby-red, and dark-obsidian palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))