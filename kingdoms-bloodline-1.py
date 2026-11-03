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

def purge_corrupt_cache(build_dir: str):
    """Purges placeholder dummy files from earlier connection dropouts."""
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
                if len(rows) < 8 or any("Exposition details continue" in r.get("text", "") for r in rows):
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

BUILD_DIR = "build_kingdoms_bloodline_1_35"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "kingdoms-bloodline",
    "start_url": "https://freewebnovel.com/novel/kingdoms-bloodline/chapter-1",
    "start_chapter": 1,
    "end_chapter": 35,
    "default_topic": "Kingdom's Bloodline",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Reborn as a destitute beggar child on the blood-soaked streets of a fractured fantasy empire, an ordinary soul discovers he carries the perilous royal bloodline of the iron-willed Constellation dynasty.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_kingdoms_bloodline_1_35.mp3",
    "final_video": "final_kingdoms_bloodline_1_35.mp4",
    "cover_image": "cover_kingdoms_bloodline_1_35.jpg",
    "timestamps_file": "youtube_timestamps_kingdoms_bloodline_1_35.txt",
    "subtitles_file": "subtitles_kingdoms_bloodline_1_35.srt",
    "payload_file": "youtube_upload_payload_kingdoms_bloodline_1_35.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "ROYAL BLOODLINE & SLUM BEGGAR AWAKENING! [Ch 1-35] | Kingdom's Bloodline Epic Fantasy Audiobook",
    "tags": [
        "Kingdoms Bloodline", "Kingdom's Bloodline", "Epic Fantasy Audiobook", "Dark Fantasy",
        "Political Fantasy", "Reincarnation", "Royal Bloodline", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the opening marathon of 'Kingdom's Bloodline' covering Chapters 1 through 35!\n\n"
        "Awakening in the body of Thales, a ragged beggar orphan surviving in the filth and crime-ridden underworld "
        "of the Lower City, he soon learns that his blood holds the key to an empire teetering on civil war. Hunted by "
        "deadly assassins, treacherous noble houses, and ancient monstrous races, Thales must weaponize pure intellect, "
        "cunning diplomacy, and unwavering resolve to survive the treacherous court of the Constellation Kingdom. "
        "Experience this 35-chapter arc with multi-voice neural TTS, context-aware acoustic soundscapes, and full soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for all dialogue, internal monologues, and narrative prose).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and political fantasy sagas!\n\n"
        "#KingdomsBloodline #EpicFantasy #DarkFantasy #PoliticalFantasy #Audiobook #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Ch 1 to 35: 1-9, 10-18, 19-27, 28-35)
    "blocks": [
        {
            "index": 1, "range": (1, 9),
            "title": ["SLUM ASHES", "ORPHANED PRINCE"],
            "fallback_color": (25, 20, 20),
            "prompt": (
                "Cinematic 3D dark fantasy illustration of a slender 7-year-old beggar boy dressed in tattered woolen rags, "
                "standing in a cold, rainy medieval cobblestone slum alleyway with intense, piercing intelligent eyes. "
                "Dim lantern light flickering off wet stone walls, shadows lurking in the background, realistic skin and dirty face textures, "
                "dramatic volumetric fog, medium shot, high realism 4k render."
            )
        },
        {
            "index": 2, "range": (10, 18),
            "title": ["BLOODLINE CALL", "SHADOW ASSASSINS"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "Cinematic 3D dark fantasy scene of the young boy surrounded by cloaked royal guards and shadowy assassin figures "
                "in a dilapidated subterranean cellar, drawn steel blades reflecting faint torchlight. "
                "The boy stands calm and observant, ancient constellation crest faintly glowing behind him, crisp cloth and chainmail textures, "
                "dramatic chiaroscuro lighting, 4k digital art style."
            )
        },
        {
            "index": 3, "range": (19, 27),
            "title": ["MIND PALACE", "COURT INTRIGUE"],
            "fallback_color": (30, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the young prince dressed in a clean dark-grey noble doublet with subtle silver embroidery, "
                "sitting at a massive oak study table with antique maps and wax-sealed letters, deep in calculated thought. "
                "Stately gothic stone hall background with towering arched stained-glass windows, soft candle illumination, highly detailed facial features."
            )
        },
        {
            "index": 4, "range": (28, 35),
            "title": ["ROYAL MANEUVERS", "THE CONSTELLATION EMBLEM"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D epic fantasy view of the young protagonist standing before an imposing throne room dais flanked by towering armored knights, "
                "confronting hostile high nobles beneath the grand starry banner of the Constellation Kingdom. "
                "Warm grand chandelier lighting, banners fluttering, intense political tension, grand scale, masterpiece 4k rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
