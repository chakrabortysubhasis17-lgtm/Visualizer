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
                if len(rows) < 8 or any("Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", "")) for r in rows):
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

BUILD_DIR = "build_invincible_081_120"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/invincible-novel/chapter-81",
    "novel_slug": "invincible-novel",
    "start_chapter": 81,
    "end_chapter": 120,
    "is_start": False,
    "default_topic": "Invincible: Twin Supreme Martial Spirits",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 81 to 120 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Rival Prodigy",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+2%",
            "pause_duration": 0.3,
            "display_text": '"Impossible! Twin supreme martial spirits... and that suffocating Asura killing intent—who exactly are you?!"',
            "tts_text": '"Impossible! Twin supreme martial spirits... and that suffocating Ah-soo-rah killing intent... who exactly are you?!"',
            "text": '"Impossible! Twin supreme martial spirits... and that suffocating Asura killing intent—who exactly are you?!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
            "bgm_mood": "battle"
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
            "display_text": "Armed with twin supreme two-headed dragon martial spirits and the ancient Asura Tactics, Huang Xiaolong storms into the royal capital—crushing arrogant nobles, refining divine spiritual elixirs, and shaking the foundations of the Martial Spirit World!",
            "tts_text": "Armed with twin supreme two-headed dragon martial spirits and the ancient Ah-soo-rah Tactics, Hwahng Shiao-long storms into the royal capital... crushing arrogant nobles, refining divine spiritual elixirs, and shaking the foundations of the Martial Spirit World!",
            "text": "Armed with twin supreme two-headed dragon martial spirits and the ancient Asura Tactics, Huang Xiaolong storms into the royal capital—crushing arrogant nobles, refining divine spiritual elixirs, and shaking the foundations of the Martial Spirit World!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "battle"
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
            "display_text": "Martial Spirit World Decree: To temper your Battle Qi and fuel this forty-chapter marathon, hit that Like button and subscribe to the channel. On the path of the invincible, only absolute strength commands destiny.",
            "tts_text": "Martial Spirit World Decree: To temper your Battle Chee and fuel this forty-chapter marathon, hit that Like button and subscribe to the channel. On the path of the invincible, only absolute strength commands destiny.",
            "text": "Martial Spirit World Decree: To temper your Battle Qi and fuel this forty-chapter marathon, hit that Like button and subscribe to the channel. On the path of the invincible, only absolute strength commands destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 81 through Chapter 120 of Invincible. Unleash your twin martial spirits, draw the Asura Blades, and witness Huang Xiaolong's unstoppable ascent.",
            "tts_text": "Your immersion resumes now, covering Chapter 81 through Chapter 120 of Invincible. Unleash your twin martial spirits, draw the Ah-soo-rah Blades, and witness Hwahng Shiao-long's unstoppable ascent.",
            "text": "Your immersion resumes now, covering Chapter 81 through Chapter 120 of Invincible. Unleash your twin martial spirits, draw the Asura Blades, and witness Huang Xiaolong's unstoppable ascent.",
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
    "final_audio": "output_invincible_081_120.mp3",
    "final_video": "final_invincible_081_120.mp4",
    "cover_image": "cover_invincible_081_120.jpg",
    "timestamps_file": "youtube_timestamps_invincible_081_120.txt",
    "subtitles_file": "subtitles_invincible_081_120.srt",
    "payload_file": "youtube_upload_payload_invincible_081_120.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "INVINCIBLE: TWIN SUPREME MARTIAL SPIRITS! [Chapters 81-120] | Xianxia Cultivation Audiobook",
    "tags": [
        "Invincible", "Invincible Audiobook", "Huang Xiaolong", "Xianxia Audiobook",
        "Progression Fantasy", "Cultivation Novel", "Martial Spirit World", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Invincible', covering Chapters 81 through 120!\n\n"
        "Awakening twin supreme two-headed dragon martial spirits and cultivating the forbidden Asura Tactics, "
        "Huang Xiaolong steps onto a grander stage in the Martial Spirit World—defeating royal prodigies, "
        "mastering divine alchemy, and uncovering ancient treasures that shock entire empires.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE XIANXIA & PROGRESSION MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#Invincible #Xianxia #ProgressionFantasy #CultivationAudiobook #HuangXiaolong #BeingABong"
    ),

    # 10 Textless 2D/2.5D Xianxia Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (81, 84),
            "fallback_color": (14, 24, 42),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in top-ranking Royal Road progression fantasy art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of young black-haired cultivator Huang Xiaolong on a jagged obsidian cliff edge, "
                "blazing golden eyes, dark gold-trimmed martial robes billowing as he raises one hand unleashing spiraling black lightning and sapphire battle Qi. "
                "UPPER-RIGHT SKY: Colossal spectral black and azure twin two-headed dragon-serpent spirits coiling through sunlit golden clouds and misty mountain peaks. "
                "High-contrast molten-gold, electric-sapphire, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (85, 88),
            "fallback_color": (22, 18, 38),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in top-ranking progression fantasy art style, "
                "rich painterly brushwork and dramatic chiaroscuro lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dynamic low-angle pose of Huang Xiaolong lunging across a cracked marble arena stage, black hair streaming, "
                "crimson-and-gold martial robes snapping as he grips twin dark-gold Asura blades unleashing a blazing scarlet-gold sword wave and violet lightning. "
                "UPPER-RIGHT & BACKGROUND: Towering phantom silhouette of a six-armed Asura Sovereign in crimson battle mist above ancient colosseum pillars and a burning sunset sky. "
                "High-contrast crimson-gold, royal-violet, and charcoal-slate palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (89, 92),
            "fallback_color": (12, 30, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in classic cultivation novel art style, "
                "sweeping atmospheric brushwork and luminous cel-shaded rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Huang Xiaolong inside a misty mountain alchemy pavilion, piercing golden eyes, "
                "dark jade-and-gold robes, extending both hands toward a levitating bronze pill furnace channeling emerald essence and liquid gold spiritual fire. "
                "UPPER-RIGHT & BACKGROUND: Bamboo silhouettes, glowing spirit lanterns, cascading celestial waterfalls, and tiered pagodas under an indigo starry sky. "
                "High-contrast jade-emerald, liquid-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (93, 96),
            "fallback_color": (28, 12, 24),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital Xianxia book-cover illustration in top-ranking progression fantasy style, "
                "bold ink linework, vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic midair shot of Huang Xiaolong hovering above glazed imperial palace rooftops at night, wind-whipped black hair, "
                "flowing black-and-scarlet Asura cloak, slashing a dark-gold sword to unleash a blazing crescent of crimson-and-black sword aura and embers. "
                "UPPER-RIGHT SKY: Stormy thunderclouds split by silver moonlight, glowing flying-sword trails, and royal capital spires. "
                "High-contrast scarlet, silver-cyan, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (97, 100),
            "fallback_color": (10, 26, 46),
            "prompt": (
                "Masterpiece 2D/2.5D painted fantasy book-cover illustration in luminous Royal Road Xianxia art style, "
                "delicate hand-painted brushwork and volumetric starlight, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Low-angle medium close-up of Huang Xiaolong seated in lotus meditation on a suspended jade boulder over a mirror-still spirit lake, "
                "eyes glowing celestial gold, concentric rings of golden meridian light and rising sapphire water droplets orbiting in a Qi vortex. "
                "UPPER-RIGHT & BACKGROUND: Floating twin mountain spires pierced by a colossal beam of starlight descending from a twilight cosmic sky. "
                "High-contrast celestial-gold, luminous-sapphire, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (101, 104),
            "fallback_color": (26, 20, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted subterranean Xianxia treasury book-cover illustration in top-ranking cultivation novel style, "
                "dramatic perspective and explosive brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Huang Xiaolong standing before colossal ancient bronze-and-obsidian treasury gates beneath a mountain, "
                "dark gold-trimmed robes bathed in golden vault light, raising a glowing palm wrapped in constellation runes amid floating spirit crystals. "
                "UPPER-RIGHT & BACKGROUND: Cavernous underground dome with dragon-carved stone pillars, suspended cyan spirit orbs, and radiant treasure rays. "
                "High-contrast molten-gold, electric-cyan, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (105, 108),
            "fallback_color": (36, 16, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted autumn Xianxia sword-sect book-cover illustration in classic cultivation webnovel art style, "
                "rich painterly foliage and warm golden-hour contrast, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dynamic three-quarter pose of Huang Xiaolong at a cliffside martial sect plaza framed by crimson maple trees, "
                "glowing autumn leaves drifting in foreground, dozens of translucent crimson-and-gold phantom swords orbiting his outstretched hand. "
                "UPPER-RIGHT HORIZON: Floating cloud-wrapped sect pavilions, jagged mountain peaks, and golden-hour sunbeams piercing amber clouds. "
                "High-contrast autumn-crimson, warm-amber, and deep-umber palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (109, 112),
            "fallback_color": (14, 20, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted heavenly tribulation book-cover illustration in top-ranking progression fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp painterly energy streaks, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Fierce upward action pose of Huang Xiaolong ascending into a raging tribulation storm, golden lightning in his eyes, "
                "dark armor wreathed in intertwined black and azure spectral dragon auras, thrusting a glowing fist shattering violet-gold lightning bolts. "
                "UPPER-RIGHT SKY: Swirling apocalyptic vortex of dark storm clouds and burning crimson lightning towering above royal academy spires. "
                "High-contrast electric-violet, blinding-gold, and storm-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (113, 116),
            "fallback_color": (18, 14, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted cosmic soul-sea Xianxia book-cover illustration in high-end cultivation novel art style, "
                "intense dramatic rim lighting and ethereal cosmic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Huang Xiaolong suspended inside an ethereal cosmic soul-sea realm, floating jet-black hair, dark-gold robes glowing with meridian starlight, "
                "channeling twin ribbons of incandescent crimson Asura flame and ice-blue soul energy past floating obsidian shards. "
                "UPPER-RIGHT & BACKGROUND: Towering luminous silhouette of an ancient Asura War God amidst floating jade spirit tablets, celestial pagodas, and star nebulae. "
                "High-contrast celestial-gold, crimson-magenta, and void-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (117, 120),
            "fallback_color": (30, 22, 16),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Xianxia dawn summit book-cover illustration in top-ranking cultivation art style, "
                "grand panoramic composition and luminous celestial brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Huang Xiaolong standing triumphantly at the highest peak of the Martial Spirit World at dawn, "
                "morning wind sweeping his black hair and gold-embroidered cloak, one hand resting on his Asura sword hilt beside a weathered jade sword monument. "
                "UPPER-RIGHT HORIZON: Endless ocean of sunrise-lit golden clouds, distant heavenly summits, and majestic twin dragon-serpent silhouettes soaring through dawn rays. "
                "High-contrast sunrise-gold, warm-ivory, and twilight-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
