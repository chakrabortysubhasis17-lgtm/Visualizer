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


BUILD_DIR = "build_taming_monster_girl_harem_51_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/taming-my-monster-girl-harem-from-scratch/chapter-51",
    "novel_slug": "taming-my-monster-girl-harem-from-scratch",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
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

    # Standard 5-Beat Intro Hook (Episode 2: Chapters 51 to 100)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Fatima)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Fatima",
            "gender": "Female",
            "line_type": "Dialogue",
            "emotion": "teasing_pouty",
            "age_category": "adult",
            "display_text": '"What, do you want to console this old lady? You\'re thousands of years too early for that, kid."',
            "tts_text": '"What, do you want to console this old lady? You\'re thousands of years too early for that, kid."',
            "text": '"What, do you want to console this old lady? You\'re thousands of years too early for that, kid."',
            "voice": "en-US-JennyNeural",
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
            "display_text": "Trapped inside a timeless dimensional seal alongside the ancient God Tamer Fatima, Will awakens his Administrator privileges, conquers the Void Beast, and breaks back into the outer world—ready to claim noble power and expand his legendary monster girl harem across Chapters 51 through 100!",
            "tts_text": "Trapped inside a timeless dimensional seal alongside the ancient God Tamer Fatima... Will awakens his Administrator privileges, conquers the Void Beast, and breaks back into the outer world... ready to claim noble power and expand his legendary monster girl harem across Chapters 51 through 100!",
            "text": "Trapped inside a timeless dimensional seal alongside the ancient God Tamer Fatima, Will awakens his Administrator privileges, conquers the Void Beast, and breaks back into the outer world—ready to claim noble power and expand his legendary monster girl harem across Chapters 51 through 100!",
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
            "display_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
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
            "display_text": "Taming System Administrator Alert: To unlock Void-element mastery and continue this fifty-chapter fantasy harem marathon, hit that Like button and subscribe to the channel. Every soul strengthens your legendary contract roster.",
            "tts_text": "Taming System Administrator Alert: To unlock Void element mastery and continue this fifty chapter fantasy harem marathon, hit that Like button and subscribe to the channel. Every soul strengthens your legendary contract roster.",
            "text": "Taming System Administrator Alert: To unlock Void-element mastery and continue this fifty-chapter fantasy harem marathon, hit that Like button and subscribe to the channel. Every soul strengthens your legendary contract roster.",
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
        # Beat 4: Episode Continuation Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Your immersion resumes now, from Chapter 51 through Chapter 100 of Taming My Monster Girl Harem From Scratch. Stand beside Fatima against the Void Beast, evolve Ember and Fong, and follow Will's unstoppable ascent.",
            "tts_text": "Your immersion resumes now, from Chapter 51 through Chapter 100 of Taming My Monster Girl Harem From Scratch. Stand beside Fatima against the Void Beast, evolve Ember and Fong, and follow Will's unstoppable ascent.",
            "text": "Your immersion resumes now, from Chapter 51 through Chapter 100 of Taming My Monster Girl Harem From Scratch. Stand beside Fatima against the Void Beast, evolve Ember and Fong, and follow Will's unstoppable ascent.",
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
    "final_audio": "output_taming_monster_girl_harem_51_100.mp3",
    "final_video": "final_taming_monster_girl_harem_51_100.mp4",
    "cover_image": "cover_taming_monster_girl_harem_51_100.jpg",
    "timestamps_file": "youtube_timestamps_taming_monster_girl_harem_51_100.txt",
    "subtitles_file": "subtitles_taming_monster_girl_harem_51_100.srt",
    "payload_file": "youtube_upload_payload_taming_monster_girl_harem_51_100.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "TAMING MY MONSTER GIRL HAREM FROM SCRATCH [Chapters 51-100] | Harem LitRPG & Monster Taming Audiobook",
    "tags": [
        "Taming My Monster Girl Harem From Scratch", "Monster Girl Harem Audiobook", "Harem LitRPG",
        "Monster Taming Progression", "Will", "Cloud", "Fatima", "Ember", "Fong",
        "System LitRPG Audiobook", "Fantasy Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Episode 2 of 'Taming My Monster Girl Harem From Scratch', covering Chapters 51 through 100!\n\n"
        "After nine grueling days of mock battles and intensive energy training inside the timeless dimensional seal, "
        "Will discovers ancient God Tamer Fatima weeping before a crystal cavern inscribed with the names of her fallen "
        "comrades. As D-Day against the primordial Void Beast arrives, Will unleashes Fatima's variable gun arts, Void-space "
        "combos with Ember and Fong, and his newly unlocked Taming System Administrator privileges to shatter the seal, "
        "return to the outer world, and build his legendary monster girl harem across Chapters 51 through 100!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, center-locked vocal clarity, ±30° 3D stage & stereo ambience).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE HAREM LITRPG & MONSTER TAMING MARATHONS ON BEING A BONG:\n"
        "• Taming My Monster Girl Harem From Scratch [Chapters 1-50] -> https://www.youtube.com/watch?v=deMiRoFyY5g\n"
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
            "range": (51, 55),
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital fantasy-romance book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, luminous cavern lighting, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Eighteen-year-old blue-haired tamer Will gently holding the shoulders of ancient long-black-haired God Tamer Fatima in her dark overcoat inside a glowing crystal grotto, "
                "her cheeks flushed crimson as golden and violet energy strands drift around them. "
                "UPPER-RIGHT BACKGROUND: Giant suspended celestial crystal illuminating ancient carved stone walls. "
                "High-contrast celestial-gold, royal-violet, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (56, 60),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital boss-battle book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic low-angle framing and fiery brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Will firing dual elemental-energy SMGs alongside Fatima's glowing sniper rifle while royal slime maiden Ember and shadow werewolf assassin Fong weave space-void rifts, "
                "facing a colossal chained Void Beast rising through swirling dark lightning in a shattered wasteland. "
                "UPPER-RIGHT SKY: Cracked obsidian clouds split by golden-violet energy arcs. "
                "High-contrast molten-gold, abyssal-violet, and crimson palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "fallback_color": (18, 22, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dimensional-breakout book-cover illustration in top-ranking webnovel art style, "
                "vibrant painterly brushwork and radiant portal light, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Will emerging from a collapsing bluish-white dimensional rift into a sunlit forest clearing flanked by pink-haired Ember, wolf-eared Fong, and Fatima, "
                "a golden Administrator Taming System sigil gleaming above his palm. "
                "UPPER-RIGHT BACKGROUND: Towering emerald canopy pierced by morning sunbeams. "
                "High-contrast cyan-azure, sunlit-gold, and emerald-green palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (66, 70),
            "fallback_color": (20, 18, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking harem progression style, "
                "luminous cel-shaded lighting and ornate architectural detail, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Blue-haired Will standing inside a grand noble estate courtyard greeted by silver-haired beauty Luo Bingyue and elegant black-and-gold-clad Wan Li with her tiny winged Ice Pixie, "
                "warm lantern light glinting off his storage ring. "
                "UPPER-RIGHT BACKGROUND: Tiered eastern-fantasy palace roofs beneath twilight stars. "
                "High-contrast sapphire-blue, silver-white, and warm-gold palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (71, 75),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital noble-duel book-cover illustration in top-ranking webnovel art style, "
                "bold ink brushwork and dynamic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Will channeling multi-elemental administrator aura and phantom gun-arts on a marble duel stage while Fong unleashes shadow-darkness claws and Ember bends spatial barriers, "
                "stunning rival aristocratic tamers across the arena. "
                "UPPER-RIGHT & BACKGROUND: Colonnaded noble pavilion and fluttering crimson-gold banners. "
                "High-contrast imperial-gold, shadow-violet, and scarlet palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (76, 80),
            "fallback_color": (16, 24, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital monster-girl-taming book-cover illustration in crisp digital webnovel art style, "
                "luminous atmospheric depth and painterly brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Will extending a glowing golden-white Administrator contract circle toward an enchanting winged monster-girl maiden in a moonlit spirit valley, "
                "Ember and Fong standing protectively beside him as shimmering mana threads link their hands. "
                "UPPER-RIGHT HORIZON: Cascading silver waterfalls under twin luminous moons. "
                "High-contrast moonlit-turquoise, warm-gold, and twilight-teal palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (81, 85),
            "fallback_color": (22, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital ancient-sanctuary book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Will unlocking an ancient God Tamer vault with Fatima and Vice Chief Fina, "
                "floating rune-inscribed relics and glowing essence crystals orbiting a golden pedestal. "
                "UPPER-RIGHT & BACKGROUND: Towering obsidian pillars etched with glowing arcane circuits. "
                "High-contrast solar-amber, violet-indigo, and turquoise palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (86, 90),
            "fallback_color": (26, 16, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital demon-frontier-war book-cover illustration in top-ranking progression art style, "
                "intense dramatic lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Will leading his evolved monster-girl squad—Ember, Fong, and winged maiden companions—atop a blazing fortress rampart, "
                "unleashing synchronized void-flame barrages against a surging horde of demonic beasts below. "
                "UPPER-RIGHT SKY: Crimson-lit storm clouds torn open by golden lightning. "
                "High-contrast crimson-gold, obsidian-slate, and cerulean palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (91, 95),
            "fallback_color": (18, 20, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital starlit-harem-banquet book-cover illustration in high-end webnovel art style, "
                "warm romantic lighting and lush painterly brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Will relaxing on a moonlit sky-garden terrace surrounded by his affectionate monster-girl companions—pink-haired Ember, wolf-eared Fong, silver-haired Luo Bingyue, and Fatima—sharing warm lantern light. "
                "UPPER-RIGHT BACKGROUND: Panoramic illuminated capital skyline beneath a starry aurora sky. "
                "High-contrast rose-gold, lantern-amber, and deep-sapphire palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (96, 100),
            "fallback_color": (22, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Administrator-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Blue-haired Will standing atop a sun-drenched mountain citadel spire surrounded by his radiant, fully evolved monster-girl harem, "
                "commanding swirling golden-violet Administrator seals as majestic dragon and phoenix spirits soar through the clouds behind them. "
                "UPPER-RIGHT HORIZON: Vast fantasy continent bathed in golden sunrise light above a sea of clouds. "
                "High-contrast sunrise-gold, royal-violet, and emerald-jade palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
