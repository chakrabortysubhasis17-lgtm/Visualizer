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


BUILD_DIR = "build_custom_made_demon_king_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/custom-made-demon-king/chapter-1",
    "novel_slug": "custom-made-demon-king",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Custom Made Demon King: Abyss Incubation",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 1 to 50 Premiere)
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
            "display_text": '"A purple moon, a blood-red sea, and a black egg... did I really just hatch into a demon in the Abyss?!"',
            "tts_text": '"A purple moon, a blood-red sea, and a black egg... did I really just hatch into a demon in the Abyss?!"',
            "text": '"A purple moon, a blood-red sea, and a black egg... did I really just hatch into a demon in the Abyss?!"',
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
            "display_text": "After pushing a child out of the path of a speeding car, ordinary gamer Roy awakens not in heaven, but hatching from an egg on a burning magma-sand beach beneath a purple moon—beginning his legendary ascent as a custom-made demon king in the Abyss!",
            "tts_text": "After pushing a child out of the path of a speeding car, ordinary gamer Roy awakens not in heaven, but hatching from an egg on a burning magma-sand beach beneath a purple moon... beginning his legendary ascent as a custom-made demon king in the Abyss!",
            "text": "After pushing a child out of the path of a speeding car, ordinary gamer Roy awakens not in heaven, but hatching from an egg on a burning magma-sand beach beneath a purple moon—beginning his legendary ascent as a custom-made demon king in the Abyss!",
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
            "display_text": "Demon King Decree: To survive the brutal Abyss and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the realm of dark evolution, only absolute cunning commands destiny.",
            "tts_text": "Demon King Decree: To survive the brutal Abyss and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the realm of dark evolution, only absolute cunning commands destiny.",
            "text": "Demon King Decree: To survive the brutal Abyss and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. In the realm of dark evolution, only absolute cunning commands destiny.",
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
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Custom Made Demon King. Break out of your black eggshell, survive the volcanic shore, and watch Roy conquer the Abyss.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Custom Made Demon King. Break out of your black eggshell, survive the volcanic shore, and watch Roy conquer the Abyss.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Custom Made Demon King. Break out of your black eggshell, survive the volcanic shore, and watch Roy conquer the Abyss.",
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
    "final_audio": "output_custom_made_demon_king_001_050.mp3",
    "final_video": "final_custom_made_demon_king_001_050.mp4",
    "cover_image": "cover_custom_made_demon_king_001_050.jpg",
    "timestamps_file": "youtube_timestamps_custom_made_demon_king_001_050.txt",
    "subtitles_file": "subtitles_custom_made_demon_king_001_050.srt",
    "payload_file": "youtube_upload_payload_custom_made_demon_king_001_050.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "CUSTOM MADE DEMON KING! [Chapters 1-50] | Dark Fantasy Abyss Progression Full Audiobook",
    "tags": [
        "Custom Made Demon King", "Custom Made Demon King Audiobook", "Roy", "Abyss Demon Novel",
        "Dark Fantasy Audiobook", "LitRPG Progression", "Demon Evolution Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Custom Made Demon King' (Part 1), covering Chapters 1 through 50!\n\n"
        "Reborn after saving a child from a speeding car, ordinary gamer Roy hatches from a black egg on a burning magma-sand beach "
        "beneath a sinister purple moon in the Abyss. With dark red skin, small horns, a sharp arrow-tail, and a relentless hunger, "
        "a customized demon lord begins his terrifying evolution!\n\n"
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
        "#CustomMadeDemonKing #AbyssDemon #DarkFantasy #LitRPG #DemonKing #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Fantasy Abyss Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (32, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy abyss book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of newborn baby demon Roy emerging from a cracked black eggshell on a volcanic magma-sand beach, "
                "dark red skin, small forehead horns, black arrow-tail, and glowing amber eyes looking up in astonishment. "
                "UPPER-RIGHT SKY: A sinister glowing purple moon hanging over a blood-red sea washing ashore smoking black coals. "
                "High-contrast obsidian-black, volcanic-crimson, and mystic-purple palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (24, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy progression book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Explosive action shot of Roy navigating a perilous volcanic canyon in the Abyss, "
                "avoiding hazards while hunting for survival amidst glowing lava rivers and ash-filled skies. "
                "UPPER-RIGHT & BACKGROUND: Sprawling volcanic wastelands, towering jagged obsidian cliffs, and distant demon hatcheries. "
                "High-contrast magma-orange, dark-charcoal, and violet-glow palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (16, 24, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital demon evolution book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Roy absorbing abyssal energy, "
                "skin glowing with dark runes as his demonic power and physical stats increase. "
                "UPPER-RIGHT & BACKGROUND: Dark cavern walls covered in glowing demonic glyphs and floating soul wisps. "
                "High-contrast demonic-red, deep-obsidian, and electric-blue palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (36, 16, 18),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking dark-fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic combat pose of Roy unleashing his first dark fire spell against a ferocious abyssal beast, flames illuminating his horned silhouette. "
                "UPPER-RIGHT SKY: Fiery volcanic eruptions lighting up a smog-filled abyss sky. "
                "High-contrast crimson-fire, toxic-green, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (22, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted demon city book-cover illustration in top-ranking dark-fantasy webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Demon Lord Roy standing proudly atop a fortified obsidian bastion overlooking a sprawling chaotic demon city in the Abyss, "
                "flanked by loyal lesser demons and shadowy familiars. "
                "UPPER-RIGHT & BACKGROUND: Gothic demon spires, sulfur fog, and massive floating dark fortresses under the purple moon. "
                "High-contrast royal-purple, demonic-crimson, and dark-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (14, 26, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyss exploration book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Roy examining ancient abyssal ruins and forbidden spell circles, "
                "fingers glowing with dark magic as he deciphers lost demon king secrets. "
                "UPPER-RIGHT & BACKGROUND: Crumbling basalt temples, glowing magical traps, and subterranean abyssal rivers. "
                "High-contrast emerald-glow, dark-slate, and mystic-blue palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (30, 20, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted demon throne-room book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy seated upon a newly conquered obsidian throne, surrounded by accumulated abyssal treasures and loyal subordinates, "
                "exuding terrifying demon lord charisma. "
                "UPPER-RIGHT HORIZON: Vaulted stone ceilings, hanging skull chandeliers, and rich dark drapery. "
                "High-contrast molten-gold, ruby-red, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyss war book-cover illustration in top-ranking dark-fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy leading his demonic horde into battle against rival demon lords, "
                "wielding dark weapons and unleashing devastating fire magic across the battlefield. "
                "UPPER-RIGHT SKY: Smoky abyss canyons lit by magical explosions and glowing war banners. "
                "High-contrast mystic-cyan, blazing-orange, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (32, 12, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyssal domain book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy resting in a private obsidian sanctum with elite demon companions, "
                "surrounded by glowing magical artifacts and pools of abyssal starlight under a vaulted cavern roof. "
                "UPPER-RIGHT & BACKGROUND: Sparkling stalactites, floating mana wisps, and cascading underground rivers of lava. "
                "High-contrast amethyst-purple, celestial-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (34, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic demon king ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Supreme Demon King Roy standing triumphantly atop a massive obsidian ziggurat overlooking his vast abyssal empire, "
                "flanked by his loyal demon generals and dark magical pillars touching the purple moon. "
                "UPPER-RIGHT HORIZON: Endless tiers of illuminated demon cities and glowing magical skies stretching across the Abyss. "
                "High-contrast empire-gold, ruby-red, and dark-obsidian palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))