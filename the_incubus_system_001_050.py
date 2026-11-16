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


BUILD_DIR = "build_the_incubus_system_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-incubus-system/chapter-1",
    "novel_slug": "the-incubus-system",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "The Incubus System: Urban Fantasy",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 1 to 50 Premiere)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Ethan)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Ethan",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"The door is locked, the curtains are down, and everyone is looking at me like prey... what kind of interview is this?!"',
            "tts_text": '"The door is locked, the curtains are down, and everyone is looking at me like prey... what kind of interview is this?!"',
            "text": '"The door is locked, the curtains are down, and everyone is looking at me like prey... what kind of interview is this?!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
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
            "display_text": "An eighteen-year-old virgin college student struggling to make ends meet in Ironshade Town, Ethan walks straight into a sinister trap during a private tutor interview in Nighthallow City—unknowingly awakening the ultimate Incubus System!",
            "tts_text": "An eighteen-year-old virgin college student struggling to make ends meet in Ironshade Town, Ethan walks straight into a sinister trap during a private tutor interview in Nighthallow City... unknowingly awakening the ultimate Incubus System!",
            "text": "An eighteen-year-old virgin college student struggling to make ends meet in Ironshade Town, Ethan walks straight into a sinister trap during a private tutor interview in Nighthallow City—unknowingly awakening the ultimate Incubus System!",
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
            "display_text": "Incubus System Decree: To unlock supernatural charm and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In a world of elves, lamias, and hidden dangers, only absolute allure commands destiny.",
            "tts_text": "Incubus System Decree: To unlock supernatural charm and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In a world of elves, lamias, and hidden dangers, only absolute allure commands destiny.",
            "text": "Incubus System Decree: To unlock supernatural charm and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In a world of elves, lamias, and hidden dangers, only absolute allure commands destiny.",
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
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of The Incubus System. Step into Nighthallow City, survive Mr. Jackson's office, and watch Ethan's extraordinary awakening.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of The Incubus System. Step into Nighthallow City, survive Mr. Jackson's office, and watch Ethan's extraordinary awakening.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of The Incubus System. Step into Nighthallow City, survive Mr. Jackson's office, and watch Ethan's extraordinary awakening.",
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
    "final_audio": "output_the_incubus_system_001_050.mp3",
    "final_video": "final_the_incubus_system_001_050.mp4",
    "cover_image": "cover_the_incubus_system_001_050.jpg",
    "timestamps_file": "youtube_timestamps_the_incubus_system_001_050.txt",
    "subtitles_file": "subtitles_the_incubus_system_001_050.srt",
    "payload_file": "youtube_upload_payload_the_incubus_system_001_050.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE INCUBUS SYSTEM! [Chapters 1-50] | Urban Fantasy Progression Full Audiobook",
    "tags": [
        "The Incubus System", "The Incubus System Audiobook", "Ethan", "Urban Fantasy Audiobook",
        "System Novel", "Nighthallow City", "Harem Progression Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'The Incubus System' (Part 1), covering Chapters 1 through 50!\n\n"
        "Living in Ironshade Town after his father's tragic accident, 18-year-old college student Ethan takes the train to Nighthallow City "
        "for a private tutor interview. But when Mr. Jackson locks the office door and strangers surround him like predators, Ethan awakens "
        "the legendary Incubus System—changing his destiny in a world of elves, lamias, and hidden dark powers!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE URBAN FANTASY & PROGRESSION MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#TheIncubusSystem #UrbanFantasy #ProgressionFantasy #Ethan #Audiobook #BeingABong"
    ),

    # 10 Textless 2D/2.5D Urban Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (18, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of 18-year-old brown-haired college student Ethan standing inside a neat vintage office room in Nighthallow City, "
                "eyes wide in tense realization as dark office curtains slide down and a locked door blocks the exit. "
                "UPPER-RIGHT BACKGROUND: Wooden executive desk, glowing lamplight, and mysterious figures standing in the shadows. "
                "High-contrast obsidian-purple, amber-glow, and dark-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (22, 16, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban fantasy progression book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Explosive action shot of Ethan awakening his supernatural incubus abilities, eyes flashing with seductive purple system energy "
                "as glowing holographic system status screens materialize around him. "
                "UPPER-RIGHT & BACKGROUND: Nighthallow City skyline at dusk, glowing MRT station neon lights, and misty street lamps. "
                "High-contrast mystic-purple, neon-cyan, and dark-charcoal palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (14, 22, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital modern fantasy book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan walking along Green Lake near Ironshade Town at twilight, "
                "reflecting on family memories with a melancholic expression as magical mist rises from the water. "
                "UPPER-RIGHT & BACKGROUND: Beautiful lakeside trees, distant town lights, and a clear evening sky with twin twilight stars. "
                "High-contrast emerald-teal, twilight-blue, and violet-glow palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (32, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking urban fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic encounter pose of Ethan meeting elegant magical beings in Nighthallow City, including a refined lamia in office attire and a graceful elf housewife. "
                "UPPER-RIGHT SKY: Bustling Aeros Republic trading city streets under an evening sky. "
                "High-contrast crimson-magenta, electric-violet, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (20, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted supernatural system-progression book-cover illustration in top-ranking dark-fantasy webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan standing confidently in a shadowy chamber, surrounded by floating system reward notifications and rising pink-purple incubus energy aura. "
                "UPPER-RIGHT & BACKGROUND: Elegant modern office interior with lowered window blinds and mysterious silhouettes watching from the corners. "
                "High-contrast royal-violet, golden-amber, and dark-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (14, 28, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted city mystery book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Ethan investigating secret faction documents in a dimly lit Nighthallow City archive room, "
                "fingers glowing with nascent incubus magic as system quest logs hover nearby. "
                "UPPER-RIGHT & BACKGROUND: Towering office buildings, glowing street signs, and foggy metropolitan alleyways. "
                "High-contrast emerald-glow, dark-slate, and mystic-blue palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (28, 20, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted secret hideout book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan seated upon a modern executive chair in a secured safehouse, flanked by newly allied supernatural companions, "
                "surrounded by glowing system upgrade panels and tactical maps. "
                "UPPER-RIGHT HORIZON: Vaulted ceiling, sleek modern architecture, and ambient moody lighting. "
                "High-contrast molten-gold, ruby-red, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted supernatural confrontation book-cover illustration in top-ranking urban fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan using his newly awakened incubus charm to disarm hostile rogue operatives in a high-rise Nighthallow City office, "
                "unleashing invisible waves of seductive energy that disorient armed attackers. "
                "UPPER-RIGHT SKY: Glass skyscraper windows reflecting a starry metropolitan night sky. "
                "High-contrast mystic-cyan, blazing-orange, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (30, 12, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted mystical safehouse grotto book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan resting in a luxurious penthouse safehouse with supernatural allies, "
                "surrounded by glowing magical artifacts and ambient purple lighting under a high ceiling. "
                "UPPER-RIGHT & BACKGROUND: Sparkling city lights visible through massive glass windows, elegant modern furniture, and warm lamps. "
                "High-contrast amethyst-purple, celestial-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (34, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic urban-overlord triumph book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Confident Ethan standing triumphantly atop a towering skyscraper overlooking all of Nighthallow City at night, "
                "surrounded by his devoted supernatural companions and glowing system dominion panels. "
                "UPPER-RIGHT HORIZON: Endless tiers of illuminated metropolitan skyscrapers and glowing magical skies stretching across the republic. "
                "High-contrast empire-gold, ruby-red, and dark-obsidian palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))