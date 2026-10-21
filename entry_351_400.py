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

BUILD_DIR = "build_entry_cultivation_351_400"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-351/",
    "start_chapter": 351,
    "end_chapter": 400,
    "default_topic": "Entry Cultivation",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_entry_cultivation_351_400.mp3",
    "final_video": "final_entry_cultivation_351_400.mp4",
    "cover_image": "cover_entry_cultivation_351_400.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_351_400.txt",
    "subtitles_file": "subtitles_entry_cultivation_351_400.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_351_400.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SUPREME ENTRY DUPLICATION & SECT WARFARE! [Ch 351-400] | Cultivation Progression Fantasy Audiobook Marathon",
    "tags": [
        "Entry Cultivation I Can Copy Entries", "Entry Cultivation", "Progression Fantasy",
        "Cultivation LitRPG", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Ascending past regional constraints, our entry-copying master plunges headfirst into the high-stakes theater of grand sect warfare!\n\n"
        "Leveraging his cheat-level capability to duplicate elite talents, supreme physiques, and heavenly daos from friends and foes alike, "
        "he outsmarts ancient orthodox patriarchs and slaughters arrogant legacy disciples. Every stolen entry transforms his foundation "
        "into an indestructible engine of martial supremacy.\n\n"
        "Welcome to Chapters 351 to 400 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 351: Stealing the Divine Phoenix Entry: Upgrading Bloodline Potential\n"
        "• Ch 358: Sect Master Confrontation: Plundering Core Legacy Techniques\n"
        "• Ch 365: Ancient Battlefield Incursion: Harvesting Fallen Immortal Entries\n"
        "• Ch 372: Pill Emperor Legacy: Copying Supreme Alchemical Mastery\n"
        "• Ch 379: Coalition Ambush: Turning Enemy Arrays Against Themselves\n"
        "• Ch 386: Sword Soul Metamorphosis: Duplicating Absolute Edge Intent\n"
        "• Ch 393: Heavenly Tribulation Manipulation: Crafting Custom Lightning Armor\n"
        "• Ch 400: Claiming Sovereign Dominance Over the Eastern Wastes\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (351, 355),
            "title": ["PHOENIX ENTRY", "BLOODLINE THEFT"],
            "fallback_color": (35, 15, 15),
            "prompt": (
                "Cinematic 3D portrait of a sharp-eyed cultivation master reaching toward a glowing golden entry panel floating in mid-air, "
                "confident smirk, wearing sleek black and crimson robes embroidered with silver runic patterns. Set inside an ancient flame-lit immortal cavern, "
                "revealing a majestic scarlet phoenix spirit silhouette manifesting behind him in the distance. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (356, 360),
            "title": ["SECT MASTER DUEL", "LEGACY PLUNDER"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the master clashing palms with an arrogant orthodox sect leader, calm commanding posture, "
                "surrounded by dazzling shockwaves of azure and gold qi energy. Set above a crumbling mountain summit fortress under turbulent clouds. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (361, 365),
            "title": ["ANCIENT BATTLEFIELD", "IMMORTAL HARVEST"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of the master walking across a desolate war-torn valley while extracting glowing blue entry shards from ancient weapon remnants, "
                "analytical focus, eerie violet fog rolling across the ground. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (366, 370),
            "title": ["PILL EMPEROR", "ALCHEMICAL MASTERY"],
            "fallback_color": (40, 30, 15),
            "prompt": (
                "Cinematic 3D portrait of the master controlling a massive multi-layered bronze cauldron with one hand, relaxed triumphant expression, "
                "warm amber fire glow reflecting off his facial features. Set inside an opulent pill-refining pavilion filled with floating medicinal herbs. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (371, 375),
            "title": ["COALITION AMBUSH", "ARRAY REVERSAL"],
            "fallback_color": (30, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the master snapping his fingers as an enemy trapping array shatters back onto its casters, "
                "cold calculating smirk, runic light reflecting off his sleeves. Set in a deep stone gorge surrounded by trapped hostile elders. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (376, 380),
            "title": ["SWORD SOUL", "ABSOLUTE EDGE"],
            "fallback_color": (15, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of the master standing with eyes closed as thousands of floating spectral swords form a protective halo around him, "
                "serene powerful aura, sharp wind pressure bending the grass. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (381, 385),
            "title": ["HEAVENLY TRIBULATION", "LIGHTNING ARMOR"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the master absorbing raging violet lightning bolts directly into his skin to forge a crackling conductive armor set, "
                "fearless resolute posture. Set on a blasted mountaintop under an apocalyptic thunderstorm. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (386, 390),
            "title": ["SECT PURGE", "DOMINANCE ASSERTED"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D portrait of the master sitting upon a conquered jade throne while hostile patriarchs bow in submission, "
                "regal sovereign authority, grand ancestral hall backdrop. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (391, 395),
            "title": ["VOID CHAMBER", "DIMENSIONAL TEAR"],
            "fallback_color": (25, 15, 40),
            "prompt": (
                "Cinematic 3D portrait of the master inspecting a shimmering spatial rift with glowing purple energy tendrils, "
                "curious experimental focus, dark starfield background reflecting in his eyes. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (396, 400),
            "title": ["EASTERN WASTES", "SOVEREIGN CROWN"],
            "fallback_color": (20, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the supreme regional lord standing atop a towering mountain pinnacle under a golden sunrise, "
                "serene invincible expression, flowing dark robes adorned with starlight badges. Set overlooking boundless cultivated territories. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
