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


BUILD_DIR = "build_incubus_system_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-incubus-system/chapter-101",
    "novel_slug": "the-incubus-system",
    "start_chapter": 101,
    "end_chapter": 150,
    "is_start": False,
    "default_topic": "The Incubus System",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 101 to 150 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Damian / Ethan)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Damian",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"Save your Magic Power, hunter! I\'m not a man—I\'m a demon, and if we don\'t seal these dimensional cracks, your entire order will be wiped out!"',
            "tts_text": '"Save your Magic Power, hunter! I\'m not a man... I\'m a demon, and if we don\'t seal these dimensional cracks, your entire order will be wiped out!"',
            "text": '"Save your Magic Power, hunter! I\'m not a man—I\'m a demon, and if we don\'t seal these dimensional cracks, your entire order will be wiped out!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch": "-1Hz",
            "sfx": "whoosh",
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
            "display_text": "Clashing midair with Demon Hunter Ruby inside his Devil Space, High Incubus Ethan Strongheart joins forces with Royal Succubus Lilieth and Demon General Sarael to seal shattering dimensional rifts—pushing his Incubus System to new heights while balancing his double life and seductive powers!",
            "tts_text": "Clashing midair with Demon Hunter Ruby inside his Devil Space, High Incubus Ethan Strongheart joins forces with Royal Succubus Lilieth and Demon General Sarael to seal shattering dimensional rifts... pushing his Incubus System to new heights while balancing his double life and seductive powers!",
            "text": "Clashing midair with Demon Hunter Ruby inside his Devil Space, High Incubus Ethan Strongheart joins forces with Royal Succubus Lilieth and Demon General Sarael to seal shattering dimensional rifts—pushing his Incubus System to new heights while balancing his double life and seductive powers!",
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
            "display_text": "High Incubus System Alert: To replenish Ethan's Demonic Points and unlock this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
            "tts_text": "High Incubus System Alert: To replenish Ethan's Demonic Points and unlock this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
            "text": "High Incubus System Alert: To replenish Ethan's Demonic Points and unlock this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
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
            "display_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of The Incubus System. Enter the Devil Space, face the Demon Generals, and witness Ethan command both shadow and desire.",
            "tts_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of The Incubus System. Enter the Devil Space, face the Demon Generals, and witness Ethan command both shadow and desire.",
            "text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of The Incubus System. Enter the Devil Space, face the Demon Generals, and witness Ethan command both shadow and desire.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "intrigue"
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
    "final_audio": "output_incubus_system_101_150.mp3",
    "final_video": "final_incubus_system_101_150.mp4",
    "cover_image": "cover_incubus_system_101_150.jpg",
    "timestamps_file": "youtube_timestamps_incubus_system_101_150.txt",
    "subtitles_file": "subtitles_incubus_system_101_150.srt",
    "payload_file": "youtube_upload_payload_incubus_system_101_150.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE INCUBUS SYSTEM [Chapters 101-150] | Urban Fantasy Harem & System LitRPG Audiobook",
    "tags": [
        "The Incubus System", "Urban Fantasy Audiobook", "Harem LitRPG", "System Progression Novel",
        "Ethan Strongheart", "Damian High Incubus", "Succubus Lilieth", "Demon Hunter Ruby", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Incubus System' (Part 3), covering Chapters 101 through 150!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/n6gAvCC1ZaA\n\n"
        "Trapped in a midair duel with Demon Hunter Ruby inside his Devil Space, Ethan Strongheart's High Incubus persona Damian "
        "is suddenly thrust into a breach from the Dark Dimension—teaming up with Royal Succubus Lilieth and Demon General Sarael "
        "as escalating demonic threats, hunter conspiracies, and new system evolutions collide!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK FANTASY & HAREM LITRPG MARATHONS ON BEING A BONG:\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n"
        "• Dual Cultivation: Gathering SSS-Rank Wives -> https://www.youtube.com/playlist?list=PLaEbSwNtKKOQ\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#TheIncubusSystem #UrbanFantasyAudiobook #HaremLitRPG #SystemProgression #EthanStrongheart #BeingABong"
    ),

    # 10 Textless 2D/2.5D Urban Dark Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (101, 105),
            "fallback_color": (16, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of winged High Incubus Damian hovering above moonlit ocean waves, "
                "summoning five levitating obsidian Demonic Spikes as white Holy Blasts collide with dark energy. "
                "UPPER-RIGHT BACKGROUND: Fierce red-haired Demon Hunter Ruby wielding a glowing white Holy Chain beside a shattering black dimensional rift. "
                "High-contrast crimson-violet, radiant-white, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (106, 110),
            "fallback_color": (22, 12, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy rift-battle book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Royal Succubus Lilieth projecting an arcane barrier over a black swamp alongside scarred Demon General Sarael "
                "holding a green-glowing skull that unleashes black flames across swarming monsters. "
                "UPPER-RIGHT & BACKGROUND: Ethan extending his hand to seal a fracturing portal between the Demon World and modern city skyline. "
                "High-contrast emerald-flame, abyssal-purple, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (111, 115),
            "fallback_color": (26, 16, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital modern-fantasy campus & double-life book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan Strongheart on a twilight university rooftop, "
                "glowing crimson incubus eyes reflecting off his dark jacket as he inspects a pink-glitter hunter smartphone and floating red system alerts. "
                "UPPER-RIGHT & BACKGROUND: Neon-lit modern city towers beneath swirling violet twilight clouds. "
                "High-contrast neon-magenta, twilight-blue, and warm-amber palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (116, 120),
            "fallback_color": (28, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Seductive dark-fantasy lounge scene with High Incubus Ethan seated beside alluring Royal Succubus Lilieth "
                "as shimmering rose-violet aura tendrils and translucent Incubus System stat windows float around them. "
                "UPPER-RIGHT SKY: Floor-to-ceiling penthouse glass overlooking a rain-slicked midnight metropolis. "
                "High-contrast rose-crimson, royal-violet, and gold-amber palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (121, 125),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-fantasy hunter-order confrontation book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Demon Hunter Ruby and elite holy-light squad investigating a scarred alleyway where black demonic lances are embedded in stone, "
                "holy barrier runes illuminating the mist. "
                "UPPER-RIGHT & BACKGROUND: Masked winged figure of Damian watching silently from a high Gothic clocktower gargoyle. "
                "High-contrast holy-gold, steel-blue, and shadow-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (126, 130),
            "fallback_color": (24, 14, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy Devil Space domain book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Ethan standing atop an obsidian bridge inside his crimson-sky Devil Space, unfurling dark bat-like wings "
                "as dozens of Demonic Spikes and Dark Energy spheres orbit his outstretched hands. "
                "UPPER-RIGHT & BACKGROUND: Calm mirror-like dark sea reflecting inverted floating ruins and crimson moons. "
                "High-contrast blood-crimson, obsidian-black, and electric-violet palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (131, 135),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-fantasy demon-noble ambush book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Damian clashing midair against a towering armored noble demon and monstrous hounds, "
                "crimson claws tearing through dark magic shockwaves. "
                "UPPER-RIGHT HORIZON: Shattered glass skyscrapers and emergency searchlights cutting through night fog. "
                "High-contrast infernal-orange, deep-violet, and slate-navy palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (136, 140),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy system evolution book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan absorbing swirling crimson-and-gold soul essence inside a glowing demonic magic circle, "
                "his High Incubus bloodline awakening with radiant runes across his chest and arms. "
                "UPPER-RIGHT SKY: Cascading translucent system skill-tree panels and spiraling dark-energy vortices. "
                "High-contrast crimson-gold, royal-purple, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (141, 145),
            "fallback_color": (26, 16, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-fantasy alliance & intrigue book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan standing between alluring succubus companion Lilieth and cautious Demon Hunter Ruby on a moonlit harbor pier, "
                "tense unspoken truce hanging in the mist between holy light and dark aura. "
                "UPPER-RIGHT & BACKGROUND: Harbor bridge lights shimmering across dark water under a crescent moon. "
                "High-contrast silver-cyan, rose-violet, and deep-navy palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (146, 150),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Demon-World-Ace ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: High Incubus Damian soaring high above a storm-lit metropolis with massive dark wings spread wide, "
                "commanding an armada of black Demonic Spikes as a colossal crimson rift pulses behind him. "
                "UPPER-RIGHT HORIZON: Dawn light breaking over city spires as demonic shadows retreat into the sky. "
                "High-contrast crimson-gold, abyssal-violet, and twilight-blue palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))