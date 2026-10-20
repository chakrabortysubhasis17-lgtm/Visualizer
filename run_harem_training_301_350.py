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

# Seamless fallback supporting both single-key and multi-key JSON configurations
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
    """Automatically removes empty or corrupt dummy files from earlier connection aborts."""
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
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} corrupt placeholder cache files to guarantee clean scraping.", flush=True)

BUILD_DIR = "build_harem_training_system_301_350"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "harem-training-system-every-girl-i-train-makes-me-stronger",
    "start_url": "https://freewebnovel.com/novel/harem-training-system-every-girl-i-train-makes-me-stronger/chapter-301",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "Arc",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_harem_training_system_301_350.mp3",
    "final_video": "final_harem_training_system_301_350.mp4",
    "cover_image": "cover_harem_training_system_301_350.jpg",
    "timestamps_file": "youtube_timestamps_harem_training_system_301_350.txt",
    "subtitles_file": "subtitles_harem_training_system_301_350.srt",
    "payload_file": "youtube_upload_payload_harem_training_system_301_350.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "SOVEREIGN REALM ASCENSION! CELESTIAL TRAINING DOMAIN EXPANSION [Ch 301-350] | Progression Fantasy LitRPG Marathon",
    "tags": [
        "Harem Training System", "Every Girl I Train Makes Me Stronger", "Progression Fantasy",
        "Cultivation LitRPG", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Transcending mortal limits, our master trainer leads his disciples across the threshold of the Higher Astral Realms!\n\n"
        "With the Training System evolving into a multi-tiered sovereign resonance matrix, every breakthrough in sword intent, "
        "primordial soul alchemy, and mythical beast symbiosis magnifies his divine foundation. Confronting celestial emissaries, "
        "conquering ancient astral trial domains, and claiming sovereign heritage seats, he demonstrates that unified disciple training "
        "surpasses all solitary cultivation paths.\n\n"
        "Welcome to Chapters 301 to 350 of 'Harem Training System: Every Girl I Train Makes Me Stronger' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 301: The Celestial Boundary Gate: Crossing the Star Stairway\n"
        "• Ch 307: Primordial Meridian Synchrony: Domain Resonance Unlocked\n"
        "• Ch 314: Nirvana Core Alchemy: Brewing Nine-Reversal Elixirs\n"
        "• Ch 321: Ancient Sovereign Vault: Breaking the Nine Heavens Array\n"
        "• Ch 328: Astral Colosseum Domination: Neutralizing Upper Realm Rivals\n"
        "• Ch 335: Space-Time Meridian Alignment: Void Field Resonance\n"
        "• Ch 342: Divine Thunder Tribulation: Quad-Disciple Co-Attunement\n"
        "• Ch 350: Sovereign Palace Coronation: Establishing the Inter-Realm Academy\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HaremTrainingSystem #EveryGirlITrainMakesMeStronger #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (301, 305),
            "title": ["CELESTIAL GATEWAY", "STAR STAIRWAY"],
            "fallback_color": (15, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of a regal young martial master standing before a colossal glowing astral gateway, calm resolute eyes, "
                "wearing midnight-blue robes with flowing platinum embroidery. Set upon an ancient stone platform suspended in deep space, "
                "revealing shimmering nebula clouds and disciplined disciples observing the cosmic threshold in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (306, 310),
            "title": ["DOMAIN RESONANCE", "SWORD HARMONY"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of the master channeling dual energetic resonance alongside a talented swordswoman disciple, "
                "proud confident expression, surrounded by concentric rings of violet and azure sword aura. Set atop a floating jade mountain spire, "
                "revealing celestial light beams cutting through cloud banks in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (311, 315),
            "title": ["NIRVANA ALCHEMY", "PILL REVERSAL"],
            "fallback_color": (45, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the master guiding an alchemist disciple hovering above a glowing magma furnace, focused analytical posture, "
                "warm golden radiance reflecting off his face and sleeves. Set inside an ancient hollow cavern illuminated by crystalline ore, "
                "revealing nine floating celestial pills radiating divine light in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (316, 320),
            "title": ["DRAKE & PHOENIX", "SOUL CONCORD"],
            "fallback_color": (20, 35, 30),
            "prompt": (
                "Cinematic 3D portrait of the master standing calmly as emerald and crimson draconic energies swirl around his hands, "
                "steady reassuring gaze, breeze lifting his dark hair. Set in a primordial sanctuary grove with glowing spirit fauna, "
                "revealing a magnificent azure drake and a fiery phoenix silhouette circling above in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (321, 325),
            "title": ["SOVEREIGN VAULT", "ANCIENT RUNES"],
            "fallback_color": (30, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the master placing his hand on an intricate glowing star seal, composed commanding presence, "
                "ancient silver runic script illuminating his sleeves and fingers. Set in the grand hall of an obsidian subterranean tomb, "
                "revealing towering ancestral statues holding glowing orbs in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (326, 330),
            "title": ["ASTRAL ARENA", "SUPREME CONFLICT"],
            "fallback_color": (20, 25, 55),
            "prompt": (
                "Cinematic 3D portrait of the master watching a tournament match from an elevated royal pavilion, confident slight smirk, "
                "hands resting on a carved marble balustrade. Set overlooking an enormous floating circular arena surrounded by tens of thousands of spectators, "
                "revealing his sword disciple defeating an arrogant upper-realm rival in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (331, 335),
            "title": ["VOID RIFT", "SPACE-TIME MATRIX"],
            "fallback_color": (35, 15, 45),
            "prompt": (
                "Cinematic 3D portrait of the master in focused meditation with a floating purple spatial crystal between his hands, "
                "intense sharp focus, subtle spatial distortion ripples curving around him. Set in a quiet chamber with polished reflective floors, "
                "revealing star maps projected into mid-air across the background. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (336, 340),
            "title": ["EMPRESS HERITAGE", "BLOODLINE WAKE"],
            "fallback_color": (40, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of the master standing protectively behind a noble disciple awakening an imperial golden crown aura, "
                "supportive encouraging smile, sleeves fluttering in an energy updraft. Set in a high-vaulted throne sanctuary beneath stained-glass skylights, "
                "revealing kneeling sect guards pledging allegiance in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (341, 345),
            "title": ["DIVINE TRIBULATION", "QUAD DEFENSE"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the master directing defensive barrier arrays against descending celestial lightning, fearless authoritative posture, "
                "eyes reflecting brilliant blue electrical arcs. Set on a cracked stone mountaintop under turbulent thunderstorm clouds, "
                "revealing four disciples maintaining synchronized ward pillars in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (346, 350),
            "title": ["INTER-REALM PALACE", "SOVEREIGN REIGN"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of the grand master seated upon an ornate white-jade throne overlooking multiple realms, "
                "calm peerless sovereign expression, draped in flowing dark blue robes adorned with gold and silver stars. "
                "Set in a boundless cosmic palace hall under a warm golden sunrise, revealing ranks of disciples and allied elders bowing respectfully. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
