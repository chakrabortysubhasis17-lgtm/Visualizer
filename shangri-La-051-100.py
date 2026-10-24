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


BUILD_DIR = "build_shangrila_frontier_051_100"
purge_corrupt_or_fallback_cache(BUILD_DIR)

CONFIG = {
    # Credentials resolved from api_credentials.json
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "shangrila-frontier",
    "start_url": "https://freewebnovel.com/novel/shangriLa-frontier-shitty-games-hunter-challenges-godly-game/chapter-53",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Shangri-La Frontier / VRMMO / Sunraku / Wezaemon the Tombguard / Setsuna",

    # Concurrency & Locked Narrator Voice Settings
    "batch_size": 3,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook (Since start_chapter > 1, pipeline prefixes continuation intro)
    "intro_hook": "We rejoin Sunraku as he joins forces with Arthur Pencilgon and Oikatzo to challenge the legendary Colossus, Wezaemon the Tombguard.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_shangrila_frontier_051_100.mp3",
    "final_video": "final_shangrila_frontier_051_100.mp4",
    "cover_image": "cover_shangrila_frontier_051_100.jpg",
    "timestamps_file": "youtube_timestamps_shangrila_frontier_051_100.txt",
    "subtitles_file": "subtitles_shangrila_frontier_051_100.srt",
    "payload_file": "youtube_upload_payload_shangrila_frontier_051_100.json",

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
    "video_title": "Shangri-La Frontier | Ch 51 - 100 Full Audio Novel Marathon | Wezaemon the Tombguard Arc",
    "privacy_status": "unlisted",
    "tags": [
        "Shangri-La Frontier", "Shangri La Frontier Audiobook", "Sunraku", "Rakuro Hizutome",
        "Arthur Pencilgon", "Oikatzo", "Wezaemon the Tombguard", "Setsuna of the Bygone Days",
        "VRMMO Audiobook", "LitRPG Audiobook", "Progression Fantasy", "Audiobook Marathon",
        "Web Novel Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to Being a Bong!\n\n"
        "Experience the complete 50-chapter audio novel marathon of 'Shangri-La Frontier' (Chapters 51 to 100) — the iconic Wezaemon the Tombguard Arc.\n\n"
        "Rejoining Sunraku as he allies with the PK guild strategist Arthur Pencilgon and top-tier pro gamer Oikatzo. "
        "Bound by the tragic lament of Setsuna of the Bygone Days, the trio embarks on an impossible raid against one of the Seven Colossi: "
        "Wezaemon the Tombguard. Witness flawless parry mechanics, desperate survival tactics against instant-death sword arts, "
        "and the mythical awakening of tactical mech Kirin.\n\n"
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
        "#ShangriLaFrontier #Sunraku #Wezaemon #ArthurPencilgon #Oikatzo #VRMMO #LitRPG #GamingAudiobook #AudiobookMarathon #BeingABong"
    ),

    # 5 Thematic Arc Visual Blocks for Chapters 51 to 100 (10 Chapters each)
    "blocks": [
        {
            "index": 1, "range": (51, 60),
            "title": ["ALLIANCE OF OUTCASTS", "PENCILGON'S GAMBIT"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic anime scene inside a dimly lit tavern cellar, a shirtless male fighter wearing a blue bird mask "
                "sitting at a rough wooden table opposite a beautiful female rogue with long silver hair and an elegant cunning smile, "
                "a muscular martial artist monk looking at battle schematics spread across the table, dramatic lantern glow, high-detail 4K."
            )
        },
        {
            "index": 2, "range": (61, 70),
            "title": ["TOMB OF BYGONE DAYS", "THE GHOST OF SETSUNA"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic ethereal fantasy scene in a ruined subterranean garden filled with glowing blue spectral flowers, "
                "the translucent ghost of a beautiful maiden in archaic robes pointing toward a colossal sealed stone tomb gate, "
                "the bird-masked dual-blade fighter gazing into the mist, soft volumetric radiance, melancholy atmosphere."
            )
        },
        {
            "index": 3, "range": (71, 80),
            "title": ["WEZAEMON AWAKENS", "BLADE OF SEVERANCE"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "Cinematic high-octane battle in a vast circular arena of ancient stone, an imposing samurai warrior clad in decaying mechanical armor "
                "drawing a colossal black nodachi emitting crimson lightning, the bird-masked protagonist executing an acrobat low-slide parry, "
                "sparks flying, dramatic motion blur, epic dark fantasy lighting."
            )
        },
        {
            "index": 4, "range": (81, 90),
            "title": ["TACTICAL STEED KIRIN", "OVERDRIVE CLASH"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic sci-fi fantasy showdown, a gigantic mechanical armored warhorse charging through shattered pillars firing particle beams, "
                "a female spear fighter and monk brawler grappling with the steel behemoth while the bird-masked warrior leaps from above with glowing daggers, "
                "neon energy flares, smoke trails, photorealistic dynamic action."
            )
        },
        {
            "index": 5, "range": (91, 100),
            "title": ["CLEAR SKY OVER THE TOMB", "WORLD RECOGNITION"],
            "fallback_color": (20, 30, 35),
            "prompt": (
                "Cinematic sweeping wide shot at dawn over ancient ruins as the ceiling shatters to reveal a brilliant clear blue sky, "
                "three exhausted adventurers standing victoriously amidst fading golden particles of a defeated colossus, "
                "glowing system notifications floating in the air, warm sunrise rays, masterpiece composition."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
