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


BUILD_DIR = "build_dual_cultivation_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world/chapter-1",
    "novel_slug": "dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 1 to 50 Premiere)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Zhao Tianlong)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Zhao Tianlong",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"Betrayed by my own son, poisoned in a rotting dungeon... but with the Harem Emperor System awakened, this old man refuses to die!"',
            "tts_text": '"Betrayed by my own son, poisoned in a rotting dungeon... but with the Harem Emperor System awakened, this old man refuses to die!"',
            "text": '"Betrayed by my own son, poisoned in a rotting dungeon... but with the Harem Emperor System awakened, this old man refuses to die!"',
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
            "display_text": "Reborn into the body of a dying deposed emperor of the Great Yan Dynasty, Zhao Tianlong defies his scheduled death, reclaims his vitality through intimate connections, and embarks on an epic journey to gather SSS-rank wives and crush his traitorous offspring!",
            "tts_text": "Reborn into the body of a dying deposed emperor of the Great Yan Dynasty, Zhao Tianlong defies his scheduled death, reclaims his vitality through intimate connections, and embarks on an epic journey to gather SSS-rank wives and crush his traitorous offspring!",
            "text": "Reborn into the body of a dying deposed emperor of the Great Yan Dynasty, Zhao Tianlong defies his scheduled death, reclaims his vitality through intimate connections, and embarks on an epic journey to gather SSS-rank wives and crush his traitorous offspring!",
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
            "display_text": "Harem Emperor Decree: To gather legendary SSS-rank wives and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, supreme power begins in the royal bedchamber.",
            "tts_text": "Harem Emperor Decree: To gather legendary SSS-rank wives and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, supreme power begins in the royal bedchamber.",
            "text": "Harem Emperor Decree: To gather legendary SSS-rank wives and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, supreme power begins in the royal bedchamber.",
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
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Step into the dark dungeon, awaken the system, and witness Zhao Tianlong's legendary comeback.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Step into the dark dungeon, awaken the system, and witness Zhao Tianlong's legendary comeback.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Step into the dark dungeon, awaken the system, and witness Zhao Tianlong's legendary comeback.",
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
    "final_audio": "output_dual_cultivation_001_050.mp3",
    "final_video": "final_dual_cultivation_001_050.mp4",
    "cover_image": "cover_dual_cultivation_001_050.jpg",
    "timestamps_file": "youtube_timestamps_dual_cultivation_001_050.txt",
    "subtitles_file": "subtitles_dual_cultivation_001_050.srt",
    "payload_file": "youtube_upload_payload_dual_cultivation_001_050.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUAL CULTIVATION: GATHERING SSS-RANK WIVES! [Chapters 1-50] | Xianxia Harem Progression Audiobook",
    "tags": [
        "Dual Cultivation", "Gathering SSS-Rank Wives", "Xianxia Audiobook", "Harem Progression Novel",
        "System Cultivation", "Zhao Tianlong", "Great Yan Dynasty", "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World' (Part 1), covering Chapters 1 through 50!\n\n"
        "Betrayed by his unfilial son and left to rot in a dark prison cell with sunset orchid poison eating away his life, "
        "former Great Yan Dynasty Emperor Zhao Tianlong awakens the Harem Emperor System! With vitality slipping away, "
        "he reunites with his loyal maid Mei Ling, initiates his legendary comeback, and begins gathering SSS-rank wives "
        "through the ancient art of dual cultivation.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE HAREM & CULTIVATION MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DualCultivation #SSSRankWives #XianxiaAudiobook #HaremProgression #CultivationNovel #BeingABong"
    ),

    # 10 Textless 2D/2.5D Xianxia Harem Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (28, 12, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of majestic older emperor Zhao Tianlong standing in a dimly lit stone dungeon cell with moldy straw, "
                "silver hair and piercing regal eyes, wearing tattered imperial dragon robes as a glowing translucent blue system screen floats before his hand. "
                "UPPER-RIGHT BACKGROUND: Heavy iron prison bars and flickering oil torchlight casting deep shadows against cracked stone walls. "
                "High-contrast imperial-gold, royal-crimson, and stone-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (18, 28, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia harem-progression book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Tender cinematic shot of loyal maid Mei Ling kneeling in prison straw before Zhao Tianlong, holding a wooden soup bowl, "
                "tears glistening in her eyes, wearing simple gray servant robes with graceful facial features and hidden Foundation Establishment Qi aura. "
                "UPPER-RIGHT & BACKGROUND: Stone archways, dripping water puddles, and soft warm lamplight illuminating the dark cell. "
                "High-contrast warm-amber, soft-jade, and charcoal-slate palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (24, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia palace-intrigue book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up inside a luxurious golden imperial bedchamber at dusk, Zhao Tianlong seated upon a carved dragon throne, "
                "youthful vitality returning to his features as floating system notification panels display Harem Points and vitality status. "
                "UPPER-RIGHT & BACKGROUND: Ornate silk curtains, burning sandalwood incense burners, and carved mahogany pillars under twilight moonlight. "
                "High-contrast molten-gold, royal-purple, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (14, 18, 36),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic action pose of Zhao Tianlong executing an ancient imperial palm strike, sending a shockwave of golden dragon Qi crashing through courtyard flagstones. "
                "UPPER-RIGHT SKY: Swirling purple-gold spiritual clouds above the grand imperial palace spires at night. "
                "High-contrast imperial-gold, vibrant-cyan, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (30, 14, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted dual-cultivation pavilion book-cover illustration in top-ranking progression webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Luminous spiritual pavilion surrounded by blooming lotus ponds, Zhao Tianlong meditating alongside a peerless female cultivator, "
                "interlocking palms as twin streams of golden and pink dual-cultivation Qi swirl upward in a glowing dragon-phoenix helix. "
                "UPPER-RIGHT & BACKGROUND: Misty mountain peaks, cascading waterfalls, and floating spiritual mist under a radiant sunrise. "
                "High-contrast lotus-pink, celestial-gold, and emerald-green palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (12, 24, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted imperial throne-room confrontation book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Zhao Tianlong standing proudly on the grand marble steps of the Great Yan dragon throne hall, pointing a golden sword down at rebellious traitor officials, "
                "eyes blazing with supreme imperial authority. "
                "UPPER-RIGHT & BACKGROUND: Massive golden dragon pillars, flying imperial guards, and stained glass windows casting colorful light across the hall. "
                "High-contrast dragon-gold, ruby-red, and obsidian palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (26, 20, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted secret alchemy chamber book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong refining spirit pills in a giant bronze cauldron, channeling pure fire Qi from his fingertips while exquisite female disciples watch in awe, "
                "pill fragrance swirling in golden smoke rings. "
                "UPPER-RIGHT HORIZON: Glowing spirit herbs arranged on jade shelves inside an ancient cavern under mystical starlight. "
                "High-contrast flame-orange, jade-green, and deep-umber palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (16, 24, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted celestial sect summit book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong standing atop a towering mountain peak overlooking rival sect masters, holding an ancient decree scroll that glows with blinding imperial light. "
                "UPPER-RIGHT SKY: Soaring divine cranes and swirling spiritual vortexes in the firmament above ancient sword monuments. "
                "High-contrast crystal-blue, blinding-white, and warm-gold palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (28, 12, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted sacred harem courtyard book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong relaxing in a warm hot spring pavilion surrounded by beautiful high-ranking consorts and wives of various cultivation sects, "
                "laughing and sharing wine under blooming cherry blossom trees. "
                "UPPER-RIGHT & BACKGROUND: Traditional oriental palace gardens, stone lanterns, and gentle flowing streams under a starry night sky. "
                "High-contrast cherry-blossom pink, celestial-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (32, 24, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic dynasty restoration book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Supreme Emperor Zhao Tianlong standing victorious atop the rebuilt Great Yan Imperial Palace at sunrise, wearing the crown of universal unity, "
                "surrounded by his devoted SSS-rank wives and bowing imperial subjects. "
                "UPPER-RIGHT HORIZON: Golden dragons soaring through the morning sky above peaceful rivers and majestic mountains. "
                "High-contrast sunrise-gold, royal-purple, and imperial-crimson palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))