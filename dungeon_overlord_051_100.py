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


BUILD_DIR = "build_dungeon_overlord_051_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-overlord-monster-girl-harem/chapter-51",
    "novel_slug": "dungeon-overlord-monster-girl-harem",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
    "default_topic": "Dungeon Overlord: Monster Girl Harem",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 51 to 100 Continuation)
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
            "display_text": '"Stay back, Asuka! Dual Cast—Tyrant Accel! Let\'s see how this upper C-Rank Drakefang Salamander handles real hellfire!"',
            "tts_text": '"Stay back, Ah-soo-kah! Dual Cast... Tyrant Accel! Let\'s see how this upper C-Rank Drakefang Salamander handles real hellfire!"',
            "text": '"Stay back, Asuka! Dual Cast—Tyrant Accel! Let\'s see how this upper C-Rank Drakefang Salamander handles real hellfire!"',
            "voice": "en-US-GuyNeural",
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
            "display_text": "Pushing his Chimera bloodline and Ifrit's forbidden mana past their limits, Leonhardt clashes with an upper C-Rank Drakefang Salamander beside a boiling forest lake—protecting Asuka, unlocking devastating dual-cast magic, and expanding his monster girl empire!",
            "tts_text": "Pushing his Chimera bloodline and Ee-freet's forbidden mana past their limits, Leonhardt clashes with an upper C-Rank Drakefang Salamander beside a boiling forest lake... protecting Ah-soo-kah, unlocking devastating dual-cast magic, and expanding his monster girl empire!",
            "text": "Pushing his Chimera bloodline and Ifrit's forbidden mana past their limits, Leonhardt clashes with an upper C-Rank Drakefang Salamander beside a boiling forest lake—protecting Asuka, unlocking devastating dual-cast magic, and expanding his monster girl empire!",
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
            "display_text": "Dungeon Master Decree: To amplify your Chimera mana and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the monster realm, only supreme overlords command destiny.",
            "tts_text": "Dungeon Master Decree: To amplify your Chimera mana and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the monster realm, only supreme overlords command destiny.",
            "text": "Dungeon Master Decree: To amplify your Chimera mana and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the monster realm, only supreme overlords command destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Dungeon Overlord. Activate your Arachne Eyes, draw your greatsword, and witness Leonhardt's relentless evolution.",
            "tts_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Dungeon Overlord. Activate your Ah-rack-nee Eyes, draw your greatsword, and witness Leonhardt's relentless evolution.",
            "text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Dungeon Overlord. Activate your Arachne Eyes, draw your greatsword, and witness Leonhardt's relentless evolution.",
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
    "final_audio": "output_dungeon_overlord_051_100.mp3",
    "final_video": "final_dungeon_overlord_051_100.mp4",
    "cover_image": "cover_dungeon_overlord_051_100.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_overlord_051_100.txt",
    "subtitles_file": "subtitles_dungeon_overlord_051_100.srt",
    "payload_file": "youtube_upload_payload_dungeon_overlord_051_100.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUNGEON OVERLORD: MONSTER GIRL HAREM! [Chapters 51-100] | Dark Fantasy LitRPG Audiobook",
    "tags": [
        "Dungeon Overlord", "Monster Girl Harem", "Dungeon Overlord Audiobook", "Dark Fantasy Audiobook",
        "LitRPG Progression", "Leonhardt", "Asuka", "Dungeon Master Novel", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dungeon Overlord: Monster Girl Harem' (Part 2), covering Chapters 51 through 100!\n\n"
        "Ambushed beside a forest lake by a colossal upper C-Rank Drakefang Salamander, Leonhardt shields Asuka, "
        "activates his 320-degree Arachne Eyes, and pushes his Chimera physique beyond Ifrit's limits with Dual-Cast Tyrant Accel "
        "and Cinderblast—unleashing devastating draconic firepower as his subterranean empire grows!\n\n"
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
            "range": (51, 55),
            "fallback_color": (28, 12, 16),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-haired Chimera warrior Leonhardt standing defensively on a grassy forest lake embankment, "
                "eyes glowing with electric-blue Arachne sight and golden pentagrams, wielding a summoned greatsword wreathed in crimson flames beside swordswoman Asuka. "
                "UPPER-RIGHT BACKGROUND: Massive obsidian-scaled Drakefang Salamander erupting from boiling lake water with glowing magma-veined underbelly and roaring fiery jaws. "
                "High-contrast crimson-flame, obsidian-black, and electric-blue palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (56, 60),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy progression book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Explosive combat pose of Leonhardt unleashing dual-cast Cinderblast fireballs and a towering wall of red flames, "
                "steam billowing off a dark forest river while silver sparks fly from his greatsword. "
                "UPPER-RIGHT & BACKGROUND: Towering ancient forest trees illuminated by fiery shockwaves under a twilight purple sky. "
                "High-contrast inferno-orange, violet-shadow, and dark-charcoal palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "fallback_color": (14, 22, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dungeon-sanctuary book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Leonhardt inside his subterranean crystal chamber tending to his wounds, "
                "surrounded by glowing blue holographic dungeon management windows and swirling elemental fire-spirit wisps. "
                "UPPER-RIGHT & BACKGROUND: Vaulted obsidian cavern arches, glowing mana conduits, and shimmering portal stones. "
                "High-contrast mystic-cyan, molten-gold, and deep-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (66, 70),
            "fallback_color": (30, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking dark-fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic sparring scene in a subterranean training arena, Leonhardt clashing blades with Asuka amid bursts of crimson sparks and golden mana trails. "
                "UPPER-RIGHT SKY: Massive underground cavern dome lit by floating crystal chandeliers and glowing rune circles. "
                "High-contrast ruby-crimson, electric-gold, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (71, 75),
            "fallback_color": (16, 26, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted monster-girl alliance book-cover illustration in top-ranking dark-fantasy webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dungeon Overlord Leonhardt standing in a lush subterranean grotto flanked by loyal monster girl companions, "
                "inspecting newly unlocked Chimera bloodline evolutions on a translucent system screen. "
                "UPPER-RIGHT & BACKGROUND: Glowing bioluminescent flora, underground waterfalls, and carved obsidian terraces. "
                "High-contrast emerald-jade, royal-purple, and warm-amber palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (76, 80),
            "fallback_color": (26, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted frontier expedition book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Leonhardt emerging from a hidden mountain cavern entrance overlooking the Gladius Kingdom borderlands at dusk, "
                "dark cloak billowing as he scouts approaching mercenary banners with glowing blue eyes. "
                "UPPER-RIGHT & BACKGROUND: Jagged mountain ridges, mist-shrouded valleys, and distant fortress watchtowers. "
                "High-contrast amber-dusk, steel-slate, and crimson-accent palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (81, 85),
            "fallback_color": (24, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-alchemy & core-forging book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt refining a blazing C-Rank monster core over an obsidian altar, channeling golden pentagram magic and crimson fire into his palm. "
                "UPPER-RIGHT HORIZON: Ancient stone pillars etched with glowing runes and swirling violet-gold mana vortexes. "
                "High-contrast celestial-gold, demonic-violet, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (86, 90),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted nocturnal ambush book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt leaping through a moonlit forest canopy with blazing greatsword raised, "
                "unleashing crescent waves of hellfire and adhesive shadow-silk threads at enemy raiders below. "
                "UPPER-RIGHT SKY: Full silver moon piercing dark storm clouds above ancient pine silhouettes. "
                "High-contrast silver-cyan, blazing-crimson, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (91, 95),
            "fallback_color": (30, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted royal dungeon banquet book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dungeon Overlord Leonhardt seated on his upgraded obsidian throne surrounded by his devoted monster girl harem, "
                "warm crystal lantern light illuminating ornate dark armor and wine goblets. "
                "UPPER-RIGHT & BACKGROUND: Grand subterranean throne hall with towering rune-carved columns and glowing crimson braziers. "
                "High-contrast royal-crimson, molten-gold, and deep-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (96, 100),
            "fallback_color": (32, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic overlord ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Sovereign Chimera Overlord Leonhardt standing atop a towering subterranean citadel spire, "
                "wreathed in twin auras of golden pentagram light and blazing Ifrit flames as his monster legions assemble below. "
                "UPPER-RIGHT HORIZON: Vast illuminated underground empire of crystal caverns, glowing fortresses, and swirling mana rivers. "
                "High-contrast empire-gold, inferno-crimson, and midnight-purple palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))