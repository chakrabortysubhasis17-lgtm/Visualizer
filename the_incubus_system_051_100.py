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


BUILD_DIR = "build_the_incubus_system_051_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-incubus-system/chapter-51",
    "novel_slug": "the-incubus-system",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
    "default_topic": "The Incubus System: High Incubus Ascension",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 51 to 100 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Ethan / Damian Lucio)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Ethan",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"Another dimensional crack has opened near Diamond College... time to boost my intelligence, unlock Demonic Spike, and end this from the shadows!"',
            "tts_text": '"Another dimensional crack has opened near Diamond College... time to boost my intelligence, unlock Demonic Spike, and end this from the shadows!"',
            "text": '"Another dimensional crack has opened near Diamond College... time to boost my intelligence, unlock Demonic Spike, and end this from the shadows!"',
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
            "display_text": "Balancing quiet campus life with his secret identity as the Level 20 High Incubus Damian Lucio, Ethan spots Demon Hunters Emma Lunaspark and Theo Ragelight mobilizing over a fresh dimensional rift—forcing him to power up his dark arsenal and protect everyone from the shadows!",
            "tts_text": "Balancing quiet campus life with his secret identity as the Level 20 High Incubus Damian Loo-see-oh, Ethan spots Demon Hunters Emma Lunaspark and Theo Ragelight mobilizing over a fresh dimensional rift... forcing him to power up his dark arsenal and protect everyone from the shadows!",
            "text": "Balancing quiet campus life with his secret identity as the Level 20 High Incubus Damian Lucio, Ethan spots Demon Hunters Emma Lunaspark and Theo Ragelight mobilizing over a fresh dimensional rift—forcing him to power up his dark arsenal and protect everyone from the shadows!",
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
            "display_text": "Incubus System Decree: To gather Demonic Power and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. Between campus romance and dark dimension battles, only absolute mastery commands destiny.",
            "tts_text": "Incubus System Decree: To gather Demonic Power and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. Between campus romance and dark dimension battles, only absolute mastery commands destiny.",
            "text": "Incubus System Decree: To gather Demonic Power and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. Between campus romance and dark dimension battles, only absolute mastery commands destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of The Incubus System. Allocate your unused stat points, seal the dimensional cracks, and follow Ethan's double life in Nighthallow City.",
            "tts_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of The Incubus System. Allocate your unused stat points, seal the dimensional cracks, and follow Ethan's double life in Nighthallow City.",
            "text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of The Incubus System. Allocate your unused stat points, seal the dimensional cracks, and follow Ethan's double life in Nighthallow City.",
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
    "final_audio": "output_the_incubus_system_051_100.mp3",
    "final_video": "final_the_incubus_system_051_100.mp4",
    "cover_image": "cover_the_incubus_system_051_100.jpg",
    "timestamps_file": "youtube_timestamps_the_incubus_system_051_100.txt",
    "subtitles_file": "subtitles_the_incubus_system_051_100.srt",
    "payload_file": "youtube_upload_payload_the_incubus_system_051_100.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE INCUBUS SYSTEM! [Chapters 51-100] | Urban Fantasy Progression Full Audiobook",
    "tags": [
        "The Incubus System", "The Incubus System Audiobook", "Ethan", "Damian Lucio",
        "Urban Fantasy Audiobook", "System Novel", "Nighthallow City", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'The Incubus System' (Part 2), covering Chapters 51 through 100!\n\n"
        "After strengthening his bond with Olivia at Diamond College, Ethan spots Demon Hunters Emma Lunaspark and Theo Ragelight "
        "reacting to a Demon Compass alert in the cafeteria. Investing 48 stat points into Intelligence and unlocking Demonic Spike "
        "and Dark Energy, Ethan prepares to intervene as his masked alter ego Damian Lucio!\n\n"
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
        "#TheIncubusSystem #UrbanFantasy #ProgressionFantasy #DamianLucio #Audiobook #BeingABong"
    ),

    # 10 Textless 2D/2.5D Urban Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (51, 55),
            "fallback_color": (18, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of brown-haired college student Ethan sitting by a sunlit Diamond College cafeteria window with a coffee cup, "
                "eyes glowing faintly with violet Observation aura as translucent blue RPG stat windows float beside him. "
                "UPPER-RIGHT BACKGROUND: Through the glass window, an elegant silver-haired elf hunter and a stern young man examine a glowing brass Demon Compass on a campus bench. "
                "High-contrast mystic-violet, warm-amber, and slate-blue palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (56, 60),
            "fallback_color": (22, 12, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-urban fantasy book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Masked High Incubus Damian Lucio hovering in a shadowy Nighthallow City alleyway at dusk, "
                "summoning ten razor-sharp black Demonic Spike lances crackling with dark purple energy behind his shoulders. "
                "UPPER-RIGHT & BACKGROUND: A jagged spatial dimensional crack tearing open in midair, leaking crimson-violet mist over brick rooftops. "
                "High-contrast obsidian-black, electric-violet, and crimson-glow palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "fallback_color": (14, 22, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital supernatural action book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Damian Lucio channeling pure Dark Energy from his clawed palm to stitch shut a glowing dimensional rift, "
                "violet lightning arcing across his dark coat as system mastery notifications shimmer in the air. "
                "UPPER-RIGHT & BACKGROUND: Nighthallow City skyscrapers and streetlamps bathed in eerie moonlight. "
                "High-contrast midnight-blue, neon-purple, and silver-cyan palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (66, 70),
            "fallback_color": (28, 16, 24),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking urban fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Elf Demon Hunter Emma Lunaspark conjuring glowing golden Holy Chains alongside a masked dark-cloaked ally in a moonlit plaza, "
                "emerald magic runes orbiting her hands. "
                "UPPER-RIGHT SKY: Swirling dark clouds over gothic university clocktowers at night. "
                "High-contrast celestial-gold, emerald-green, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (71, 75),
            "fallback_color": (20, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted modern campus romance and intrigue book-cover illustration in top-ranking webnovel art style, "
                "warm painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan walking along a tree-lined Diamond College courtyard at golden sunset with Olivia Creststream, "
                "warm autumn light filtering through maple leaves while subtle pink-violet charm motes drift in the breeze. "
                "UPPER-RIGHT & BACKGROUND: Classic red-brick university halls, arched stone walkways, and twilight clouds. "
                "High-contrast sunset-amber, rose-pink, and twilight-purple palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (76, 80),
            "fallback_color": (14, 24, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban mystery book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Ethan standing inside a sleek executive office overlooking Nighthallow City at night, "
                "conversing with a refined hybrid-beast woman while translucent system relationship panels glow softly. "
                "UPPER-RIGHT & BACKGROUND: Floor-to-ceiling glass windows revealing glittering metropolis lights and a crescent moon. "
                "High-contrast teal-cyan, warm-gold, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (81, 85),
            "fallback_color": (26, 14, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted supernatural battle book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and explosive magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Damian Lucio unleashing a bolt of crackling crimson-violet Hell Thunder from his fingertips across a rain-slicked rooftop, "
                "illuminating his dark demon form and glowing amber eyes. "
                "UPPER-RIGHT HORIZON: Stormy night sky split by purple lightning over industrial warehouses. "
                "High-contrast electric-magenta, crimson-red, and charcoal-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (86, 90),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted lakeside sanctuary book-cover illustration in top-ranking urban fantasy art style, "
                "dramatic perspective and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan standing on a wooden pier beside Green Lake in Ironshade Town under a star-filled night sky, "
                "surrounded by drifting blue spirit lights and calm water reflections. "
                "UPPER-RIGHT SKY: Twin constellations shining over distant misty hills and town lanterns. "
                "High-contrast sapphire-blue, silver-white, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (91, 95),
            "fallback_color": (30, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted demonic sanctum book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Damian Lucio opening a swirling Devil Space portal in a secluded penthouse chamber, "
                "violet-black dimensional energy framing his silhouette as ancient demonic artifacts levitate nearby. "
                "UPPER-RIGHT & BACKGROUND: Plush modern interior bathed in mystical amethyst light and moonlight. "
                "High-contrast amethyst-purple, celestial-gold, and dark-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (96, 100),
            "fallback_color": (32, 20, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic urban-overlord vista book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ethan standing atop a grand tower overlooking the Aeros Republic capital at dawn, "
                "subtle High Incubus aura shimmering around him as warm sunrise light breaks over the city skyline. "
                "UPPER-RIGHT HORIZON: Golden morning clouds, sparkling river bridges, and towering metropolis spires. "
                "High-contrast sunrise-gold, royal-purple, and twilight-blue palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
