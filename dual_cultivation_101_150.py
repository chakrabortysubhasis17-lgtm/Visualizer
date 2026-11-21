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


BUILD_DIR = "build_dual_cultivation_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world/chapter-101",
    "novel_slug": "dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world",
    "start_chapter": 101,
    "end_chapter": 150,
    "is_start": False,
    "default_topic": "Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 101 to 150 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Feng Lianhua)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Feng Lianhua",
            "gender": "Female",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"You dare brand me an oath-breaker, Elder Zhao? Step closer and witness what true winter looks like when unbound from your sect\'s shackles!"',
            "tts_text": '"You dare brand me an oath-breaker, Elder Jow? Step closer and witness what true winter looks like when unbound from your sect\'s shackles!"',
            "text": '"You dare brand me an oath-breaker, Elder Zhao? Step closer and witness what true winter looks like when unbound from your sect\'s shackles!"',
            "voice": "en-US-AvaMultilingualNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
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
            "display_text": "Synchronized with Zhao Tianlong's Great Vehicle realm resonance, Feng Lianhua confronts Elder Zhao Mingwei and thirty elite Immortal Sect disciples alone—unleashing the Absolute Zero Mandala as ancient sect secrets unravel and the battle for supremacy escalates!",
            "tts_text": "Synchronized with Jow Tyan-long's Great Vehicle realm resonance, Fung Lyan-hwa confronts Elder Jow Ming-way and thirty elite Immortal Sect disciples alone... unleashing the Absolute Zero Mandala as ancient sect secrets unravel and the battle for supremacy escalates!",
            "text": "Synchronized with Zhao Tianlong's Great Vehicle realm resonance, Feng Lianhua confronts Elder Zhao Mingwei and thirty elite Immortal Sect disciples alone—unleashing the Absolute Zero Mandala as ancient sect secrets unravel and the battle for supremacy escalates!",
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
            "display_text": "Harem Emperor Decree: To shatter hypocritical sect formations and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, only sovereign power commands destiny.",
            "tts_text": "Harem Emperor Decree: To shatter hypocritical sect formations and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, only sovereign power commands destiny.",
            "text": "Harem Emperor Decree: To shatter hypocritical sect formations and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, only sovereign power commands destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Unfurl the Absolute Zero Mandala, crush the Immortal Sect's ambush, and witness Zhao Tianlong's ascendant reign.",
            "tts_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Dual Cultivation: Gathering triple-S-Rank Wives in the Cultivation World. Unfurl the Absolute Zero Mandala, crush the Immortal Sect's ambush, and witness Jow Tyan-long's ascendant reign.",
            "text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Unfurl the Absolute Zero Mandala, crush the Immortal Sect's ambush, and witness Zhao Tianlong's ascendant reign.",
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
    "final_audio": "output_dual_cultivation_101_150.mp3",
    "final_video": "final_dual_cultivation_101_150.mp4",
    "cover_image": "cover_dual_cultivation_101_150.jpg",
    "timestamps_file": "youtube_timestamps_dual_cultivation_101_150.txt",
    "subtitles_file": "subtitles_dual_cultivation_101_150.srt",
    "payload_file": "youtube_upload_payload_dual_cultivation_101_150.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUAL CULTIVATION: GATHERING SSS-RANK WIVES! [Chapters 101-150] | Xianxia Harem Progression Audiobook",
    "tags": [
        "Dual Cultivation", "Gathering SSS-Rank Wives", "Xianxia Audiobook", "Harem Progression Novel",
        "System Cultivation", "Zhao Tianlong", "Feng Lianhua", "Immortal Sect", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World' (Part 3), covering Chapters 101 through 150!\n\n"
        "Empowered by her soul-link to Zhao Tianlong's Great Vehicle cultivation, Feng Lianhua faces down Dao Integration Elder "
        "Zhao Mingwei and thirty Core Formation disciples—unleashing the crystalline Absolute Zero Mandala as the Immortal Sect's "
        "darkest secrets come to light and new SSS-rank alliances take shape!\n\n"
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
        "#DualCultivation #SSSRankWives #XianxiaAudiobook #HaremProgression #FengLianhua #BeingABong"
    ),

    # 10 Textless 2D/2.5D Xianxia Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (101, 105),
            "fallback_color": (14, 24, 38),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of fierce ice-cultivator Feng Lianhua standing atop a floating crystalline frost platform, "
                "pale blue eyes blazing as thousands of geometric ice crystals orbit her in an Absolute Zero Mandala. "
                "UPPER-RIGHT BACKGROUND: White-robed Dao Integration elders and flying-sword disciples engulfed in golden binding chains and shattering frost waves. "
                "High-contrast glacier-cyan, celestial-gold, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (106, 110),
            "fallback_color": (24, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia sky-battle book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Zhao Tianlong descending from storm clouds in imperial gold-and-obsidian robes beside Feng Lianhua, "
                "unleashing a towering golden dragon Qi aura that overwhelms rival sect elders. "
                "UPPER-RIGHT & BACKGROUND: Fractured spatial rifts, swirling spirit clouds, and shattered flying swords falling through twilight skies. "
                "High-contrast imperial-gold, ice-blue, and royal-violet palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (111, 115),
            "fallback_color": (16, 26, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dual-cultivation sanctuary book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up inside a luminous jade-and-ice spiritual pavilion, Zhao Tianlong and Feng Lianhua meditating together "
                "as twin streams of molten golden solar Qi and crystalline frost essence spiral into a harmonious celestial lotus. "
                "UPPER-RIGHT & BACKGROUND: Floating translucent system status windows, glowing spirit lanterns, and misty mountain waterfalls. "
                "High-contrast celestial-gold, frost-cyan, and deep-teal palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (116, 120),
            "fallback_color": (28, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic martial pose of Zhao Tianlong standing alongside Mei Ling, Lin Yue, and Feng Lianhua on a high cloud-cliff, "
                "surveying the southern sect territories as golden war banners unfurl in the wind. "
                "UPPER-RIGHT SKY: Dramatic crimson sunset clouds pierced by beams of divine light over distant Immortal Sect mountain peaks. "
                "High-contrast scarlet-crimson, warm-gold, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (121, 125),
            "fallback_color": (18, 22, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted ancient secret realm book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong entering an ancient celestial treasury chamber lined with towering jade monoliths, "
                "extending his hand toward a levitating divine inheritance orb radiating golden light. "
                "UPPER-RIGHT & BACKGROUND: Swirling starlight constellations, ancient formation arrays etched in marble, and floating spirit wisps. "
                "High-contrast sapphire-blue, blinding-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (126, 130),
            "fallback_color": (26, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted sect-siege confrontation book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Zhao Tianlong hovering midair before the grand mountain gates of the Immortal Sect, raising a golden imperial decree sword "
                "as shimmering defensive domes crack beneath his Great Vehicle realm pressure. "
                "UPPER-RIGHT & BACKGROUND: Grand white-marble sect palaces, soaring elders on flying swords, and swirling golden-red Qi storms. "
                "High-contrast molten-gold, ruby-crimson, and charcoal-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (131, 135),
            "fallback_color": (24, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted celestial alchemy & breakthrough book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong channeling golden-violet flame beneath an ornate dragon-carved bronze cauldron, "
                "refining supreme immortal elixirs while luminous system upgrade notifications hover beside him. "
                "UPPER-RIGHT HORIZON: Glowing spirit-herb gardens, floating jade pagodas, and a starry night sky. "
                "High-contrast royal-purple, flame-gold, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (136, 140),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted heavenly tribulation book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong standing fearless atop a jagged mountain peak as nine-colored heavenly tribulation lightning strikes down around him, "
                "his golden dragon aura deflecting the celestial bolts into showers of sparks. "
                "UPPER-RIGHT SKY: Colossal swirling storm vortexes illuminated by silver-violet lightning arcs. "
                "High-contrast electric-cyan, imperial-gold, and midnight-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (141, 145),
            "fallback_color": (30, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted imperial harem courtyard book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong relaxing in a tranquil moonlit palace garden surrounded by his devoted SSS-rank wives—Feng Lianhua, Mei Ling, and Lin Yue, "
                "warm lantern light reflecting off silk robes and blooming lotus ponds. "
                "UPPER-RIGHT & BACKGROUND: Ornate curved palace roofs, cascading water features, and a luminous full moon. "
                "High-contrast rose-crimson, warm-amber, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (146, 150),
            "fallback_color": (32, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic immortal dynasty ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Supreme Emperor Zhao Tianlong standing triumphantly atop the conquered Immortal Sect summit at sunrise, "
                "golden dragon aura soaring behind him as his peerless SSS-rank companions stand proudly at his side. "
                "UPPER-RIGHT HORIZON: Endless sea of golden morning clouds, floating celestial palaces, and soaring divine cranes. "
                "High-contrast sunrise-gold, royal-purple, and imperial-crimson palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))