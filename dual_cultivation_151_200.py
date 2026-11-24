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


BUILD_DIR = "build_dual_cultivation_151_200"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world/chapter-151",
    "novel_slug": "dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world",
    "start_chapter": 151,
    "end_chapter": 200,
    "is_start": False,
    "default_topic": "Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 151 to 200)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Emperor Tianlong)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Emperor Tianlong",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "amused_commanding",
            "age_category": "adult",
            "display_text": '"I came here to deliver invitations to my royal marriage, Zhao Chen. Even with your Peak Core Formation breakthrough, your fate and your allies already belong in the palm of my hand!"',
            "tts_text": '"I came here to deliver invitations to my royal marriage, Zhao Chen. Even with your Peak Core Formation breakthrough... your fate and your allies already belong in the palm of my hand!"',
            "text": '"I came here to deliver invitations to my royal marriage, Zhao Chen. Even with your Peak Core Formation breakthrough, your fate and your allies already belong in the palm of my hand!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "whoosh",
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
            "display_text": "As Son of Heaven Zhao Chen achieves a hollow breakthrough to Peak Core Formation, Emperor Tianlong arrives with royal marriage invitations—turning scheming beauty Yu Xiang's calculations upside down and igniting a fifty-chapter storm of cultivation rivalry, fortune siphoning, and imperial conquest!",
            "tts_text": "As Son of Heaven Zhao Chen achieves a hollow breakthrough to Peak Core Formation, Emperor Tianlong arrives with royal marriage invitations... turning scheming beauty Yu Xiang's calculations upside down and igniting a fifty-chapter storm of cultivation rivalry, fortune siphoning, and imperial conquest!",
            "text": "As Son of Heaven Zhao Chen achieves a hollow breakthrough to Peak Core Formation, Emperor Tianlong arrives with royal marriage invitations—turning scheming beauty Yu Xiang's calculations upside down and igniting a fifty-chapter storm of cultivation rivalry, fortune siphoning, and imperial conquest!",
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
            "display_text": "Imperial System Decree: To gather heavenly fortune and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. Every tribute strengthens the Emperor's domain.",
            "tts_text": "Imperial System Decree: To gather heavenly fortune and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. Every tribute strengthens the Emperor's domain.",
            "text": "Imperial System Decree: To gather heavenly fortune and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. Every tribute strengthens the Emperor's domain.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "conversational_mid",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "chime",
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
            "display_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Step into the imperial court, outmaneuver the Sons of Heaven, and witness Emperor Tianlong's grand wedding.",
            "tts_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Dual Cultivation: Gathering triple-S-Rank Wives in the Cultivation World. Step into the imperial court, outmaneuver the Sons of Heaven, and witness Emperor Tianlong's grand wedding.",
            "text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Step into the imperial court, outmaneuver the Sons of Heaven, and witness Emperor Tianlong's grand wedding.",
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
    "final_audio": "output_dual_cultivation_151_200.mp3",
    "final_video": "final_dual_cultivation_151_200.mp4",
    "cover_image": "cover_dual_cultivation_151_200.jpg",
    "timestamps_file": "youtube_timestamps_dual_cultivation_151_200.txt",
    "subtitles_file": "subtitles_dual_cultivation_151_200.srt",
    "payload_file": "youtube_upload_payload_dual_cultivation_151_200.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUAL CULTIVATION: GATHERING SSS-RANK WIVES! [Chapters 151-200] | Villain Emperor LitRPG Audiobook",
    "tags": [
        "Dual Cultivation Gathering SSS-Rank Wives", "Dual Cultivation Audiobook", "SSS-Rank Wives LitRPG",
        "Villain Emperor Cultivation", "Emperor Tianlong", "Zhao Chen", "Yu Xiang", "Xuanhuan Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World!' (Part 4), covering Chapters 151 through 200!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLaEbSwNtKKOQ\n\n"
        "As Son of Heaven Zhao Chen stabilizes a hollow breakthrough to Peak Core Formation, crimson-eyed Emperor Tianlong "
        "arrives with royal marriage invitations that shatter Yu Xiang's calculations and siphon the protagonist's heavenly luck. "
        "From grand imperial wedding ceremonies to ruthless sect rivalries and SSS-rank bloodline awakenings, the Emperor's "
        "dominion expands across Chapters 151 through 200!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE VILLAIN & CULTIVATION SYSTEM MARATHONS ON BEING A BONG:\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• The Incubus System: Urban Fantasy Harem LitRPG -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DualCultivation #SSSRankWives #VillainEmperor #CultivationAudiobook #LitRPG #Xuanhuan #BeingABong"
    ),

    # 10 Textless 2D/2.5D Imperial Xuanhuan Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (151, 155),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital xuanhuan-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of crimson-eyed Emperor Tianlong in flowing dark-gold imperial silk robes "
                "holding a gilded royal wedding invitation with an amused smirk, standing beside poised violet-eyed beauty Yu Xiang in silver-and-violet court robes. "
                "UPPER-RIGHT BACKGROUND: Frustrated young cultivator Zhao Chen surrounded by fading golden Core Formation aura on a stone pavilion terrace. "
                "High-contrast imperial-crimson, molten-gold, and royal-violet palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (156, 160),
            "fallback_color": (26, 16, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital royal-wedding-palace book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and luminous lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Tianlong standing beneath towering vermilion palace pillars draped in crimson-and-gold ceremonial silk banners, "
                "flanked by two radiant SSS-rank brides—one wielding emerald spirit vines, the other radiating serene frost-blue aura. "
                "UPPER-RIGHT & BACKGROUND: Floating celestial lanterns and soaring spirit cranes above an endless imperial citadel. "
                "High-contrast ceremonial-crimson, sunrise-gold, and jade-violet palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (161, 165),
            "fallback_color": (16, 18, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital fortune-siphoning & system-interface book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Emperor Tianlong gazing at translucent golden-crimson system destiny panels "
                "as threads of golden protagonist luck flow from a distant horizon into his outstretched palm. "
                "UPPER-RIGHT & BACKGROUND: Starlit astral observatories and swirling dragon-vein qi currents over misty mountain peaks. "
                "High-contrast celestial-gold, crimson-violet, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (166, 170),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Violet-eyed strategist Yu Xiang standing by a moonlit lotus pond in an imperial courtyard, "
                "holding an ornate crimson wedding scroll while translucent system affinity rings shimmer faintly around her. "
                "UPPER-RIGHT SKY: Twin crescent moons reflecting across still palace waters and carved marble bridges. "
                "High-contrast amethyst-violet, silver-cyan, and warm-lantern-gold palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (171, 175),
            "fallback_color": (24, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted sect-summit-confrontation book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Tianlong seated effortlessly on a floating imperial palanquin above a grand martial arena, "
                "unleashing a wave of supreme crimson dragon pressure that forces rival sect elders and arrogant young masters to their knees. "
                "UPPER-RIGHT & BACKGROUND: Cloud-piercing sect pagodas and golden protective formations rippling in the sky. "
                "High-contrast imperial-gold, blood-crimson, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (176, 180),
            "fallback_color": (16, 22, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted spirit-realm-treasury book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Emperor Tianlong and his frost-maiden companion exploring an ancient subterranean spirit-vein vault, "
                "claiming a floating lotus of primordial dual-cultivation essence surrounded by crystalline ice pillars. "
                "UPPER-RIGHT & BACKGROUND: Glowing jade stalactites and ancient celestial runes etched into cavern walls. "
                "High-contrast glacial-cyan, emerald-jade, and royal-gold palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (181, 185),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted dual-cultivation-resonance book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Emperor Tianlong meditating inside a grand imperial cultivation chamber "
                "as twin spirals of golden solar qi and violet lunar essence intertwine into a radiant dragon-and-phoenix aura. "
                "UPPER-RIGHT HORIZON: Translucent SSS-rank system breakthrough windows illuminating incense-filled pavilion rafters. "
                "High-contrast solar-gold, lunar-violet, and crimson-silk palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (186, 190),
            "fallback_color": (22, 12, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted destiny-clash-duel book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Tianlong blocking a desperate full-power sword strike from Son of Heaven Zhao Chen with a single finger wreathed in crimson imperial lightning, "
                "shattering the ground beneath them into concentric shockwaves. "
                "UPPER-RIGHT SKY: Storm clouds torn open by a colossal phantom golden dragon roaring behind the Emperor. "
                "High-contrast crimson-lightning, molten-gold, and obsidian-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (191, 195),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted imperial-harem-pavilion book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Tianlong standing on a starlit sky-palace balcony surrounded by his loyal SSS-rank empresses in flowing ceremonial silks, "
                "gazing out over an illuminated immortal capital as golden destiny stars align overhead. "
                "UPPER-RIGHT & BACKGROUND: Floating heavenly palaces and cascading waterfalls of spiritual mist. "
                "High-contrast starlight-gold, royal-purple, and twilight-blue palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (196, 200),
            "fallback_color": (26, 16, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Heavenly-Emperor-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Tianlong standing atop the Imperial Dragon Altar at sunrise in crimson-and-gold sovereign robes, "
                "crimson eyes blazing with absolute authority as nine golden dragons coil around the heavens behind him. "
                "UPPER-RIGHT HORIZON: Brilliant dawn light breaking across endless immortal mountain ranges and sea of clouds. "
                "High-contrast sunrise-gold, imperial-crimson, and celestial-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
