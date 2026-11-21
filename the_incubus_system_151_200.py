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


BUILD_DIR = "build_incubus_system_151_200"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-incubus-system/chapter-151",
    "novel_slug": "the-incubus-system",
    "start_chapter": 151,
    "end_chapter": 200,
    "is_start": False,
    "default_topic": "The Incubus System",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 151 to 200 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Tiffany Duskblight)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Tiffany",
            "gender": "Female",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-3%",
            "pause_duration": 0.3,
            "display_text": '"Sorry for keeping you waiting—wait... Ethan?! What are you doing outside Theo\'s hospital room?!"',
            "tts_text": '"Sorry for keeping you waiting... wait... Ethan?! What are you doing outside Theo\'s hospital room?!"',
            "text": '"Sorry for keeping you waiting—wait... Ethan?! What are you doing outside Theo\'s hospital room?!"',
            "voice": "en-US-AvaMultilingualNeural",
            "pitch": "+1Hz",
            "sfx": "gasp",
            "bgm_mood": "intrigue"
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
            "display_text": "Accompanying Emma and Larry to Nighthallow City Hospital to check on Theo, Ethan Strongheart runs straight into his stepsister Tiffany Duskblight—uncovering a shocking Demon Hunter secret that threatens to expose his High Incubus double life across Chapters 151 to 200!",
            "tts_text": "Accompanying Emma and Larry to Nighthallow City Hospital to check on Theo, Ethan Strongheart runs straight into his stepsister Tiffany Duskblight... uncovering a shocking Demon Hunter secret that threatens to expose his High Incubus double life across Chapters 151 to 200!",
            "text": "Accompanying Emma and Larry to Nighthallow City Hospital to check on Theo, Ethan Strongheart runs straight into his stepsister Tiffany Duskblight—uncovering a shocking Demon Hunter secret that threatens to expose his High Incubus double life across Chapters 151 to 200!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "intrigue"
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
            "display_text": "High Incubus System Alert: To conceal Ethan's demonic aura and power this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
            "tts_text": "High Incubus System Alert: To conceal Ethan's demonic aura and power this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
            "text": "High Incubus System Alert: To conceal Ethan's demonic aura and power this fifty-chapter urban fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Demon World's new ace.",
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
            "display_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of The Incubus System. Step into Nighthallow City Hospital, navigate family secrets and hunter alliances, and witness Ethan balance shadow and desire.",
            "tts_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of The Incubus System. Step into Nighthallow City Hospital, navigate family secrets and hunter alliances, and witness Ethan balance shadow and desire.",
            "text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of The Incubus System. Step into Nighthallow City Hospital, navigate family secrets and hunter alliances, and witness Ethan balance shadow and desire.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "tension"
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
    "final_audio": "output_incubus_system_151_200.mp3",
    "final_video": "final_incubus_system_151_200.mp4",
    "cover_image": "cover_incubus_system_151_200.jpg",
    "timestamps_file": "youtube_timestamps_incubus_system_151_200.txt",
    "subtitles_file": "subtitles_incubus_system_151_200.srt",
    "payload_file": "youtube_upload_payload_incubus_system_151_200.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE INCUBUS SYSTEM [Chapters 151-200] | Urban Fantasy Harem & System LitRPG Audiobook",
    "tags": [
        "The Incubus System", "Urban Fantasy Audiobook", "Harem LitRPG", "System Progression Novel",
        "Ethan Strongheart", "Damian High Incubus", "Tiffany Duskblight", "Emma", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Incubus System' (Part 4), covering Chapters 151 through 200!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/n6gAvCC1ZaA\n\n"
        "After a chaotic ride from Diamond College with Emma and Larry, Ethan Strongheart arrives at Nighthallow City Hospital "
        "to visit Theo—only to come face-to-face with his stepsister Tiffany Duskblight and discover she is a trained Demon Hunter! "
        "As secrets collide between his civilian life, hunter allies, and High Incubus powers, new threats and relationships ignite "
        "across Chapters 151 through 200.\n\n"
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
            "range": (151, 155),
            "fallback_color": (16, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of Ethan Strongheart standing frozen in shock outside a sleek modern hospital corridor door, "
                "floating translucent Observation skill status panels glowing faintly beside red-haired stepsister Tiffany Duskblight in an unbuttoned white jacket. "
                "UPPER-RIGHT BACKGROUND: Elegant dark-haired Emma and grinning friend Larry standing down the glass-lined hallway. "
                "High-contrast twilight-cyan, rose-crimson, and midnight-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (156, 160),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital modern-fantasy intrigue book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan and gentle heiress Emma conversing quietly on a moonlit hospital terrace overlooking Nighthallow City, "
                "soft warm lantern light reflecting off their eyes as unspoken secrets linger between them. "
                "UPPER-RIGHT & BACKGROUND: Towering glass medical towers and distant neon city avenues under a starry night sky. "
                "High-contrast warm-amber, twilight-indigo, and silver-blue palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (161, 165),
            "fallback_color": (18, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy hunter-duel book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of red-haired Demon Hunter Tiffany wielding glowing golden Holy Chains and Holy Orbs "
                "in a rain-slicked alley as dark demonic shadows swirl across brick walls. "
                "UPPER-RIGHT & BACKGROUND: Winged silhouette of High Incubus Damian watching silently from a rooftop ledge above the mist. "
                "High-contrast holy-gold, abyssal-violet, and midnight-navy palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (166, 170),
            "fallback_color": (26, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Seductive dark-fantasy penthouse scene with Ethan and Royal Succubus Lilieth analyzing glowing crimson Incubus System skill trees "
                "while dark arcane energy spirals gently around their hands. "
                "UPPER-RIGHT SKY: Floor-to-ceiling windows overlooking a neon-lit midnight metropolis pierced by distant violet lightning. "
                "High-contrast crimson-rose, royal-violet, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (171, 175),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-fantasy campus & double-life book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan walking across the autumn courtyard of Diamond College flanked by tomboyish Olivia, gentle Emma, and red-haired Tiffany, "
                "subtle crimson demonic runes glinting faintly in his eyes. "
                "UPPER-RIGHT & BACKGROUND: Grand gothic-modern university clocktower framed by golden afternoon clouds. "
                "High-contrast autumn-gold, sapphire-blue, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (176, 180),
            "fallback_color": (22, 12, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy dimensional-breach book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Winged High Incubus Damian soaring midair before a shattering black dimensional crack above Nighthallow Harbor, "
                "hurling dozens of obsidian Demonic Spikes into a horde of emerging abyssal monsters. "
                "UPPER-RIGHT & BACKGROUND: Dark storm clouds torn open by crimson-violet portal energy over crashing waves. "
                "High-contrast electric-violet, blood-crimson, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (181, 185),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-fantasy Devil Space domain book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan standing atop an obsidian bridge inside his crimson-moon Devil Space, "
                "channeling swirling Dark Energy spheres as translucent system level-up windows shimmer beside him. "
                "UPPER-RIGHT HORIZON: Calm mirror-black ocean reflecting inverted floating ruins and twin scarlet moons. "
                "High-contrast scarlet-crimson, abyssal-purple, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (186, 190),
            "fallback_color": (24, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy noble-demon showdown book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Damian clashing midair against a towering armored Demon Noble amidst swirling black flames and crimson lightning, "
                "demonic wings flared wide as shockwaves shatter nearby warehouse rooftops. "
                "UPPER-RIGHT SKY: Emergency searchlights and arcane barrier domes illuminating the night sky. "
                "High-contrast infernal-crimson, royal-purple, and charcoal-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (191, 195),
            "fallback_color": (26, 16, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-fantasy bloodline-awakening book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan kneeling inside a luminous crimson-and-gold demonic magic circle as his High Incubus bloodline evolves, "
                "radiant runes surging across his skin while swirling soul essence spirals upward. "
                "UPPER-RIGHT & BACKGROUND: Shadowed sanctuary pillars and floating golden-violet system notifications. "
                "High-contrast molten-gold, rose-crimson, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (196, 200),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic High-Incubus-sovereign book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: High Incubus Damian standing atop a high Gothic spire overlooking Nighthallow City at dawn with dark wings unfurled, "
                "glowing crimson eyes surveying the metropolis as faint shadow tendrils fade into the morning mist. "
                "UPPER-RIGHT HORIZON: Golden sunrise breaking through parting storm clouds over gleaming skyscrapers. "
                "High-contrast sunrise-gold, crimson-violet, and twilight-blue palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
