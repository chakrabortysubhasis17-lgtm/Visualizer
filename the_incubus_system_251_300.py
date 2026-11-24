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


BUILD_DIR = "build_incubus_system_251_300"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-incubus-system/chapter-251",
    "novel_slug": "the-incubus-system",
    "start_chapter": 251,
    "end_chapter": 300,
    "is_start": False,
    "default_topic": "The Incubus System",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Scraper & Line Sanitization Rules (Strips WebNovel watermarks & Pubfuture ad injections)
    "strip_patterns": [
        r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*",
        r"https?://(?:m\.)?webnovel\.com/[^\s\"']+",
        r"Ads\s+by\s+Pubfuture",
        r"Pubfuture\s+Ads",
        r"Read\s+latest\s+Chapters\s+at\s+FreeWebNovel[^\n]*",
    ],

    # Standard 5-Beat Intro Hook (Continuation: Chapters 251 to 300)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Ethan)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Ethan",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "casual_confident",
            "age_category": "young",
            "display_text": '"Don\'t choke on your taco, Larry—Emma and Olivia already know that I\'m dating both of them!"',
            "tts_text": '"Don\'t choke on your taco, Larry... Emma and Olivia already know that I\'m dating both of them!"',
            "text": '"Don\'t choke on your taco, Larry—Emma and Olivia already know that I\'m dating both of them!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-4%",
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
            "emotion": "ominous",
            "age_category": "adult",
            "display_text": "With Emma and Olivia united as his loyal partners, Diamond's afternoon summons awaiting, and new demon hunts calling under the cover of night, Ethan balances campus secrets with rising demonic threats across Chapters 251 through 300!",
            "tts_text": "With Emma and Olivia united as his loyal partners, Diamond's afternoon summons awaiting, and new demon hunts calling under the cover of night... Ethan balances campus secrets with rising demonic threats across Chapters 251 through 300!",
            "text": "With Emma and Olivia united as his loyal partners, Diamond's afternoon summons awaiting, and new demon hunts calling under the cover of night, Ethan balances campus secrets with rising demonic threats across Chapters 251 through 300!",
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
            "display_text": "High Incubus System Alert: To strengthen Ethan's Demon's Rule protection and unlock this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
            "tts_text": "High Incubus System Alert: To strengthen Ethan's Demon's Rule protection and unlock this fifty chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
            "text": "High Incubus System Alert: To strengthen Ethan's Demon's Rule protection and unlock this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
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
        # Beat 4: Continuation Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Your immersion resumes now, covering Chapter 251 through Chapter 300 of The Incubus System. Test new demonic skills, untangle dangerous alliances, and follow Ethan's ascent.",
            "tts_text": "Your immersion resumes now, covering Chapter 251 through Chapter 300 of The Incubus System. Test new demonic skills, untangle dangerous alliances, and follow Ethan's ascent.",
            "text": "Your immersion resumes now, covering Chapter 251 through Chapter 300 of The Incubus System. Test new demonic skills, untangle dangerous alliances, and follow Ethan's ascent.",
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
    "final_audio": "output_incubus_system_251_300.mp3",
    "final_video": "final_incubus_system_251_300.mp4",
    "cover_image": "cover_incubus_system_251_300.jpg",
    "timestamps_file": "youtube_timestamps_incubus_system_251_300.txt",
    "subtitles_file": "subtitles_incubus_system_251_300.srt",
    "payload_file": "youtube_upload_payload_incubus_system_251_300.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE INCUBUS SYSTEM [Chapters 251-300] | Urban Fantasy Harem & System LitRPG Audiobook",
    "tags": [
        "The Incubus System", "Urban Fantasy Audiobook", "Harem LitRPG", "System Progression Novel",
        "Ethan Strongheart", "Damian High Incubus", "Emma", "Olivia", "Diamond", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Incubus System' (Part 6), covering Chapters 251 through 300!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/n6gAvCC1ZaA\n\n"
        "Following yesterday's turbulent events, Ethan balances campus life with Emma and Olivia—both now united as his loyal "
        "partners—while preparing for a crucial afternoon meeting with Diamond, watching over Mia's return to Ironshade Town, "
        "and taking his servants into the night to test newly unlocked demonic skills across Chapters 251 through 300.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, center-locked vocal clarity, stereo spatial ambience).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK FANTASY & HAREM LITRPG MARATHONS ON BEING A BONG:\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#TheIncubusSystem #UrbanFantasyAudiobook #HaremLitRPG #SystemProgression #EthanStrongheart #BeingABong"
    ),

    # 10 Textless 2D/2.5D Urban Dark Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (251, 255),
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dynamic medium-shot composition, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Crimson-eyed Ethan Strongheart seated at a sunlit university cafeteria table smiling calmly beside elegant blonde Emma "
                "and sharp-eyed Demon Hunter Olivia, while startled friend Larry drops his textbook across the table. "
                "UPPER-RIGHT BACKGROUND: Tall sunlit glass cafeteria windows overlooking green campus trees and clear afternoon clouds. "
                "High-contrast warm-amber, crimson-violet, and sunlit-azure palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (256, 260),
            "fallback_color": (24, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital high-society-intrigue book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic chiaroscuro lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan standing inside Diamond's luxurious top-floor executive office "
                "across from poised silver-haired heiress Diamond, subtle crimson demonic aura glinting in his eyes beside a crystal decanter. "
                "UPPER-RIGHT & BACKGROUND: Floor-to-ceiling panoramic windows revealing Nighthallow City's golden late-afternoon skyline. "
                "High-contrast royal-violet, champagne-gold, and scarlet-crimson palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (261, 265),
            "fallback_color": (16, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital nocturnal-demon-hunt book-cover illustration in top-ranking webnovel art style, "
                "dramatic rim lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Winged High Incubus Damian descending into a moonlit industrial alley alongside loyal succubus servants, "
                "unleashing newly awakened dark-crimson energy blades against emerging shadow-beasts. "
                "UPPER-RIGHT & BACKGROUND: Cracked dimensional barrier glowing purple between rain-slicked brick rooftops. "
                "High-contrast blood-crimson, abyssal-indigo, and electric-violet palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (266, 270),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and atmospheric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Graceful aristocratic lady Pearl resting on a velvet chaise inside her candlelit Gothic mansion parlor "
                "while Ethan inspects a glowing crimson bloodline crest floating above an ornate silver mirror. "
                "UPPER-RIGHT BACKGROUND: Tall arched mansion windows framed by crimson drapes and drifting midnight mist. "
                "High-contrast ruby-crimson, antique-gold, and twilight-purple palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (271, 275),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Ironshade-Town-journey book-cover illustration in top-ranking webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan escorting dark-haired Mia along a misty cobblestone avenue bordered by wrought-iron lanterns, "
                "faint black Shadow Needles and crimson protective wards shimmering in the evening air around them. "
                "UPPER-RIGHT & BACKGROUND: Steep slate-roofed towers of Ironshade Town silhouetted beneath a crescent moon. "
                "High-contrast midnight-blue, silver-mist, and scarlet-crimson palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (276, 280),
            "fallback_color": (22, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital hunter-alliance book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Demon Hunter Olivia and red-haired Ruby standing back-to-back with masked High Incubus Damian on a storm-lashed bridge, "
                "golden Holy Chains intersecting with obsidian Demonic Spikes as swirling abyssal hounds charge from the fog. "
                "UPPER-RIGHT & BACKGROUND: Suspended steel bridge cables illuminated by flashes of violet lightning. "
                "High-contrast holy-gold, blood-crimson, and storm-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (281, 285),
            "fallback_color": (20, 12, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted Devil-Space-evolution book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan meditating above a floating obsidian altar inside his Devil Space, "
                "translucent crimson Incubus System skill matrices and swirling dark-mana rings revolving around his outstretched hands. "
                "UPPER-RIGHT HORIZON: Endless crimson-lit void sea reflecting twin eclipsing moons. "
                "High-contrast scarlet-crimson, royal-violet, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (286, 290),
            "fallback_color": (24, 14, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted twilight-penthouse-intrigue book-cover illustration in top-ranking progression art style, "
                "dramatic low-angle framing and razor-sharp brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan standing beside poised Camila and sharp-suited Ivy on a glass-balustraded penthouse balcony, "
                "a subtle crimson contract seal fading into golden sparks between their hands. "
                "UPPER-RIGHT SKY: Neon reflections of Nighthallow City glittering beneath violet twilight clouds. "
                "High-contrast rose-gold, deep-violet, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (291, 295),
            "fallback_color": (26, 12, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted demonic-breach-clash book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: High Incubus Damian unleashing a storm of crimson-black Demonic Lances against a towering abyssal warlord "
                "amidst shattered warehouse pillars and surging purple hellfire. "
                "UPPER-RIGHT & BACKGROUND: Swirling dimensional vortex tearing across the harbor night sky. "
                "High-contrast molten-crimson, electric-violet, and charcoal-black palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (296, 300),
            "fallback_color": (18, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic High-Incubus-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: High Incubus Damian standing atop a rain-washed clocktower spire with dark wings spread wide against the dawn, "
                "glowing crimson eyes surveying Nighthallow City as his sister Celia and fox-eared Foxy watch from the balcony below. "
                "UPPER-RIGHT HORIZON: Brilliant crimson-and-gold sunrise piercing through parting storm clouds over the metropolis. "
                "High-contrast sunrise-gold, crimson-violet, and twilight-blue palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
