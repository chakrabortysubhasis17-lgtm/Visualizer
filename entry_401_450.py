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

BUILD_DIR = "build_entry_cultivation_401_450"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-401-catastrophe-secretly-brews-as-storms-rise-the-great-sage-waves-his-staff-to-cause-havoc-in-the-netherworld/",
    "start_chapter": 401,
    "end_chapter": 450,
    "default_topic": "Entry Cultivation",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_entry_cultivation_401_450.mp3",
    "final_video": "final_entry_cultivation_401_450.mp4",
    "cover_image": "cover_entry_cultivation_401_450.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_401_450.txt",
    "subtitles_file": "subtitles_entry_cultivation_401_450.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_401_450.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "HAVOC IN THE NETHERWORLD & GREAT SAGE ASCENT! [Ch 401-450] | Cultivation Progression Fantasy Audiobook",
    "tags": [
        "Entry Cultivation I Can Copy Entries", "Entry Cultivation", "Progression Fantasy",
        "Cultivation LitRPG", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "As catastrophes secretly brew and dark storms gather across the realms, the Great Sage wields his staff to turn the Netherworld upside down!\n\n"
        "With cataclysms threatening the mortal and immortal planes alike, our protagonist steps into forbidden underworld domains, "
        "copying supreme mythological entries, suppressing ghostly sovereigns, and rewriting the rules of reincarnation itself. No hellish "
        "abyss or ancient plotting faction can withstand his unstoppable entry-duplicating momentum.\n\n"
        "Welcome to Chapters 401 to 450 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 401: Catastrophe Brews: Descending into the Roaring Netherworld\n"
        "• Ch 408: Great Sage Staff Waves: Shattering the Ghost Gate Barriers\n"
        "• Ch 415: Underworld Sovereign Subjugation: Harvesting Death Entries\n"
        "• Ch 422: Reincarnation Pool Incursion: Stealing Karma Law Entries\n"
        "• Ch 429: Demonic Uprising Suppression: Purging Nether Abominations\n"
        "• Ch 436: Immortal Court Intervention: Defying Celestial Decrees\n"
        "• Ch 443: Netherworld Throne Domination: Rewriting the Book of Life and Death\n"
        "• Ch 450: Returning to the Upper Realms as a Mythic Overlord\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (401, 405),
            "title": ["NETHERWORLD DESCENT", "CATASTROPHE BREWS"],
            "fallback_color": (20, 15, 30),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of a powerful cultivation master standing at the gloomy shores of the River Styx, "
                "calm piercing gaze, wearing obsidian robes swirling with ghostly green fire motes. Set in a desolate underworld realm under a blood-red moon, "
                "revealing towering weeping willow ghost trees in the distance. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (406, 410),
            "title": ["GREAT SAGE STAFF", "NETHERWORLD HAVOC"],
            "fallback_color": (35, 20, 15),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master wielding a glowing golden iron-banded staff that stretches into the clouds, "
                "confident defiant smirk, surrounded by golden heavenly shockwaves. Set inside a crumbling underworld temple crowded by terrified spectral fiends. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (411, 415),
            "title": ["GHOST GATE", "BARRIER SHATTER"],
            "fallback_color": (15, 30, 25),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master smashing a colossal bronze underworld gate with a single staff strike, "
                "intense dynamic action focus, brilliant blue and gold energy splinters flashing across the stone floor. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (416, 420),
            "title": ["UNDERWORLD SOVEREIGN", "DEATH ENTRY HARVEST"],
            "fallback_color": (25, 15, 35),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master pulling a glowing crimson entry scroll from a defeated ghost king's chest, "
                "cold calculating smirk, swirling dark yin qi energy parting around him. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (421, 425),
            "title": ["REINCARNATION POOL", "KARMA LAW THEFT"],
            "fallback_color": (30, 25, 45),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master hovering above a mystical glowing white karma pool absorbing swirling karmic threads, "
                "profound enlightened focus, celestial lotus aura blooming beneath him. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (426, 430),
            "title": ["DEMONIC UPRISING", "ABOMINATION PURGE"],
            "fallback_color": (40, 15, 15),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master unleashing a roaring golden dragon firestorm that incinerates legions of nether demons, "
                "fearless authoritative posture, blazing inferno background. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (431, 435),
            "title": ["IMMORTAL COURT", "DECREE DEFIANCE"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master holding a shredded imperial celestial decree while confronting golden-armored heavenly generals, "
                "unyielding sovereign confidence. Set in an opulent floating celestial palace hall. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (436, 440),
            "title": ["BOOK OF LIFE AND DEATH", "LAW REWRITTEN"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master writing new destiny entries into an ancient glowing jade ledger using a brush of pure light, "
                "serene triumphant expression. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (441, 445),
            "title": ["UNDERWORLD THRONE", "NETHER DOMINION"],
            "fallback_color": (20, 20, 40),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the master sitting upon a majestic throne of skulls and dark gold inside the Nether Capital, "
                "regal supreme overlord authority, bowing ghost ministers in the background. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (446, 450),
            "title": ["MYTHIC OVERLORD", "RETURN TO THE UPPER REALMS"],
            "fallback_color": (15, 20, 45),
            "prompt": (
                "Cinematic 3D dark fantasy portrait of the supreme mythic overlord rising from the underworld abyss back into the mortal realm through a pillar of golden light, "
                "serene invincible expression, majestic swirling dragon aura. Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
