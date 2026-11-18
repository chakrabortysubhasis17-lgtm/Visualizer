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


BUILD_DIR = "build_dual_cultivation_051_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world/chapter-51",
    "novel_slug": "dual-cultivation-gathering-sss-rank-wives-in-the-cultivation-world",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
    "default_topic": "Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 51 to 100 Continuation)
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
            "display_text": '"A twisted spire pulsing with demonic blood, and an ancient entity trying to break our minds—stand behind me, I will hold the line!"',
            "tts_text": '"A twisted spire pulsing with demonic blood, and an ancient entity trying to break our minds... stand behind me, I will hold the line!"',
            "text": '"A twisted spire pulsing with demonic blood, and an ancient entity trying to break our minds—stand behind me, I will hold the line!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
            "bgm_mood": "dread"
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
            "display_text": "Venturing deep into the midnight-stone crater of the Fragment Nexus, Zhao Tianlong shields Feng Lianhua, Mei Ling, and Lin Yue from soul-shattering illusions and dark sect conspiracies—unleashing golden inheritance light to claim priceless fragments and ascend to greater heights!",
            "tts_text": "Venturing deep into the midnight-stone crater of the Fragment Nexus, Zhao Tianlong shields Feng Lianhua, Mei Ling, and Lin Yue from soul-shattering illusions and dark sect conspiracies... unleashing golden inheritance light to claim priceless fragments and ascend to greater heights!",
            "text": "Venturing deep into the midnight-stone crater of the Fragment Nexus, Zhao Tianlong shields Feng Lianhua, Mei Ling, and Lin Yue from soul-shattering illusions and dark sect conspiracies—unleashing golden inheritance light to claim priceless fragments and ascend to greater heights!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
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
            "display_text": "Harem Emperor Decree: To temper your soul against demonic whispers and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, only unyielding will commands destiny.",
            "tts_text": "Harem Emperor Decree: To temper your soul against demonic whispers and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, only unyielding will commands destiny.",
            "text": "Harem Emperor Decree: To temper your soul against demonic whispers and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the path of dual cultivation, only unyielding will commands destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Enter the Fragment Nexus, shatter the dark illusions, and witness Zhao Tianlong's continued rise.",
            "tts_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Enter the Fragment Nexus, shatter the dark illusions, and witness Zhao Tianlong's continued rise.",
            "text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World. Enter the Fragment Nexus, shatter the dark illusions, and witness Zhao Tianlong's continued rise.",
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
    "final_audio": "output_dual_cultivation_051_100.mp3",
    "final_video": "final_dual_cultivation_051_100.mp4",
    "cover_image": "cover_dual_cultivation_051_100.jpg",
    "timestamps_file": "youtube_timestamps_dual_cultivation_051_100.txt",
    "subtitles_file": "subtitles_dual_cultivation_051_100.srt",
    "payload_file": "youtube_upload_payload_dual_cultivation_051_100.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUAL CULTIVATION: GATHERING SSS-RANK WIVES! [Chapters 51-100] | Xianxia Harem Progression Audiobook",
    "tags": [
        "Dual Cultivation", "Gathering SSS-Rank Wives", "Xianxia Audiobook", "Harem Progression Novel",
        "System Cultivation", "Zhao Tianlong", "Feng Lianhua", "Fragment Nexus", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dual Cultivation: Gathering SSS-Rank Wives in the Cultivation World' (Part 2), covering Chapters 51 through 100!\n\n"
        "Standing before the midnight-stone crater of the Fragment Nexus, Zhao Tianlong confronts a terrifying ancient entity "
        "that twists space and shatters Feng Lianhua's faith in the Immortal Sect. Shielding Feng Lianhua, Mei Ling, and Lin Yue "
        "with golden inheritance light, Zhao Tianlong fights to claim the crystalline fragments and deepen his bonds!\n\n"
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
        "#DualCultivation #SSSRankWives #XianxiaAudiobook #HaremProgression #ZhaoTianlong #BeingABong"
    ),

    # 10 Textless 2D/2.5D Xianxia Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (51, 55),
            "fallback_color": (24, 12, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of imperial cultivator Zhao Tianlong standing in a midnight-black stone crater, "
                "unleashing a radiant golden barrier of inheritance light to shield pale-eyed Immortal Sect beauty Feng Lianhua, nature-affined Mei Ling, and sharp-eyed archer Lin Yue. "
                "UPPER-RIGHT BACKGROUND: Twisted impossible spires pulsing with veins of crimson energy and floating demonic crystal shards. "
                "High-contrast celestial-gold, crimson-blood, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (56, 60),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia dark-ruins book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Tense defensive stand inside a crumbling mausoleum of jagged black rock etched with glowing demonic runes, "
                "Zhao Tianlong channeling golden Qi while Lin Yue draws a glowing emerald spirit bow and Mei Ling summons nature vines. "
                "UPPER-RIGHT & BACKGROUND: Swirling shadow wisps, fractured spatial rifts, and a massive pulsing crimson crystal hovering above a dark spire. "
                "High-contrast demonic-crimson, emerald-green, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "fallback_color": (14, 24, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Xianxia dual-cultivation book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up inside a secluded spirit-stone sanctuary, Zhao Tianlong and Feng Lianhua seated face-to-face in meditation, "
                "intertwining streams of golden imperial Qi and ice-jade immortal essence swirling upward in a luminous vortex. "
                "UPPER-RIGHT & BACKGROUND: Floating translucent system status windows, glowing jade talismans, and misty cavern waterfalls. "
                "High-contrast celestial-gold, ice-cyan, and deep-teal palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (66, 70),
            "fallback_color": (28, 14, 20),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Explosive action pose of Zhao Tianlong shattering a spatial distortion barrier with a golden dragon palm strike, "
                "sending shockwaves of radiant energy across shattered obsidian bridges. "
                "UPPER-RIGHT SKY: Collapsing dark void vortex pierced by beams of golden sunlight breaking through stormy clouds. "
                "High-contrast imperial-gold, scarlet-red, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (71, 75),
            "fallback_color": (16, 26, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted spiritual forest sanctuary book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong walking beside Mei Ling and Lin Yue through an ancient spirit-herb valley after escaping the dark realm, "
                "emerald spirit fireflies and golden pollen drifting around them. "
                "UPPER-RIGHT & BACKGROUND: Towering jade-green mountain peaks, cascading silver waterfalls, and floating immortal sect pavilions in the distance. "
                "High-contrast jade-emerald, warm-gold, and twilight-blue palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (76, 80),
            "fallback_color": (26, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted sect confrontation book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Cold and vengeful Feng Lianhua standing beside Zhao Tianlong atop a cloud-swept Immortal Sect plaza, "
                "ice-blue sword aura radiating from her palm as they confront corrupt elders. "
                "UPPER-RIGHT & BACKGROUND: Grand white-marble sect halls, flying swords hovering in formation, and dramatic sunset clouds. "
                "High-contrast glacier-blue, molten-gold, and crimson-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (81, 85),
            "fallback_color": (24, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted secret treasury pavilion book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong absorbing the purified essence of a massive crystalline fragment inside an imperial cultivation chamber, "
                "golden dragon tattoos glowing across his robes while floating system panels display breakthrough stats. "
                "UPPER-RIGHT HORIZON: Ornate dragon-carved pillars, glowing spirit lanterns, and swirling purple-gold Qi clouds. "
                "High-contrast royal-purple, blinding-gold, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (86, 90),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted celestial night battle book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong soaring midair above imperial city walls at night, unleashing a sweeping golden sword wave "
                "while Lin Yue fires piercing emerald arrows from a nearby pagoda roof. "
                "UPPER-RIGHT SKY: Full silver moon framed by swirling storm clouds and streaks of flying-sword light. "
                "High-contrast silver-cyan, imperial-gold, and midnight-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (91, 95),
            "fallback_color": (30, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted imperial harem garden book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Zhao Tianlong sharing a quiet moonlit banquet in an ornate palace pavilion with Feng Lianhua, Mei Ling, and Lin Yue, "
                "warm lantern light reflecting off silk robes and jade wine cups. "
                "UPPER-RIGHT & BACKGROUND: Blooming crimson plum blossoms, tranquil koi ponds, and tiered golden palace roofs under a starry sky. "
                "High-contrast rose-crimson, warm-amber, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (96, 100),
            "fallback_color": (32, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic empire ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Emperor Zhao Tianlong standing triumphantly atop a towering celestial platform overlooking his expanding dynasty at dawn, "
                "golden dragon aura rising behind him as his devoted SSS-rank wives stand at his side. "
                "UPPER-RIGHT HORIZON: Endless sea of golden sunrise clouds, distant immortal mountain peaks, and soaring spiritual cranes. "
                "High-contrast sunrise-gold, royal-purple, and imperial-crimson palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))