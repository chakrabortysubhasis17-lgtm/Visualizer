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

BUILD_DIR = "build_wasting_money_to_become_an_immortal_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/wasting-money-to-become-an-immortal/chapter-1",
    "novel_slug": "wasting-money-to-become-an-immortal",
    "start_chapter": 1,
    "end_chapter": 50,
    "default_topic": "Wasting Money To Become An Immortal",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate Universal 5-Beat Intro Hook for Chapter 1 (Lin Fan, Super Prodigal System & Reincarnation)
    "intro_hook": [
        # Beat 1: High-Stakes Teaser (0:00 - 0:12)
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": '"Where are my lackeys? Get rid of this white, it\'s too bright! I don\'t care how much money it takes, just get it done!" Waking up in the void after dying in a fire, self-proclaimed super prodigal Lin Fan is bound to the Super Prodigal System—rewarded for his shameless generosity with a ticket to the immortal cultivation realm!',
            "tts_text": '"Where are my lackeys? Get rid of this white, it\'s too bright! I don\'t care how much money it takes, just get it done!" Waking up in the void after dying in a fire, self-proclaimed super prodigal Lin Fan is bound to the Super Prodigal System... rewarded for his shameless generosity with a ticket to the immortal cultivation realm!',
            "text": '"Where are my lackeys? Get rid of this white, it\'s too bright! I don\'t care how much money it takes, just get it done!" Waking up in the void after dying in a fire, self-proclaimed super prodigal Lin Fan is bound to the Super Prodigal System—rewarded for his shameless generosity with a ticket to the immortal cultivation realm!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
            "bgm_mood": "playful"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
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

        # Beat 2: Trademark Channel Signature (0:12 - 0:17)
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Male",
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
            "gender": "Male",
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

        # Beat 3: In-Universe Lore-Bound CTA (0:17 - 0:27)
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Super Prodigal Directive: To activate your infinite spirit stone allowance for today's grand release, smash the Like button and subscribe to the channel. Remember, wasting money isn't just a habit—it's your holy duty on the path to immortality.",
            "tts_text": "Super Prodigal Directive: To activate your infinite spirit stone allowance for today's grand release, smash the Like button and subscribe to the channel. Remember, wasting money isn't just a habit... it's your holy duty on the path to immortality.",
            "text": "Super Prodigal Directive: To activate your infinite spirit stone allowance for today's grand release, smash the Like button and subscribe to the channel. Remember, wasting money isn't just a habit—it's your holy duty on the path to immortality.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "coin",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Male",
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

        # Beat 4: Recap Bridge (0:27 - 0:40)
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Our journey begins from the very beginning. Today, we step into chapters one through fifty of Wasting Money To Become An Immortal. Lackeys, prepare the carriage and count the coin—let the prodigal descent begin.",
            "tts_text": "Our journey begins from the very beginning. Today, we step into chapters one through fifty of Wasting Money To Become An Immortal. Lackeys, prepare the carriage and count the coin... let the prodigal descent begin.",
            "text": "Our journey begins from the very beginning. Today, we step into chapters one through fifty of Wasting Money To Become An Immortal. Lackeys, prepare the carriage and count the coin—let the prodigal descent begin.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "warmth"
        },

        # Beat 5: Post-Intro Scene SFX & Transition Silence (0:40 - 0:42)
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Male",
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
            "sfx": "hum",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Male",
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

    "build_dir": BUILD_DIR,
    "final_audio": "output_wasting_money_to_become_an_immortal_1_50.mp3",
    "final_video": "final_wasting_money_to_become_an_immortal_1_50.mp4",
    "cover_image": "cover_wasting_money_to_become_an_immortal_1_50.jpg",
    "timestamps_file": "youtube_timestamps_wasting_money_to_become_an_immortal_1_50.txt",
    "subtitles_file": "subtitles_wasting_money_to_become_an_immortal_1_50.srt",
    "payload_file": "youtube_upload_payload_wasting_money_to_become_an_immortal_1_50.json",

    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    "video_title": "SUPER PRODIGAL SYSTEM & CULTIVATION TYCOON! [Chapters 1-50] | Wasting Money To Become An Immortal Full Audiobook",
    "tags": [
        "Wasting Money To Become An Immortal", "Super Prodigal System", "Cultivation Comedy",
        "Xianxia Audiobook", "LitRPG Cultivation", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the complete opening arc of 'Wasting Money To Become An Immortal', covering Chapters 1 through 50!\n\n"
        "After dying in a burning building to save a child, self-proclaimed super prodigal Lin Fan awakens in a mysterious void "
        "and is granted the ultimate cheat: the Super Prodigal System! Reincarnating into a ruthless cultivation world, "
        "he discovers that the fastest road to godhood isn't bitter ascetic meditation—it's squandering spirit stones with "
        "flamboyant generosity and unhinged extravagance.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system notifications).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#WastingMoneyToBecomeAnImmortal #SuperProdigalSystem #CultivationComedy #Audiobook #BeingABong"
    ),

    "blocks": [
        {
            "index": 1, "range": (1, 12),
            "title": ["A PRODIGAL SYSTEM", "AWAKENING IN THE VOID"],
            "fallback_color": (30, 25, 40),
            "prompt": (
                "Cinematic 3D illustration of a young handsome man dressed in opulent noble silk robes standing in a glowing ethereal white void, "
                "conversing with a mysterious tall figure made of pure radiant light, golden system interface panels and holographic coins floating in midair, "
                "octane render, unreal engine 5 style, crisp textures, volumetric light rays, 4k digital art."
            )
        },
        {
            "index": 2, "range": (13, 25),
            "title": ["REINCARNATION ARRIVAL", "SHAMELESS SPENDING BEGINS"],
            "fallback_color": (35, 30, 20),
            "prompt": (
                "Cinematic 3D xianxia fantasy scene of an extravagant young clan master strolling arrogantly through a bustling ancient cultivator market, "
                "flanked by nervous clan lackeys carrying overflowing chests of glowing blue spirit stones and immortal jade, "
                "colorful fantasy merchant stalls, lively crowd, dramatic golden hour lighting, highly detailed 4k masterpiece."
            )
        },
        {
            "index": 3, "range": (26, 38),
            "title": ["AUCTION MAYHEM", "SHOCKING THE SECT ELDERS"],
            "fallback_color": (40, 20, 25),
            "prompt": (
                "Cinematic 3D dramatic action scene inside an opulent multi-tiered cultivation auction house, "
                "a young prodigal casually tossing sacks of luminous purple spirit gems from a VIP balcony, "
                "stunned sect elders and martial cultivators staring in utter shock and disbelief below, dynamic composition, warm dramatic lighting, 4k."
            )
        },
        {
            "index": 4, "range": (39, 50),
            "title": ["PRODIGAL IMMORTALITY", "THE RISE OF LIN FAN"],
            "fallback_color": (25, 35, 30),
            "prompt": (
                "Cinematic 3D grandiose establishing shot of Lin Fan standing triumphantly atop an ornate flying spirit boat sailing through sea of golden clouds, "
                "flashing jade talismans and divine spiritual artifacts surrounding him as celestial mountains loom in the distance, "
                "majestic panoramic sunset, epic fantasy render, 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
