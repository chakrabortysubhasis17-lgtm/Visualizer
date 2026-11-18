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


BUILD_DIR = "build_custom_made_demon_king_051_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/custom-made-demon-king/chapter-51",
    "novel_slug": "custom-made-demon-king",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
    "default_topic": "Custom Made Demon King: Surface Invasion",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 51 to 100 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Roy)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Roy",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"One forged letter threatening the Gold Dragon Queen, and the entire elven garrison abandons their fortress—let\'s see how Xeron likes an empty city!"',
            "tts_text": '"One forged letter threatening the Gold Dragon Queen, and the entire elven garrison abandons their fortress... let\'s see how Zair-on likes an empty city!"',
            "text": '"One forged letter threatening the Gold Dragon Queen, and the entire elven garrison abandons their fortress—let\'s see how Xeron likes an empty city!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
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
            "display_text": "Marching across the surface world as adjutant to the great demon Xeron, Roy outsmarts the AvLee elves with ruthless psychological warfare—emptying cliffside fortresses, harvesting souls for custom demon evolution, and carving his path toward supremacy!",
            "tts_text": "Marching across the surface world as adjutant to the great demon Zair-on, Roy outsmarts the Av-Lee elves with ruthless psychological warfare... emptying cliffside fortresses, harvesting souls for custom demon evolution, and carving his path toward supremacy!",
            "text": "Marching across the surface world as adjutant to the great demon Xeron, Roy outsmarts the AvLee elves with ruthless psychological warfare—emptying cliffside fortresses, harvesting souls for custom demon evolution, and carving his path toward supremacy!",
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
            "display_text": "Demon King Decree: To gather soul essence for your custom evolution system and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the surface battlefield, only absolute cunning commands destiny.",
            "tts_text": "Demon King Decree: To gather soul essence for your custom evolution system and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the surface battlefield, only absolute cunning commands destiny.",
            "text": "Demon King Decree: To gather soul essence for your custom evolution system and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. On the surface battlefield, only absolute cunning commands destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Custom Made Demon King. March with the demonic legion, besiege the elven strongholds, and witness Roy's calculated ascent.",
            "tts_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Custom Made Demon King. March with the demonic legion, besiege the elven strongholds, and witness Roy's calculated ascent.",
            "text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Custom Made Demon King. March with the demonic legion, besiege the elven strongholds, and witness Roy's calculated ascent.",
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
    "final_audio": "output_custom_made_demon_king_051_100.mp3",
    "final_video": "final_custom_made_demon_king_051_100.mp4",
    "cover_image": "cover_custom_made_demon_king_051_100.jpg",
    "timestamps_file": "youtube_timestamps_custom_made_demon_king_051_100.txt",
    "subtitles_file": "subtitles_custom_made_demon_king_051_100.srt",
    "payload_file": "youtube_upload_payload_custom_made_demon_king_051_100.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "CUSTOM MADE DEMON KING! [Chapters 51-100] | Dark Fantasy Surface Invasion Full Audiobook",
    "tags": [
        "Custom Made Demon King", "Custom Made Demon King Audiobook", "Roy", "Demon King Progression",
        "Dark Fantasy Audiobook", "LitRPG Evolution", "AvLee Elves", "Xeron", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Custom Made Demon King' (Part 2), covering Chapters 51 through 100!\n\n"
        "Serving as adjutant to the great demon Xeron during the surface invasion of AvLee, Roy uses a clever bluff threatening "
        "the Gold Dragon Queen to trick elven druid heroes into abandoning their cliffside city. Amidst advancing hordes of gogs, "
        "hellhounds, and middle-rank evil spirits, Roy quietly harvests souls and evolves his custom demonic form!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK FANTASY & LITRPG MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#CustomMadeDemonKing #DemonEvolution #DarkFantasy #LitRPG #DemonKing #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Fantasy Surface Invasion Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (51, 55),
            "fallback_color": (26, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of horned dark-red demon Roy standing on a rocky cliff overlook, "
                "sharp calculating eyes glowing with abyssal fire, black arrow-tail whipping behind him as he watches a distant cliffside elven fortress. "
                "UPPER-RIGHT BACKGROUND: Towering white-stone elven spires perched on sheer emerald cliffs with ancient dendroid treants guarding the walls. "
                "High-contrast demonic-crimson, emerald-forest, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (56, 60),
            "fallback_color": (30, 14, 16),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy siege book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Advancing demonic legion marching through a burning forest valley, hordes of fiery hellhounds, gogs, and whip-wielding evil spirits following Roy and towering horned demon general Xeron. "
                "UPPER-RIGHT & BACKGROUND: Smoke billowing over elven arrow towers under a blood-orange war sky. "
                "High-contrast hellfire-orange, charcoal-black, and deep-crimson palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "fallback_color": (16, 22, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital custom-evolution book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Roy inside a shadowed command tent channeling floating blue soul wisps into a glowing holographic demon-customization interface, "
                "dark runes shifting across his clawed forearms. "
                "UPPER-RIGHT & BACKGROUND: Glowing soul-essence orbs drifting through dark smoky air. "
                "High-contrast soul-cyan, abyssal-violet, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (66, 70),
            "fallback_color": (28, 16, 14),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking dark-fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic action pose of Roy unleashing dark frost-fire magic from his clawed hand to shatter an elven magical barrier, "
                "sparks and ice shards flying across ruined stone battlements. "
                "UPPER-RIGHT SKY: Swarming pegasus riders silhouetted against storm clouds and blazing demon fire. "
                "High-contrast frost-cyan, inferno-red, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (71, 75),
            "fallback_color": (22, 18, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted dragon-sanctuary book-cover illustration in top-ranking webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy peering from a jagged mountain crag toward an ancient golden dragon sanctuary hidden deep within misty AvLee peaks, "
                "amber eyes glinting with strategic ambition. "
                "UPPER-RIGHT & BACKGROUND: Colossal silhouette of a majestic Gold Dragon circling radiant sunlit clouds above emerald canyons. "
                "High-contrast celestial-gold, forest-emerald, and shadow-violet palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (76, 80),
            "fallback_color": (14, 24, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-alchemy & soul-forging book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Roy examining captured magical artifacts and ancient spell scrolls inside a conquered elven treasury vault, "
                "crimson demonic aura illuminating golden elven relics. "
                "UPPER-RIGHT & BACKGROUND: Tall carved marble pillars, shattered crystal cases, and glowing arcane sigils. "
                "High-contrast mystic-teal, molten-gold, and dark-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (81, 85),
            "fallback_color": (30, 14, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted demonic confrontation book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm fiery lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy facing off against an arrogant middle-rank demon commander in a scorched canyon, "
                "unleashing overwhelming abyssal pressure and dark lightning from his horns and claws. "
                "UPPER-RIGHT HORIZON: Jagged volcanic spires and swirling ash clouds lit by crimson lightning. "
                "High-contrast crimson-red, electric-violet, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (86, 90),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted nocturnal raid book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy gliding silently over a moonlit ancient forest canopy with newly evolved demonic wings, "
                "scouting an elven supply convoy winding through a misty gorge below. "
                "UPPER-RIGHT SKY: Full purple-tinted moon shining through tattered midnight clouds. "
                "High-contrast silver-purple, shadow-indigo, and emerald-mist palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (91, 95),
            "fallback_color": (32, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyssal portal nexus book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy standing before a towering flaming Hellgate summoning portal on the surface battlefield, "
                "absorbing waves of dark dimensional energy as fresh demon reinforcements march forth. "
                "UPPER-RIGHT & BACKGROUND: Swirling vortex of crimson and violet abyssal fire tearing through the sky. "
                "High-contrast inferno-magenta, celestial-gold, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (96, 100),
            "fallback_color": (34, 20, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic demon lord rise book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Evolved Demon Lord Roy standing victorious atop the ruined battlements of a conquered surface citadel at twilight, "
                "black wings spread wide and glowing runes pulsing across his armored form as his loyal demon followers kneel below. "
                "UPPER-RIGHT HORIZON: Burning war banners, distant mountain ranges, and a dramatic crimson-and-gold sunset sky. "
                "High-contrast empire-gold, demonic-crimson, and twilight-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
