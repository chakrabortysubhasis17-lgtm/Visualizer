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

BUILD_DIR = "build_sss_rank_goddess_301_350"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-301",
    "start_chapter": 301,
    "end_chapter": 350,
    "default_topic": "SSS-Rank Goddess Summon",

    # Concurrency & Synthesis Parameters
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_sss_rank_goddess_301_350.mp3",
    "final_video": "final_sss_rank_goddess_301_350.mp4",
    "cover_image": "cover_sss_rank_goddess_301_350.jpg",
    "timestamps_file": "youtube_timestamps_sss_rank_goddess_301_350.txt",
    "subtitles_file": "subtitles_sss_rank_goddess_301_350.srt",
    "payload_file": "youtube_upload_payload_sss_rank_goddess_301_350.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "DIVINE REALM ASCENSION & CELESTIAL PACT! [Ch 301-350] | Starting With An SSS-Rank Goddess Summon",
    "tags": [
        "Starting With An SSS-Rank Goddess Summon", "SSS Rank Goddess Summon", 
        "LitRPG Audiobook", "Progression Fantasy", "Fantasy Audiobook", 
        "Goddess Summon", "System Summoning", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong! Grab your headphones and get cozy. You are about to enjoy hours of non-stop story completely free—made with endless coffee and a whole lot of heart.\n\n"
        "In return, just show me two seconds of love! Hit like, share the vibe, and tap Subscribe. Think of your subscription as the spark that keeps this channel running—without it, the next marathon loses motivation! So tap that button, relax, and let the adventure begin.\n\n"
        "In Chapters 301 to 350, our summoner ascends past mortal planar barriers into higher divine territories. "
        "With top-tier SSS-rank contracts evolving into cosmic goddess forms, ancient planar lords and interdimensional conquerors discover "
        "what happens when an unmatched summoner brings absolute celestial firepower to the battlefield.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, Pedalboard vocal smoothing DSP, multi-voice dramatization).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 4K 3D Fantasy Visual Artworks + 15s Animated Outro.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 MARATHON ARC BREAKDOWN:\n"
        "• Ch 301 - 310: Divine Domain Breach & Primordial Incursion\n"
        "• Ch 311 - 320: Heavenly Warfront & SSS-Tier Synergy\n"
        "• Ch 321 - 330: Ancient Abyss Trial & Celestial Artifact Awakening\n"
        "• Ch 331 - 340: Monarch Realm Showdown & God-Slaying Array\n"
        "• Ch 341 - 350: Supreme Pantheon Ascension & Sovereign Rule\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited, dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for upcoming marathons!\n\n"
        "#SSSRankGoddessSummon #FantasyAudiobook #ProgressionFantasy #LitRPG #SystemSummoning #AudiobookMarathon #BeingABong"
    ),

    # Visual Prompts (5 blocks, 10 chapters each)
    "blocks": [
        {
            "index": 1, "range": (301, 310),
            "title": ["DIVINE DOMAIN", "PRIMORDIAL INCURSION"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D fantasy portrait of a powerful young male summoner in silver-trimmed dark trenchcoat robes, "
                "standing shoulder-to-shoulder with a radiant celestial goddess with long platinum hair, luminous white wings, "
                "and glowing golden eyes. Floating ancient summon grimoire between them, glowing arcane summoning rings on the ground, "
                "celestial temple ruins background under a violet twilight sky, ultra-fine textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (311, 320),
            "title": ["HEAVENLY WARFRONT", "SSS SYNERGY"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D fantasy portrait of the determined male summoner channeling golden radiant energy from his palms, "
                "flanked by a majestic battle goddess in sculpted golden plate armor wielding a blazing crystal spear. "
                "Floating shattered citadel background, dynamic particle embers, lens flares, crisp detailed facial features, "
                "volumetric lighting, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (321, 330),
            "title": ["ANCIENT ABYSS", "ARTIFACT AWAKENING"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D fantasy portrait of the summoner holding a hovering obsidian relic pulsing with cosmic nebula light, "
                "accompanied by a mysterious dark-robed shadow goddess with floating amethyst crystals and ethereal horns. "
                "Subterranean crystal cavern background with glowing runes, atmospheric mist, high-contrast dramatic rim lighting, "
                "intricate cloth and armor details, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (331, 340),
            "title": ["MONARCH SHOWDOWN", "GOD-SLAYING ARRAY"],
            "fallback_color": (40, 15, 20),
            "prompt": (
                "Cinematic 3D fantasy portrait of the summoner surrounded by five colossal hovering elemental glyphs and runic magic circles, "
                "gazing fiercely upward toward a cracked cosmic sky while commanding multiple divine spirit apparitions. "
                "Explosive magical battlefield background with crimson thunder and lightning, cinematic motion blur, sharp facial focus, "
                "photorealistic skin rendering, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (341, 350),
            "title": ["PANTHEON ASCENT", "SOVEREIGN RULE"],
            "fallback_color": (30, 15, 50),
            "prompt": (
                "Cinematic 3D fantasy portrait of the Supreme Summoner seated upon a floating starlight throne, "
                "flanked by majestic divine goddesses holding sacred scepters and celestial blades beneath a swirling galaxy halo. "
                "Luminous translucent system interface screens displaying SSS-rank evolution stats, opulent marble pillars, "
                "regal ambiance, volumetric god rays, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
