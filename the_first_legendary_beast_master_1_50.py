import os
import re
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

WATERMARK_PATTERNS = [
    re.compile(r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*", re.IGNORECASE),
    re.compile(r"https?://(?:m\.)?webnovel\.com/[^\s\"']+", re.IGNORECASE),
    re.compile(r"Ads\s+by\s+Pubfuture", re.IGNORECASE),
    re.compile(r"Pubfuture\s+Ads", re.IGNORECASE),
]


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
                has_watermark = any(
                    any(
                        pat.search(r.get("display_text") or r.get("tts_text") or r.get("text", ""))
                        for pat in WATERMARK_PATTERNS
                    )
                    for r in rows
                )
                if len(rows) < 8 or has_watermark or any(
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
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} stale/watermark cache files to guarantee clean scraping.", flush=True)


BUILD_DIR = "build_first_legendary_beast_master_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/the-first-legendary-beast-master/chapter-1",
    "novel_slug": "the-first-legendary-beast-master",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "The First Legendary Beast Master",

    "batch_size": 15,
    "parallel_chapters": 1,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Scraper & Line Sanitization Rules
    "strip_patterns": [
        r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*",
        r"https?://(?:m\.)?webnovel\.com/[^\s\"']+",
        r"Ads\s+by\s+Pubfuture",
        r"Pubfuture\s+Ads",
        r"Read\s+latest\s+Chapters\s+at\s+FreeWebNovel[^\n]*",
    ],

    # Standard 5-Beat Intro Hook (Series Premiere: Chapters 1 to 50)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Crimson-Eyed Military Medic)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Military Medic",
            "gender": "Female",
            "line_type": "Dialogue",
            "emotion": "intrigued_amused",
            "age_category": "adult",
            "display_text": '"There you are. I thought that we lost you there for a minute—zero casualties at this stop always means there is a powerful one in the bunch."',
            "tts_text": '"There you are. I thought that we lost you there for a minute... zero casualties at this stop always means there is a powerful one in the bunch."',
            "text": '"There you are. I thought that we lost you there for a minute—zero casualties at this stop always means there is a powerful one in the bunch."',
            "voice": "en-US-JennyNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "+0Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "chime",
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
            "display_text": "Surviving the lethal Mana Awakening Serum with three crimson claw marks seared onto his forearm—an unknown class found in no academy textbook—a fourteen-year-old miner's son boards the train to Golden Divine Academy and awakens a forgotten power across Chapters 1 through 50!",
            "tts_text": "Surviving the lethal Mana Awakening Serum with three crimson claw marks seared onto his forearm... an unknown class found in no academy textbook... a fourteen year old miner's son boards the train to Golden Divine Academy and awakens a forgotten power across Chapters 1 through 50!",
            "text": "Surviving the lethal Mana Awakening Serum with three crimson claw marks seared onto his forearm—an unknown class found in no academy textbook—a fourteen-year-old miner's son boards the train to Golden Divine Academy and awakens a forgotten power across Chapters 1 through 50!",
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
            "display_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
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
            "display_text": "Golden Dragon Academy Directive: To unlock Karl's forbidden bloodline marks and launch this fifty-chapter beast-taming marathon, hit that Like button and subscribe to the channel. Every soul fuels the rise of the First Legendary Beast Master.",
            "tts_text": "Golden Dragon Academy Directive: To unlock Karl's forbidden bloodline marks and launch this fifty chapter beast taming marathon, hit that Like button and subscribe to the channel. Every soul fuels the rise of the First Legendary Beast Master.",
            "text": "Golden Dragon Academy Directive: To unlock Karl's forbidden bloodline marks and launch this fifty-chapter beast-taming marathon, hit that Like button and subscribe to the channel. Every soul fuels the rise of the First Legendary Beast Master.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "conversational_mid",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "interface",
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
        # Beat 4: Series Premiere Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of The First Legendary Beast Master. Witness the Divine Serum trial, forge primal beast bonds, and follow Karl's rise.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of The First Legendary Beast Master. Witness the Divine Serum trial, forge primal beast bonds, and follow Karl's rise.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of The First Legendary Beast Master. Witness the Divine Serum trial, forge primal beast bonds, and follow Karl's rise.",
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
    "final_audio": "output_first_legendary_beast_master_1_50.mp3",
    "final_video": "final_first_legendary_beast_master_1_50.mp4",
    "cover_image": "cover_first_legendary_beast_master_1_50.jpg",
    "timestamps_file": "youtube_timestamps_first_legendary_beast_master_1_50.txt",
    "subtitles_file": "subtitles_first_legendary_beast_master_1_50.srt",
    "payload_file": "youtube_upload_payload_first_legendary_beast_master_1_50.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "THE FIRST LEGENDARY BEAST MASTER [Chapters 1-50] | Progression Fantasy & Beast Taming LitRPG Audiobook",
    "tags": [
        "The First Legendary Beast Master", "Beast Taming Audiobook", "Progression Fantasy LitRPG",
        "Golden Dragon Nation", "Karl", "Divine Serum Awakening", "Fantasy Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to Episode 1 of 'The First Legendary Beast Master', covering Chapters 1 through 50!\n\n"
        "In the Golden Dragon Nation, only five percent survive the Mana Awakening Serum to become superhuman Elites. "
        "At Lithium Mine Middle School, fourteen-year-old Karl nearly dies during his injection—only to awaken with three "
        "crimson claw marks seared onto his forearm, a mysterious mark absent from every official Academy manual. "
        "Aboard the luxury train to Golden Divine Academy and beyond, Karl uncovers his true Beast Master calling across "
        "Chapters 1 through 50!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, center-locked vocal clarity, stereo spatial ambience).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE PROGRESSION FANTASY & LITRPG MARATHONS ON BEING A BONG:\n"
        "• The Incubus System -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#TheFirstLegendaryBeastMaster #BeastMasterAudiobook #ProgressionFantasy #LitRPG #GoldenDragonNation #BeingABong"
    ),

    # 10 Textless 2D/2.5D Progression Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (20, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital progression-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Fourteen-year-old bronze-skinned boy Karl in a modest mining-town school uniform sitting in a gymnasium folding chair, "
                "staring in shock at three glowing crimson claw marks seared along his forearm as a sharp-eyed crimson-eyed military medic in a green uniform holds a golden-liquid syringe. "
                "UPPER-RIGHT BACKGROUND: Tall industrial gymnasium windows revealing dusty lithium mine ridges under a golden sky. "
                "High-contrast crimson-red, imperial-gold, and slate-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (24, 18, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital luxury-train-mystery book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and warm cinematic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Karl seated at a mahogany desk inside a velvet-draped luxury train cabin studying an open illustrated awakening manual, "
                "faint crimson beast-spirit wisps swirling from the three claw marks on his outstretched wrist. "
                "UPPER-RIGHT & BACKGROUND: Panoramic train window showing sweeping mountain valleys and Golden Dragon Nation banners at sunset. "
                "High-contrast warm-amber, scarlet-crimson, and deep-mahogany palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Golden-Divine-Academy book-cover illustration in top-ranking webnovel art style, "
                "grand architectural framing and luminous brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Young Karl standing at the grand stone gates of Golden Divine Academy gazing upward in awe "
                "as noble student mages and warriors channel elemental fire and ice aura across the marble courtyard. "
                "UPPER-RIGHT & BACKGROUND: Towering golden-spired citadels and colossal carved dragon statues beneath drifting dawn clouds. "
                "High-contrast imperial-gold, sapphire-blue, and crimson-slate palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (18, 24, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant atmospheric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Karl kneeling inside an ancient forested beast-sanctuary clearing as his crimson claw mark projects a glowing summoning sigil, "
                "forming a shimmering soul bond with a fierce young shadow-furred magical beast cub. "
                "UPPER-RIGHT BACKGROUND: Giant moss-covered spirit trees and drifting emerald-gold mana particles in sunbeams. "
                "High-contrast emerald-green, blood-crimson, and sunlit-gold palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital combat-arena-duel book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic action brushwork and rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Karl commanding his agile bonded magical beast in a stone academy sparring arena "
                "against an arrogant noble student wielding blazing fire-blade constructs, sparks and crimson mana shockwaves erupting between them. "
                "UPPER-RIGHT & BACKGROUND: Tiered amphitheater bleachers packed with stunned academy instructors and cadets. "
                "High-contrast molten-orange, crimson-violet, and charcoal-stone palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (14, 18, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital wilderness-hunt book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric moonlight, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Karl leading a squad of young academy elites through a misty canyon at twilight alongside his fierce bonded beast, "
                "crimson beast-master runes glowing on his forearm as they ambush a pack of armored earth-monsters. "
                "UPPER-RIGHT & BACKGROUND: Jagged moonlit cliffs and glowing crystal veins lining the canyon walls. "
                "High-contrast midnight-indigo, crystal-cyan, and scarlet-crimson palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (26, 18, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted bloodline-evolution book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and luminous energy effects, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Karl channeling refined mana crystals into his bonded beast inside a stone meditation chamber, "
                "golden-crimson evolutionary light enveloping the creature as dormant mythical traits awaken. "
                "UPPER-RIGHT HORIZON: Ancient dragon-carved pillars and floating arcane light orbs illuminating the vaulted ceiling. "
                "High-contrast radiant-gold, blood-crimson, and obsidian-brown palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (18, 22, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted dual-beast-contract book-cover illustration in top-ranking progression art style, "
                "dramatic low-angle framing and razor-sharp brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Karl standing confidently with two distinct magical beasts flanking him—a sleek shadow-predator and a storm-winged raptor—"
                "while glowing crimson claw sigils pulse brightly along his raised forearm. "
                "UPPER-RIGHT SKY: Dramatic wind-swept clouds and golden lightning arcing over mountain peaks. "
                "High-contrast storm-blue, imperial-gold, and scarlet-crimson palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (24, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted monster-horde-defense book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Karl fighting side-by-side with his evolved magical beasts atop a fortified frontier wall "
                "repelling a surging tide of wild monsters with synchronized beast-arts and golden-crimson shockwaves. "
                "UPPER-RIGHT & BACKGROUND: Signal flares rising into a smoke-streaked twilight sky above the Golden Dragon borderlands. "
                "High-contrast ember-red, royal-gold, and dark-slate palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (20, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Beast-Master-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Karl standing atop a sunlit cliff overlooking the Golden Dragon Nation with his loyal magical beasts beside him, "
                "the three crimson claw marks on his forearm radiating regal golden-scarlet light as ancient dragon silhouettes shimmer in the clouds. "
                "UPPER-RIGHT HORIZON: Brilliant sunrise breaking over distant golden spires and vast emerald valleys. "
                "High-contrast sunrise-gold, crimson-scarlet, and twilight-azure palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))