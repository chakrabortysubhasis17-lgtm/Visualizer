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

BUILD_DIR = "build_cultivation_online_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/cultivation-online-novel/chapter-1",
    "novel_slug": "cultivation-online-novel",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Cultivation Online: Heaven Refining Physique",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Series Premiere - Chapters 1 to 50)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Mysterious Goddess Evaluator)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Mysterious Goddess",
            "gender": "Female",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"Heaven Refining Physique... and Soul Strength at the Spirit Warrior rank as a mortal? Take this token—do not lose it!"',
            "tts_text": '"Heaven Refining Fiz-eek... and Soul Strength at the Spirit Warrior rank as a mortal? Take this token... do not lose it!"',
            "text": '"Heaven Refining Physique... and Soul Strength at the Spirit Warrior rank as a mortal? Take this token—do not lose it!"',
            "voice": "en-US-AvaMultilingualNeural",
            "pitch": "+0Hz",
            "sfx": "hum",
            "bgm_mood": "wonder"
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
            "display_text": "Blind since age seven and bedridden for five years, eighteen-year-old Yuan puts on a full-immersion VR helmet—only to shatter space during character evaluation and awaken a Celestial-ranked physique beyond the four known ranks of the cultivation world!",
            "tts_text": "Blind since age seven and bedridden for five years, eighteen-year-old Yoo-ahn puts on a full-immersion V-R helmet... only to shatter space during character evaluation and awaken a Celestial-ranked fiz-eek beyond the four known ranks of the cultivation world!",
            "text": "Blind since age seven and bedridden for five years, eighteen-year-old Yuan puts on a full-immersion VR helmet—only to shatter space during character evaluation and awaken a Celestial-ranked physique beyond the four known ranks of the cultivation world!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "wonder"
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
            "display_text": "Heavenly Continent Decree: To temper your Spirit Qi and support this brand-new fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of immortality, only the strong command their fate.",
            "tts_text": "Heavenly Continent Decree: To temper your Spirit Chee and support this brand-new fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of immortality, only the strong command their fate.",
            "text": "Heavenly Continent Decree: To temper your Spirit Qi and support this brand-new fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of immortality, only the strong command their fate.",
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
        # Beat 4: Series Launch Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Cultivation Online. Step into the Eastern Continent, awaken your physique, and let the journey of a peerless prodigy begin.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Cultivation Online. Step into the Eastern Continent, awaken your fiz-eek, and let the journey of a peerless prodigy begin.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Cultivation Online. Step into the Eastern Continent, awaken your physique, and let the journey of a peerless prodigy begin.",
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
    "final_audio": "output_cultivation_online_001_050.mp3",
    "final_video": "final_cultivation_online_001_050.mp4",
    "cover_image": "cover_cultivation_online_001_050.jpg",
    "timestamps_file": "youtube_timestamps_cultivation_online_001_050.txt",
    "subtitles_file": "subtitles_cultivation_online_001_050.srt",
    "payload_file": "youtube_upload_payload_cultivation_online_001_050.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "CULTIVATION ONLINE: HEAVEN REFINING PHYSIQUE! [Chapters 1-50] | VRMMORPG Xianxia Audiobook",
    "tags": [
        "Cultivation Online", "Yuan", "VRMMORPG", "Xianxia Audiobook",
        "Progression Fantasy", "Cultivation Novel", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Cultivation Online', covering Chapters 1 through 50!\n\n"
        "Blind since childhood and crippled for five years, eighteen-year-old Yuan enters the world's first "
        "100% full-immersion VRMMORPG thanks to his devoted younger sister. Inside the evaluation void, his "
        "extraordinary Soul Strength and Celestial-ranked Heaven Refining Physique shock an otherworldly goddess—"
        "launching his rise across the Eastern Continent.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#CultivationOnline #Xianxia #VRMMORPG #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # 10 Textless 2D/2.5D Xianxia Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (16, 18, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital fantasy book-cover illustration in top-ranking VRMMORPG LitRPG webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND RIGHT: Dynamic three-quarter shot of eighteen-year-old Yuan standing inside a pitch-black starless void, looking down in emotional awe at his glowing hands "
                "as golden-cyan neural immersion threads dissolve the shadows around his crisp white cultivator robes. "
                "UPPER-LEFT SKY: Floating translucent sapphire-blue countdown runes and luminous ethereal interface ribbons spiraling through the dark abyss. "
                "High-contrast midnight-indigo, ethereal cyan, and warm starlight-gold color palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (28, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in top-ranking progression fantasy art style, "
                "rich painterly brushwork and dramatic chiaroscuro lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-RIGHT FOREGROUND: Peerless otherworldly Goddess Evaluator stepping out of a jagged spatial tear ripped open in a luminous white void, "
                "dressed in flowing crimson-and-gold imperial silk robes, piercing golden eyes wide with shock as she holds a blazing crystal evaluation orb radiating celestial-violet light. "
                "LEFT MIDGROUND: Young dark-haired Yuan stepping back in surprise as an emerald-jade medallion arcs through the air trailing golden Spirit Qi sparks. "
                "High-contrast crimson-gold, celestial-violet, and luminous ivory palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (18, 28, 42),
            "prompt": (
                "Masterpiece 2D/2.5D painted epic Xianxia landscape book-cover illustration in classic cultivation novel art style, "
                "sweeping atmospheric brushwork and dramatic high-angle vista, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "UPPER-LEFT FOREGROUND: Elderly white-bearded Immortal Elder Song in flowing azure robes hovering effortlessly above the clouds atop a gleaming spirit longsword, "
                "waving his wide sleeves to unleash thousands of glowing golden talismans into the sky. "
                "LOWER-RIGHT & BACKGROUND: Massive white-marble celestial arena on Mountain 96 floating above a sea of sunlit golden clouds, surrounded by towering floating peaks and waterfalls. "
                "High-contrast azure-blue, sunlit-gold, and cloud-white palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (20, 22, 38),
            "prompt": (
                "Masterpiece sharp anime-manhwa digital fantasy book-cover illustration in top-ranking LitRPG cultivation style, "
                "bold ink linework, vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Three-quarter action pose of Yuan sitting cross-legged in the lotus position on white marble, eyes blazing with golden Spirit Qi "
                "as a massive, roaring vortex of five-colored elemental Qi spirals violently into his chest, eclipsing the astonished crowd of white-robed initiates behind him. "
                "RIGHT & BACKGROUND: Four colossal elemental spatial portals—crimson flame, glacial blue, emerald wind, and golden earth—towering at the edge of the cloud platform. "
                "High-contrast elemental-gold, deep-indigo, and emerald palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (14, 30, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted fantasy book-cover illustration in luminous Royal Road / Kindle Xianxia art style, "
                "delicate hand-painted foliage and volumetric moonbeams, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "RIGHT-SIDE FOREGROUND: Over-the-shoulder three-quarter view of Yuan in white-and-emerald cultivator robes standing on an ancient moss-covered stone root on the Eastern Continent, "
                "gazing out across an endless primeval spirit forest bathed in silver-blue moonlight. "
                "LEFT & MIDGROUND: Bioluminescent spirit herbs glowing along a misty forest stream, giant ancient spirit trees piercing the canopy, and drifting emerald Qi fireflies. "
                "High-contrast emerald-green, moonlight-silver, and deep-forest teal palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (30, 18, 18),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking monster-hunting LitRPG style, "
                "dynamic Dutch-angle combat composition and explosive brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Yuan lunging diagonally across a shattered forest clearing, swinging a gleaming spirit-steel sword in a blinding crescent arc of golden-cyan Qi energy. "
                "RIGHT & UPPER SWEEP: A colossal, armored Shadow-Flame Spirit Tiger lunging out of the dark mist with bared fangs and blazing amber eyes, "
                "clashing head-on against Yuan's sword wave amidst flying splinters and sparks. "
                "High-contrast molten-amber, cyan-steel, and midnight-shadow palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (26, 20, 16),
            "prompt": (
                "Masterpiece 2D/2.5D painted Xianxia city-pavilion book-cover illustration in classic cultivation webnovel art style, "
                "rich architectural brushwork and warm lantern-lit contrast, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "LEFT & MIDGROUND VISTA: Grand multi-tiered Eastern Continent cultivation city carved into tiered jade cliffs, bustling stone bridges over misty waterfalls, "
                "and an ornate golden Treasure Pavilion glowing with warm amber spirit lanterns at twilight. "
                "RIGHT FOREGROUND: Mysterious veiled spirit-beast companion perched on a carved jade lantern post overlooking the lively cultivator streets below. "
                "High-contrast lantern-amber, jade-green, and twilight-violet palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (22, 16, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted sword-cultivation book-cover illustration in top-ranking progression fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp painterly energy streaks, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-RIGHT FOREGROUND: Fierce three-quarter waist-up pose of Yuan gripping his spirit sword with both hands, dark hair whipping in a gale of pure Sword Intent "
                "as dozens of translucent golden-white phantom spirit blades manifest in the sky behind his outstretched blade. "
                "LEFT BACKGROUND: Jagged bamboo-covered mountain peaks shrouded in swirling storm clouds and streaks of silver sword-light. "
                "High-contrast celestial-gold, storm-slate, and crisp-ivory palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (28, 16, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark Xianxia duel book-cover illustration in high-end cultivation novel art style, "
                "intense dramatic rim lighting and dynamic diagonal clash, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "LEFT FOREGROUND: Arrogant young sect prodigy in ornate crimson-and-black brocade robes unleashing a roaring serpent of dark blood-fire from a jade fan. "
                "RIGHT FOREGROUND: Calm, unyielding Yuan stepping forward through the heatwave, deflecting the flames effortlessly with a single palm strike radiating pure celestial-gold Heaven Refining Qi. "
                "High-contrast crimson-fire, pure-gold, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (24, 18, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Xianxia breakthrough book-cover illustration in top-ranking cultivation art style, "
                "grand vertical composition and luminous celestial brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "RIGHT-THIRD FOREGROUND: Yuan levitating above a cracked mountain peak at dawn, bathed in swirling golden-white Celestial Physique flames and crystalline soul-light "
                "as he breaks through into the Spirit Warrior realm, holding the ancient red-and-gold jade token aloft. "
                "LEFT & UPPER SKY: Colossal violet-and-gold heavenly tribulation clouds parting to reveal a beam of dawn sunlight illuminating misty waterfalls and distant sect pagodas. "
                "High-contrast celestial-gold, royal-violet, and dawn-crimson palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
