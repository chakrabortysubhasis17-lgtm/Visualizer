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

BUILD_DIR = "build_kingdoms_bloodline_85_112"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/kingdoms-bloodline/chapter-85",
    "novel_slug": "kingdoms-bloodline",
    "start_chapter": 85,
    "end_chapter": 112,
    "default_topic": "Kingdom's Bloodline: The Blood Clan's True Form",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Accurate 5-Beat Intro Hook for Chapter 85
    "intro_hook": [
        # Beat 1: High-Stakes Teaser
        {
            "line_id": "intro_01_teaser",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": '"Reveal your True Form, you blood-sucking little shit!" Shrouded in dark snow-swept fog, Aida wields her Sunset Goddess-blessed machete against the razor claws of Supreme Class Blood Clansman Simon Corleone, while Wya Caso faces the brutal test of the Tower of Eradication!',
            "tts_text": '"Reveal your True Form, you blood-sucking little shit!" Shrouded in dark snow-swept fog, Aida wields her Sunset Goddess-blessed machete against the razor claws of Supreme Class Blood Clansman Simon Corleone... while Wya Caso faces the brutal test of the Tower of Eradication!',
            "text": '"Reveal your True Form, you blood-sucking little shit!" Shrouded in dark snow-swept fog, Aida wields her Sunset Goddess-blessed machete against the razor claws of Supreme Class Blood Clansman Simon Corleone, while Wya Caso faces the brutal test of the Tower of Eradication!',
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "blade",
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
        # Beat 2: Trademark Channel Signature
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
        # Beat 3: In-Universe CTA
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Imperial Decree: To fuel the Northland's frontlines and support today's massive release, hit that Like button and subscribe to the channel. Defying ancient vampires and surviving the fog demands unwavering resolve.",
            "tts_text": "Imperial Decree: To fuel the Northland's frontlines and support today's massive release, hit that Like button and subscribe to the channel. Defying ancient vampires and surviving the fog demands unwavering resolve.",
            "text": "Imperial Decree: To fuel the Northland's frontlines and support today's massive release, hit that Like button and subscribe to the channel. Defying ancient vampires and surviving the fog demands unwavering resolve.",
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
        # Beat 4: Recap Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, the Northland's perilous politics pushed mortal knights and covert protectors into lethal clashes. Now, entering Chapters 85 through 112 of Kingdom's Bloodline, ancient vampires unleash their monstrous metamorphoses. Steel yourselves, and let the battle begin.",
            "tts_text": "Previously, the Northland's perilous politics pushed mortal knights and covert protectors into lethal clashes. Now, entering Chapters 85 through 112 of Kingdom's Bloodline... ancient vampires unleash their monstrous metamorphoses. Steel yourselves, and let the battle begin.",
            "text": "Previously, the Northland's perilous politics pushed mortal knights and covert protectors into lethal clashes. Now, entering Chapters 85 through 112 of Kingdom's Bloodline, ancient vampires unleash their monstrous metamorphoses. Steel yourselves, and let the battle begin.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
        },
        # Beat 5: Lead-In Transition
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
            "sfx": "wind",
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
    "final_audio": "output_kingdoms_bloodline_85_112.mp3",
    "final_video": "final_kingdoms_bloodline_85_112.mp4",
    "cover_image": "cover_kingdoms_bloodline_85_112.jpg",
    "timestamps_file": "youtube_timestamps_kingdoms_bloodline_85_112.txt",
    "subtitles_file": "subtitles_kingdoms_bloodline_85_112.srt",
    "payload_file": "youtube_upload_payload_kingdoms_bloodline_85_112.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "KINGDOM'S BLOODLINE: THE BLOOD CLAN'S TRUE FORM! [Chapters 85-112] | Dark Fantasy Full Audiobook",
    "tags": [
        "Kingdoms Bloodline", "Dark Fantasy", "Vampire Novel", "Audiobook",
        "Fantasy Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Kingdom's Bloodline', covering Chapters 85 through 112!\n\n"
        "As Aida confronts Simon Corleone in the snow-covered fog and Wya Caso tests the limits of the Power of "
        "Eradication against immortal vampires, the true monstrous nature of the Blood Clan is unveiled. "
        "Experience professional multi-voice narration, atmospheric sound design, and master audio mastering.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and narration).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#KingdomsBloodline #DarkFantasy #Audiobook #BeingABong #FantasyAudiobook"
    ),

    # 4 Thematic Visual Blocks for Chapters 85 to 112
    "blocks": [
        {
            "index": 1, "range": (85, 91),
            "title": ["THE BLOOD CLAN'S TRUE FORM", "MIST AND BLADE"],
            "fallback_color": (15, 20, 30),
            "prompt": (
                "Cinematic dark fantasy illustration of a female elven warrior with silver irises and white hair wielding an ornate engraved machete, "
                "clashing blades against a terrifying pale vampire with glowing red eyes and blood-stained claws inside a dense, suffocating black fog, "
                "snow-covered battlefield, dramatic volumetric moonlight, octane render, unreal engine 5, 4k digital art."
            )
        },
        {
            "index": 2, "range": (92, 98),
            "title": ["TOWER OF ERADICATION", "THE SEED'S TRIAL"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic dark fantasy scene of a resilient young swordsman in torn armor facing off against an immortal blood clansman in a misty pine forest, "
                "sparks flying from a clash between steel and razor-sharp claws, atmospheric winter fog, cinematic rim lighting, high contrast 4k."
            )
        },
        {
            "index": 3, "range": (99, 105),
            "title": ["THE ALCHEMY BALL", "VETERANS IN THE FOG"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "Cinematic dark fantasy depiction of two grim, battle-scarred veteran warriors confronting each other under a shroud of thick magical alchemy fog, "
                "intense psychological standoff, realistic textures, eerie green and blue moonlight filtering through canopy, masterpiece digital render."
            )
        },
        {
            "index": 4, "range": (106, 112),
            "title": ["METAMORPHOSIS", "MONSTERS OF LEGEND"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic dark fantasy epic climax shot of two ancient supreme-class vampires transforming into terrifying winged gargoyle monsters with massive bat-like wings, "
                "bony spurs, glowing red eyes, and monstrous fangs howling under a crimson moon, photorealistic textures, masterpiece 4k digital art."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
