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

# Credential resolution with multi-key/account fallback
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


def purge_corrupt_or_fallback_cache(build_dir: str):
    """
    Purges placeholder files, corrupt manifests, and rule-based fallback files
    staged during earlier runs without Gemini credentials.
    """
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

                is_dummy = len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows)
                is_fallback_only = not any(r.get("speaker") not in ["Narrator", "Mc", "System"] for r in rows)

                if is_dummy or is_fallback_only:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                try:
                    os.remove(fpath)
                    removed += 1
                except OSError:
                    pass
    if removed > 0:
        print(f"[Pre-Flight Cleanup] [OK] Purged {removed} invalid/fallback staged files. Gemini Director will parse cleanly.", flush=True)


BUILD_DIR = "build_circle_of_inevitability_051_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "circle-of-inevitability",
    "start_url": "https://freewebnovel.com/novel/lord-of-mysteries-2-circle-of-inevitability/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Lord of the Mysteries 2 / Circle of Inevitability / Lumian Lee / Aurore / Cordu Time Loop / Alms Monk / Inevitability Ritual",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We return to the cursed mountain village of Cordu as Lumian Lee digs deeper into the looping nightmare, uncovering harrowing sacrifices, heretical conspiracies, and the encroaching terror of inevitable catastrophe.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_circle_of_inevitability_051_100.mp3",
    "final_video": "final_circle_of_inevitability_051_100.mp4",
    "cover_image": "cover_circle_of_inevitability_051_100.jpg",
    "timestamps_file": "youtube_timestamps_circle_of_inevitability_051_100.txt",
    "subtitles_file": "subtitles_circle_of_inevitability_051_100.srt",
    "payload_file": "youtube_upload_payload_circle_of_inevitability_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # Post-Render Multilingual Subtitle Engine (15 Languages to build/subtitles/)
    "enable_subtitles": True,
    "subtitle_languages": [
        "de", "es", "pt", "ru", "hi", "bn", "ms", "tl", "fr", "fi", "ja", "pl", "ur", "ar", "vi"
    ],

    # YouTube Metadata
    "video_title": "Circle of Inevitability (LOTM 2) | Ch 51 - 100 Full Audio Novel Marathon | Unraveling Cordu Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Lord of the Mysteries 2", "Circle of Inevitability", "Circle of Inevitability Audiobook",
        "LOTM 2", "Lumian Lee", "Aurore Lee", "Cordu Village", "Hunter Pathway",
        "Tarot Club", "Occult Mystery", "Lovecraftian Horror", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Lord of the Mysteries 2: Circle of Inevitability' (Chapters 51 to 100) — the Unraveling Cordu Arc.\n\n"
        "As the terrifying truth behind the Cordu village loop comes into sharper focus, Lumian Lee must navigate a labyrinth of madness. "
        "Sinister heretical rites, the mysterious actions of Madame Pualis, the encroaching influence of the Inevitability entity, "
        "and chilling revelations about the villagers force Lumian to push his Hunter abilities to their absolute limits. "
        "Experience the dread, psychological intrigue, and mounting catastrophe in this gripping continuation.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal presence).\n"
        "🎙️ NARRATION: en-US-ChristopherNeural (Deep Cinematic Baritone).\n"
        "📖 CLOSED CAPTIONS: Multilingual Subtitles (15 languages available in Soft CC).\n"
        "🎨 VISUAL ENGINE: Dynamic 4K Visual Arc Blocks + 15s Outro Slate.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\n"
        "This audiobook is an edited, dramatized fan adaptation produced for literature commentary and entertainment purposes.\n\n"
        "#LordOfTheMysteries2 #CircleOfInevitability #LumianLee #LOTM2 #OccultHorror #FantasyAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 51 to 100 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (51, 60),
            "title": ["RITUAL INFILTRATION", "SHADOWS IN THE CHAPEL"],
            "fallback_color": (25, 20, 25),
            "prompt": (
                "Cinematic Victorian gaslamp horror interior of a dark stone church crypt illuminated by flickering blue candle flames, "
                "a young hunter with an iron axe creeping behind an ancient gothic column, observing robed cultists performing a ritual "
                "around an altar draped in thorns, volumetric shadows, eerie atmospheric 4K rendering."
            )
        },
        {
            "index": 2, "range": (61, 70),
            "title": ["THE LADY OF THE CASTLE", "OCCULT ENTANGLEMENTS"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic psychological horror scene inside an opulent vintage French-style castle parlor, an elegant noblewoman with a mysterious subtle smile "
                "holding a decorative porcelain teacup, surreal warped mirrors on the walls displaying shifting lizard-like shadows, "
                "soft golden chandelier light, dramatic composition."
            )
        },
        {
            "index": 3, "range": (71, 80),
            "title": ["DANSE MACABRE", "THE ALMS MONK"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic dark fantasy composition of an eerie dirt plaza in Cordu village under an indigo twilight sky, "
                "villagers moving in an unsettling synchronized dance around a bizarre robed monk figure holding a begging bowl, "
                "swirling mystical violet dust, uncanny atmosphere, sharp focus."
            )
        },
        {
            "index": 4, "range": (81, 90),
            "title": ["FRACTURED CYCLES", "DESPERATE STAND"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic high-octane occult combat sequence outside a burning stone cottage, the young hunter wielding flame-wreathed daggers "
                "leaping forward against terrifying mutated shadow beasts with elongated limbs, embers dancing in the air, "
                "dramatic motion blur, intense rim lighting."
            )
        },
        {
            "index": 5, "range": (91, 100),
            "title": ["APPROACHING DISASTER", "THE LOOMING APEX"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic wide angle apocalyptic vista of Cordu village surrounded by jagged mountain peaks, "
                "a massive celestial distortion in the stormy clouds above revealing faint swirling cosmic circles and crimson omens, "
                "the young protagonist standing with his sister on a cliffside preparing for the fateful culmination, masterpiece rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
