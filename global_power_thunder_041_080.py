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


BUILD_DIR = "build_purple_sky_divine_thunder_41_80"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/global-power-awakening-of-the-purple-sky-divine-thunder-at-the-beginning/chapter-41-tan-mingyang-freshman-competition/",
    "novel_slug": "global-power-awakening-of-the-purple-sky-divine-thunder-at-the-beginning",
    "start_chapter": 41,
    "end_chapter": 80,
    "is_start": False,
    "default_topic": "Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 41 to 80 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Protagonist",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"You think an S-rank fire talent makes you untouchable in the Freshman Competition? Step onto the arena and see how your flames fare against the Purple Sky Divine Thunder!"',
            "tts_text": '"You think an S-rank fire talent makes you untouchable in the Freshman Competition? Step onto the arena... and see how your flames fare against the Purple Sky Divine Thunder!"',
            "text": '"You think an S-rank fire talent makes you untouchable in the Freshman Competition? Step onto the arena and see how your flames fare against the Purple Sky Divine Thunder!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch": "-1Hz",
            "sfx": "thunder",
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
            "display_text": "As the Freshman Competition erupts into fierce elemental clashes, the wielder of the supreme Purple Sky Divine Thunder faces down prodigies like Tan Mingyang—unleashing annihilating violet lightning that shakes the martial academy and pushes his global awakening into overdrive!",
            "tts_text": "As the Freshman Competition erupts into fierce elemental clashes, the wielder of the supreme Purple Sky Divine Thunder faces down prodigies like Tahn Ming-yahng... unleashing annihilating violet lightning that shakes the martial academy and pushes his global awakening into overdrive!",
            "text": "As the Freshman Competition erupts into fierce elemental clashes, the wielder of the supreme Purple Sky Divine Thunder faces down prodigies like Tan Mingyang—unleashing annihilating violet lightning that shakes the martial academy and pushes his global awakening into overdrive!",
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
            "display_text": "Divine Thunder Decree: To channel celestial tribulation lightning and power this forty-chapter awakening marathon, hit that Like button and subscribe to the channel. In an era of global superpowers, divine thunder reigns supreme.",
            "tts_text": "Divine Thunder Decree: To channel celestial tribulation lightning and power this forty-chapter awakening marathon, hit that Like button and subscribe to the channel. In an era of global superpowers, divine thunder reigns supreme.",
            "text": "Divine Thunder Decree: To channel celestial tribulation lightning and power this forty-chapter awakening marathon, hit that Like button and subscribe to the channel. In an era of global superpowers, divine thunder reigns supreme.",
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
            "display_text": "Your immersion resumes now, covering Chapter 41 through Chapter 80 of Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning. Step into the Freshman Competition, crush arrogant rivals, and witness the rise of the Purple Sky Sovereign.",
            "tts_text": "Your immersion resumes now, covering Chapter 41 through Chapter 80 of Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning. Step into the Freshman Competition, crush arrogant rivals, and witness the rise of the Purple Sky Sovereign.",
            "text": "Your immersion resumes now, covering Chapter 41 through Chapter 80 of Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning. Step into the Freshman Competition, crush arrogant rivals, and witness the rise of the Purple Sky Sovereign.",
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
    "final_audio": "output_purple_sky_divine_thunder_41_80.mp3",
    "final_video": "final_purple_sky_divine_thunder_41_80.mp4",
    "cover_image": "cover_purple_sky_divine_thunder_41_80.jpg",
    "timestamps_file": "youtube_timestamps_purple_sky_divine_thunder_41_80.txt",
    "subtitles_file": "subtitles_purple_sky_divine_thunder_41_80.srt",
    "payload_file": "youtube_upload_payload_purple_sky_divine_thunder_41_80.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "GLOBAL POWER: AWAKENING OF THE PURPLE SKY DIVINE THUNDER! [Chapters 41-80] | Urban Superpower LitRPG Audiobook",
    "tags": [
        "Global Power Awakening", "Purple Sky Divine Thunder", "Superpower Awakening Audiobook",
        "Urban Fantasy LitRPG", "Lightning Ability Novel", "Freshman Competition", "Tan Mingyang", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning' (Part 2), covering Chapters 41 through 80!\n\n"
        "In a world where spiritual energy has revived and awakened superpowers determine humanity's survival, the Freshman Competition "
        "becomes a proving ground of raw elemental might. Facing elite fire-wielding prodigies like Tan Mingyang, the inheritor of the "
        "SSS-tier Purple Sky Divine Thunder unleashes devastating violet tribulation lightning—shattering tournament records and "
        "attracting the gaze of hidden forces!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE INFINITE EVOLUTION & AWAKENING MARATHONS ON BEING A BONG:\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• Divine Kingdom: Awakening SSS-Talent -> https://www.youtube.com/playlist?list=PLELyNPaob7EA\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#GlobalPowerAwakening #PurpleSkyDivineThunder #SuperpowerAudiobook #LitRPG #UrbanFantasy #BeingABong"
    ),

    # 10 Textless 2D/2.5D Urban Superpower Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (41, 44),
            "fallback_color": (18, 12, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital urban-superpower book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of a young martial academy prodigy wreathed in crackling Purple Sky Divine Thunder, "
                "violet lightning arcing off his clenched fist as he steps onto a grand tournament arena. "
                "UPPER-RIGHT BACKGROUND: Rival cadet Tan Mingyang unleashing blazing crimson flames across a shattered stone combat stage. "
                "High-contrast electric-violet, infernal-crimson, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (45, 48),
            "fallback_color": (20, 14, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital arena-duel book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: A towering pillar of purple tribulation lightning crashing down from the stadium sky, "
                "obliterating a roaring wall of golden-red fire as shockwaves ripple across energy barriers. "
                "UPPER-RIGHT & BACKGROUND: Shocked academy instructors and thousands of spectators rising from tiered coliseum seats. "
                "High-contrast royal-purple, blinding-cyan, and ember-orange palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (49, 52),
            "fallback_color": (14, 18, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital academy-training & breakthrough book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up inside a gravity-enhanced thunder cultivation chamber, the protagonist meditating "
                "as violet lightning dragons coil around his body and floating translucent awakening system panels glow beside him. "
                "UPPER-RIGHT & BACKGROUND: High-tech steel walls scarred by scorch marks and pulsing spiritual energy conduits. "
                "High-contrast deep-violet, electric-blue, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (53, 56),
            "fallback_color": (22, 14, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic martial pose of the Purple Sky Thunder wielder standing alongside elite freshman teammates in sleek academy combat uniforms, "
                "violet lightning sparks dancing along his fingertips. "
                "UPPER-RIGHT SKY: Floating holographic tournament brackets and dramatic twilight storm clouds over a futuristic martial university. "
                "High-contrast neon-violet, silver-cyan, and twilight-navy palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (57, 60),
            "fallback_color": (16, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted wilderness-rift expedition book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The protagonist leaping through a monster-infested dimensional wilderness outside the city walls, "
                "cleaving a mutated beast in half with a blade of condensed purple divine thunder. "
                "UPPER-RIGHT & BACKGROUND: Towering ancient ruins, glowing dimensional rifts, and swirling storm clouds. "
                "High-contrast amethyst-purple, emerald-mist, and charcoal-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (61, 64),
            "fallback_color": (24, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted urban-night ambush book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: The protagonist standing calm on a rain-slicked city overpass surrounded by shadowed assassins, "
                "unleashing an omnidirectional web of purple lightning arcs that illuminates the dark street. "
                "UPPER-RIGHT & BACKGROUND: Neon skyscrapers, shattered streetlamps, and rain droplets frozen in midair by static charge. "
                "High-contrast electric-magenta, storm-violet, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (65, 68),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted secret-treasury & spirit-pool book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of the protagonist absorbing liquid lightning essence inside an ancient thunder-spirit pool, "
                "glowing violet runes surging across his skin and eyes. "
                "UPPER-RIGHT HORIZON: Crystalline cavern stalactites humming with pure spiritual energy. "
                "High-contrast celestial-violet, luminous-cyan, and deep-navy palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (69, 72),
            "fallback_color": (20, 12, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted inter-academy championship clash book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The protagonist soaring midair wrapped in a cloak of Purple Sky Divine Thunder, "
                "hurling a colossal purple lightning spear down toward an armored rival prodigy. "
                "UPPER-RIGHT SKY: Fractured energy domes and swirling thunderheads over a grand metropolitan stadium. "
                "High-contrast imperial-violet, lightning-white, and obsidian-blue palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (73, 76),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted dimensional-beast-tide defense book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The protagonist standing atop a fortified city bastion alongside awakened defenders, "
                "summoning a storm of purple sky thunderbolts down onto a surging horde of abyssal beasts. "
                "UPPER-RIGHT & BACKGROUND: Blazing artillery flares and crimson rift portals tearing open the horizon. "
                "High-contrast storm-purple, crimson-flare, and iron-slate palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (77, 80),
            "fallback_color": (18, 14, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic thunder-sovereign ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The protagonist standing victorious atop the highest spire of the martial academy at dawn, "
                "a colossal phantom avatar of the Purple Sky Divine Thunder materializing behind him in the clouds. "
                "UPPER-RIGHT HORIZON: Golden sunrise piercing through parting violet storm clouds over a sprawling awakened metropolis. "
                "High-contrast royal-violet, sunrise-gold, and celestial-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
