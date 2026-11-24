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


BUILD_DIR = "build_incubus_system_201_250"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-incubus-system/chapter-201",
    "novel_slug": "the-incubus-system",
    "start_chapter": 201,
    "end_chapter": 250,
    "is_start": False,
    "default_topic": "The Incubus System",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 201 to 250)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Damian / Ethan)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Damian",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "protective_reassuring",
            "age_category": "young",
            "display_text": '"Don\'t be afraid, Celia. Give me your loyalty under Demon\'s Rule, and I\'ll make sure no demon in this world ever lays a finger on you!"',
            "tts_text": '"Don\'t be afraid, Celia. Give me your loyalty under Demon\'s Rule... and I\'ll make sure no demon in this world ever lays a finger on you!"',
            "text": '"Don\'t be afraid, Celia. Give me your loyalty under Demon\'s Rule, and I\'ll make sure no demon in this world ever lays a finger on you!"',
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
            "display_text": "Sealing his Demon's Rule contract with his sister Celia Strongheart and unexpectedly awakening her Shadow Needle skill, Ethan uncovers mysterious dual-element magic hidden within those closest to him—navigating escalating demon incursions, hunter investigations, and high-stakes alliances across Chapters 201 through 250!",
            "tts_text": "Sealing his Demon's Rule contract with his sister Celia Strongheart and unexpectedly awakening her Shadow Needle skill, Ethan uncovers mysterious dual element magic hidden within those closest to him... navigating escalating demon incursions, hunter investigations, and high stakes alliances across Chapters 201 through 250!",
            "text": "Sealing his Demon's Rule contract with his sister Celia Strongheart and unexpectedly awakening her Shadow Needle skill, Ethan uncovers mysterious dual-element magic hidden within those closest to him—navigating escalating demon incursions, hunter investigations, and high-stakes alliances across Chapters 201 through 250!",
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
            "display_text": "Your immersion resumes now, covering Chapter 201 through Chapter 250 of The Incubus System. Witness the awakening of Shadow Needle, protect Nighthallow City from demonic breaches, and follow Ethan's ascent.",
            "tts_text": "Your immersion resumes now, covering Chapter 201 through Chapter 250 of The Incubus System. Witness the awakening of Shadow Needle, protect Nighthallow City from demonic breaches, and follow Ethan's ascent.",
            "text": "Your immersion resumes now, covering Chapter 201 through Chapter 250 of The Incubus System. Witness the awakening of Shadow Needle, protect Nighthallow City from demonic breaches, and follow Ethan's ascent.",
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
    "final_audio": "output_incubus_system_201_250.mp3",
    "final_video": "final_incubus_system_201_250.mp4",
    "cover_image": "cover_incubus_system_201_250.jpg",
    "timestamps_file": "youtube_timestamps_incubus_system_201_250.txt",
    "subtitles_file": "subtitles_incubus_system_201_250.srt",
    "payload_file": "youtube_upload_payload_incubus_system_201_250.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE INCUBUS SYSTEM [Chapters 201-250] | Urban Fantasy Harem & System LitRPG Audiobook",
    "tags": [
        "The Incubus System", "Urban Fantasy Audiobook", "Harem LitRPG", "System Progression Novel",
        "Ethan Strongheart", "Damian High Incubus", "Celia Strongheart", "Foxy", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Incubus System' (Part 5), covering Chapters 201 through 250!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/n6gAvCC1ZaA\n\n"
        "To shield his sister Celia Strongheart from worsening demon attacks, Ethan initiates Demon's Rule—sealing a loyal "
        "contract that unexpectedly boosts her strength by sixty percent and awakens her Shadow Needle skill! As Ethan investigates "
        "the dual-element mystery inside Celia while Foxy keeps watch, new demon breaches, hunter confrontations, and system "
        "evolutions unfold across Chapters 201 through 250.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
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
            "range": (201, 205),
            "fallback_color": (18, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of crimson-eyed Ethan Strongheart standing in a sunlit modern apartment living room "
                "halting five levitating black Shadow Needles midair with telekinesis as his surprised dark-haired sister Celia Strongheart looks at her glowing hands. "
                "UPPER-RIGHT BACKGROUND: Cute fox-eared companion Foxy peeking around the dining table beside a morning wall clock. "
                "High-contrast crimson-violet, shadow-black, and warm-morning-gold palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (206, 210),
            "fallback_color": (24, 14, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dual-element-mystery book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan using Observation skill as translucent crimson system panels reveal twin swirling currents of dark shadow energy "
                "and luminous silver-blue magic harmonizing inside Celia's aura. "
                "UPPER-RIGHT & BACKGROUND: Modern Nighthallow City skyline seen through tall apartment windows under drifting twilight clouds. "
                "High-contrast royal-violet, silver-cyan, and scarlet-crimson palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (211, 215),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital campus-and-hunter-intrigue book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan walking along a tree-lined university avenue alongside elegant heiress Emma "
                "and sharp-eyed red-haired Demon Hunter Tiffany Duskblight, subtle golden and crimson magic sigils reflecting in glass windows. "
                "UPPER-RIGHT & BACKGROUND: Classic stone towers of Diamond College framed by crisp autumn sky. "
                "High-contrast sapphire-blue, autumn-gold, and crimson-slate palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (216, 220),
            "fallback_color": (22, 12, 28),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Winged High Incubus Damian soaring above a neon-lit harbor warehouse district at midnight, "
                "commanding an array of obsidian Demonic Spikes as a jagged dimensional rift tears open in the clouds. "
                "UPPER-RIGHT SKY: Swarming abyssal silhouettes descending through purple lightning over dark ocean waves. "
                "High-contrast electric-violet, blood-crimson, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (221, 225),
            "fallback_color": (26, 16, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted succubus-alliance book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan conversing with alluring Royal Succubus Lilieth inside a candle-lit arcane sanctum, "
                "floating crimson-and-gold Incubus System skill trees and dimensional map runes glowing between them. "
                "UPPER-RIGHT & BACKGROUND: Stained-glass Gothic arches overlooking a storm-swept metropolis. "
                "High-contrast rose-crimson, imperial-gold, and abyssal-purple palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (226, 230),
            "fallback_color": (16, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted hunter-and-demon-clash book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Red-haired Demon Hunter Ruby and Tiffany unleashing radiant white Holy Chains and golden Holy Orbs in a rain-drenched plaza, "
                "while masked winged figure Damian deflects incoming demon-beast claws from above. "
                "UPPER-RIGHT & BACKGROUND: Shattered streetlamps and glowing holy barrier runes cutting through midnight fog. "
                "High-contrast holy-gold, ice-cyan, and deep-navy palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (231, 235),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted Devil-Space-training book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ethan standing on an obsidian bridge inside his crimson-sky Devil Space, "
                "channeling swirling Dark Energy spheres and Telekinesis rings as dozens of black lances orbit around him. "
                "UPPER-RIGHT HORIZON: Mirror-still dark sea reflecting inverted floating ruins and a giant scarlet moon. "
                "High-contrast scarlet-crimson, royal-violet, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (236, 240),
            "fallback_color": (24, 12, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted demon-general-skirmish book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: High Incubus Damian clashing midair against a towering armored Demon Noble amidst emerald hellfire and dark lightning, "
                "black bat-like wings flared wide as shockwaves shatter nearby skyscraper glass. "
                "UPPER-RIGHT SKY: Emergency searchlights and swirling dimensional vortex clouds above Nighthallow City. "
                "High-contrast emerald-flame, blood-crimson, and charcoal-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (241, 245),
            "fallback_color": (26, 16, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted bloodline-resonance & loyalty-pact book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan standing inside a luminous crimson-and-violet demonic magic circle as his High Incubus rank advances, "
                "radiant runes pulsing across his outstretched palms while translucent level-up panels gleam beside him. "
                "UPPER-RIGHT & BACKGROUND: Moonlit penthouse terrace overlooking shimmering city avenues. "
                "High-contrast molten-gold, rose-violet, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (246, 250),
            "fallback_color": (18, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic High-Incubus-dominion book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: High Incubus Damian perched atop a high Gothic cathedral spire overlooking Nighthallow City at dawn with dark wings spread wide, "
                "glowing crimson eyes surveying the horizon as faint shadow tendrils dissipate into morning light. "
                "UPPER-RIGHT HORIZON: Golden sunrise breaking through parting storm clouds over gleaming metropolitan towers. "
                "High-contrast sunrise-gold, crimson-violet, and twilight-blue palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
