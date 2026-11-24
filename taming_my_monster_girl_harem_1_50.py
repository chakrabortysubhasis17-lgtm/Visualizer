import os
import re
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

WATERMARK_PATTERNS = [
    re.compile(r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*", re.IGNORECASE),
    re.compile(r"https?://(?:m\.)?webnovel\.com/[^\s\"']+", re.IGNORECASE),
    re.compile(r"Ads\s+by\s+Pubfuture", re.IGNORECASE),
    re.compile(r"Pubfuture\s+Ads", re.IGNORECASE),
]


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
                has_watermark = any(
                    any(
                        pat.search(r.get("display_text") or r.get("tts_text") or r.get("text", ""))
                        for pat in WATERMARK_PATTERNS
                    )
                    for r in rows
                )
                if len(rows) < 8 or has_watermark or any(
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
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} stale/watermark cache files to guarantee clean scraping.", flush=True)


BUILD_DIR = "build_taming_monster_girl_harem_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/taming-my-monster-girl-harem-from-scratch/chapter-1",
    "novel_slug": "taming-my-monster-girl-harem-from-scratch",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Taming My Monster Girl Harem From Scratch",

    "batch_size": 15,
    "parallel_chapters": 1,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Scraper & Line Sanitization Rules
    "strip_patterns": [
        r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*",
        r"https?://(?:m\.)?webnovel\.com/[^\s\"']+",
        r"Ads\s+by\s+Pubfuture",
        r"Pubfuture\s+Ads",
        r"Read\s+latest\s+Chapters\s+at\s+FreeWebNovel[^\n]*",
    ],

    # Standard 5-Beat Intro Hook (Series Premiere: Chapters 1 to 50)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Cloud)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Cloud",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "exhilarated_bold",
            "age_category": "young",
            "display_text": '"I\'ll make my own monster girl harem!"',
            "tts_text": '"I\'ll make my own monster girl harem!"',
            "text": '"I\'ll make my own monster girl harem!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "+0Hz",
            "rate": "-2%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "chime",
            "bgm_mood": "intrigue"
        },
        # Beat 1b: Narrative Teaser Hook (Slow, weighty delivery)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Awakening his past-life memories in a gritty alleyway and knocking out the mayor's ruthless son with a single counterpunch, eighteen-year-old orphan Cloud unlocks the Taming System—escaping past the city gates to inherit monster skills and build his own legendary monster girl harem across Chapters 1 through 50!",
            "tts_text": "Awakening his past life memories in a gritty alleyway and knocking out the mayor's ruthless son with a single counterpunch... eighteen year old orphan Cloud unlocks the Taming System... escaping past the city gates to inherit monster skills and build his own legendary monster girl harem across Chapters 1 through 50!",
            "text": "Awakening his past-life memories in a gritty alleyway and knocking out the mayor's ruthless son with a single counterpunch, eighteen-year-old orphan Cloud unlocks the Taming System—escaping past the city gates to inherit monster skills and build his own legendary monster girl harem across Chapters 1 through 50!",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-6%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "intrigue"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 2: Channel Trademark Signature
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "confident",
            "age_category": "adult",
            "display_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "engaged_alert",
            "pitch": "-2Hz",
            "rate": "+2%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "whoosh",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 3: In-Universe Call to Action
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "persuasive",
            "age_category": "adult",
            "display_text": "Taming System Alert: To unlock Cloud's monster skill inheritance and launch this fifty-chapter fantasy harem marathon, hit that Like button and subscribe to the channel. Every soul strengthens your legendary contract roster.",
            "tts_text": "Taming System Alert: To unlock Cloud's monster skill inheritance and launch this fifty chapter fantasy harem marathon, hit that Like button and subscribe to the channel. Every soul strengthens your legendary contract roster.",
            "text": "Taming System Alert: To unlock Cloud's monster skill inheritance and launch this fifty-chapter fantasy harem marathon, hit that Like button and subscribe to the channel. Every soul strengthens your legendary contract roster.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "conversational_mid",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "interface",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 4: Series Premiere Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Taming My Monster Girl Harem From Scratch. Escape the city guards, tame fierce monster girls, and follow Cloud's rise.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Taming My Monster Girl Harem From Scratch. Escape the city guards, tame fierce monster girls, and follow Cloud's rise.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Taming My Monster Girl Harem From Scratch. Escape the city guards, tame fierce monster girls, and follow Cloud's rise.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-3%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "tension"
        },
        # Beat 5: Transition SFX & Lead-in Silence
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.2,
            "sfx": "teleport",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 1.0,
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_taming_monster_girl_harem_1_50.mp3",
    "final_video": "final_taming_monster_girl_harem_1_50.mp4",
    "cover_image": "cover_taming_monster_girl_harem_1_50.jpg",
    "timestamps_file": "youtube_timestamps_taming_monster_girl_harem_1_50.txt",
    "subtitles_file": "subtitles_taming_monster_girl_harem_1_50.srt",
    "payload_file": "youtube_upload_payload_taming_monster_girl_harem_1_50.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "TAMING MY MONSTER GIRL HAREM FROM SCRATCH [Chapters 1-50] | Harem LitRPG & Monster Taming Audiobook",
    "tags": [
        "Taming My Monster Girl Harem From Scratch", "Monster Girl Harem Audiobook", "Harem LitRPG",
        "Monster Taming Progression", "Cloud", "System LitRPG Audiobook", "Fantasy Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Episode 1 of 'Taming My Monster Girl Harem From Scratch', covering Chapters 1 through 50!\n\n"
        "In a harsh world where humans survive only by taming monsters and inheriting their skills, eighteen-year-old "
        "malnourished orphan Cloud regains his past-life memories in the middle of a brutal beating by the mayor's arrogant "
        "son, Fatty Zen. Sidestepping Zen's punch and knocking him out cold, Cloud awakens the Taming System and flees past "
        "the city gates with one bold ambition—to tame powerful monster girls, inherit their abilities, and build his own "
        "legendary monster girl harem across Chapters 1 through 50!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, center-locked vocal clarity, stereo spatial ambience).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE HAREM LITRPG & MONSTER TAMING MARATHONS ON BEING A BONG:\n"
        "• The First Legendary Beast Master -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• The Incubus System -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#TamingMyMonsterGirlHaremFromScratch #MonsterGirlHarem #HaremLitRPG #MonsterTaming #SystemProgression #BeingABong"
    ),

    # 10 Textless 2D/2.5D Fantasy Harem Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (22, 18, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital fantasy-adventure book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dynamic low-angle composition, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Lean, ragged-clothed eighteen-year-old youth Cloud with a cut on his forehead running joyfully along a sunlit dirt road outside massive stone city gates, "
                "a glowing golden-cyan Taming System rune shimmering beside his outstretched hand as wind sweeps through his hair. "
                "UPPER-RIGHT BACKGROUND: Medieval walled city towers fading behind rolling green hills and bright sunlit clouds. "
                "High-contrast sunlit-gold, emerald-green, and sky-azure palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (16, 24, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital monster-taming-pact book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and luminous forest lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Cloud kneeling beside a crystal woodland brook extending a glowing golden taming contract circle toward an enchanting fox-eared monster girl, "
                "swirling arcane threads linking their palms as her fluffy tail sways in wonder. "
                "UPPER-RIGHT & BACKGROUND: Sunbeams piercing through towering ancient spirit trees and drifting glowing pollen. "
                "High-contrast emerald-jade, warm-gold, and twilight-teal palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital skill-inheritance book-cover illustration in top-ranking webnovel art style, "
                "dramatic rim lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Cloud channel-testing newly inherited monster agility and claw aura in a rocky canyon clearing, "
                "while his loyal wolf-eared warrior companion watches proudly with a curved blade resting on her shoulder. "
                "UPPER-RIGHT & BACKGROUND: Jagged red-rock cliffs bathed in warm late-afternoon light. "
                "High-contrast amber-crimson, royal-violet, and stone-slate palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (18, 20, 32),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking harem progression style, "
                "vibrant cel-shaded lighting and dynamic composition, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Cloud standing on a bustling frontier guild balcony flanked by a graceful winged harpy maiden and a silver-haired demi-human beauty, "
                "translucent golden Taming System status sigils gleaming beside him. "
                "UPPER-RIGHT BACKGROUND: Timber-and-stone guildhall roofs, fluttering adventure banners, and distant misty peaks. "
                "High-contrast sapphire-blue, rose-gold, and warm-ivory palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital forest-ambush-battle book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic action brushwork and fiery lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Cloud unleashing synchronized monster-tamer skills alongside his fierce dragonkin and lamia companions, "
                "crimson-gold shockwaves repelling a charging pack of armored wild beasts in a moonlit glade. "
                "UPPER-RIGHT & BACKGROUND: Towering pine silhouettes lit by flying sparks and crescent moonlight. "
                "High-contrast molten-gold, blood-crimson, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (16, 22, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital lakeside-sanctuary book-cover illustration in crisp digital webnovel art style, "
                "luminous atmospheric depth and painterly brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Cloud relaxing beside a starlit hot-spring lake surrounded by his affectionate monster-girl companions—fox-girl, cat-girl, and elf-eared mage—sharing warm lantern light. "
                "UPPER-RIGHT & BACKGROUND: Mirror-calm lake water reflecting twin moons and glowing fireflies among willow branches. "
                "High-contrast moonlit-cyan, lantern-amber, and deep-violet palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted ancient-ruins-dungeon book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Cloud leading his monster-girl party into a sunken crystal cavern, "
                "raising a glowing golden taming medallion to pacify a towering guardian beast-maiden wrapped in arcane chains. "
                "UPPER-RIGHT HORIZON: Luminous turquoise crystal spires illuminating carved stone pillars in the cavern vault. "
                "High-contrast crystal-turquoise, imperial-gold, and abyssal-purple palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (26, 18, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted arena-showdown book-cover illustration in top-ranking progression art style, "
                "dramatic low-angle framing and razor-sharp brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Confident, well-built Cloud standing in a grand tournament arena channeling multi-monster aura rings, "
                "stunning rival noble tamers across the stone floor while his beast-girl retinue cheers from the box. "
                "UPPER-RIGHT SKY: Dramatic golden sunset clouds and fluttering tournament pennants above stone coliseum arches. "
                "High-contrast solar-gold, scarlet-crimson, and twilight-slate palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (20, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted bloodline-awakening book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Cloud standing at the center of an intricate golden-and-violet taming mandala as his contracted monster girls undergo bloodline evolution around him, "
                "radiant feathers, tail-flames, and ethereal runes swirling skyward. "
                "UPPER-RIGHT & BACKGROUND: Star-filled night sky split by an aurora of arcane mana. "
                "High-contrast celestial-gold, royal-violet, and rose-magenta palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (22, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Beast-Lord-dominion book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Cloud standing atop a sun-drenched mountain citadel terrace surrounded by his loyal, radiant monster-girl harem, "
                "commanding swirling multi-elemental beast auras as a legendary sky-serpent coils gracefully through the clouds behind them. "
                "UPPER-RIGHT HORIZON: Vast fantasy kingdom valleys bathed in golden morning light beneath soaring peaks. "
                "High-contrast sunrise-gold, emerald-jade, and crimson-violet palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
