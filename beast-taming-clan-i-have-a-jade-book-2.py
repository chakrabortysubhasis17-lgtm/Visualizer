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

BUILD_DIR = "build_beast_taming_clan_36_70"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "beast-taming-clan-i-have-a-jade-book",
    "start_url": "https://freewebnovel.com/novel/beast-taming-clan-i-have-a-jade-book/chapter-36",
    "start_chapter": 36,
    "end_chapter": 70,
    "default_topic": "Beast Taming Clan",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Full Mir-Style Dynamic Intro Sequence Passed in intro_hook
    "intro_hook": [
        {
            "line_id": "intro_01_hook",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "In our previous chapters, guided by the revelations of the heavenly Jade Book, our young cultivator nurtured "
                "rare spiritual beast bloodlines and broke through ancestral thresholds. But sudden prominence brought dangerous eyes, "
                "and greedy rival sects have gathered at the mountain borders, determined to plunder the clan's spiritual foundation."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "chime",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 0.4,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_02_body",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": (
                "Welcome back to Being a Bong. We narrate the unreal worlds to life. "
                "In this episode, we step right back into the series, picking up immediately where the tribulation thunder left off, "
                "take a second to hit that like button, subscribe if you are new to the channel, and drop your thoughts in the comments. "
                "Your support is the engine that keeps this massive releases alive. "
                "Settle in as the beast horde prepares to defend the valley, adjust your volume, and let's begin today's episode."
            ),
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_lead_in_pause",
            "speaker": "Narrator",
            "gender": "Male",
            "line_type": "Narration",
            "text": "",
            "pause_duration": 1.0,
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "rate": "+0%",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_beast_taming_clan_36_70.mp3",
    "final_video": "final_beast_taming_clan_36_70.mp4",
    "cover_image": "cover_beast_taming_clan_36_70.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_clan_36_70.txt",
    "subtitles_file": "subtitles_beast_taming_clan_36_70.srt",
    "payload_file": "youtube_upload_payload_beast_taming_clan_36_70.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "MYTHICAL BLOODLINE ASCENT & SECT WAR! [Ch 36-70] | Beast Taming Clan Xianxia Full Audiobook",
    "tags": [
        "Beast Taming Clan", "Jade Book", "Xianxia Audiobook", "Cultivation Audiobook",
        "Beast Tamer", "Clan Building", "Progression Fantasy", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Beast Taming Clan: I Have A Jade Book' with Chapters 36 through 70!\n\n"
        "Leveraging the secrets of the Jade Book, our protagonist guides his spiritual beasts through rare elemental mutations "
        "and tribulation breakthroughs, solidifying his family's rising status. But as rival sects conspire to seize their "
        "spiritual grounds, the clan must rally their evolved beasts for all-out sect warfare. Experience this 35-chapter "
        "marathon with multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for all dialogue, spirit pacts, and cultivation stats).\n"
        "🎨 VISUAL ENGINE: High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more chapters and cultivation updates!\n\n"
        "#BeastTamingClan #JadeBook #Xianxia #CultivationAudiobook #ProgressionFantasy #BeingABong"
    ),

    # Visual Prompts (4 thematic blocks covering Ch 36 to 70: 36-44, 45-53, 54-62, 63-70)
    "blocks": [
        {
            "index": 1, "range": (36, 44),
            "title": ["BLOODLINE TRIBULATION", "SPIRITUAL REFINEMENT"],
            "fallback_color": (20, 35, 20),
            "prompt": (
                "Cinematic 3D cultivation fantasy illustration of a young Daoist cultivator standing under a stormy sky, "
                "his jade book glowing brilliantly as golden lightning strikes an evolving winged spiritual serpent beside him. "
                "Mountain peak training arena, swirling spiritual Qi vortex, crisp cloth textures, dramatic atmospheric lighting."
            )
        },
        {
            "index": 2, "range": (45, 53),
            "title": ["SECT CONSPIRACY", "CLAN DEFENSE ARRAYS"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "Cinematic 3D xianxia scene of the young clan leader atop high fortress ramparts directing a massive golden defensive array dome, "
                "protecting the lush spiritual beast valley from invading hostile cultivators on flying swords. "
                "Floating talisman banners, glowing array runes, deep dusk sky, highly detailed architecture, 4k render."
            )
        },
        {
            "index": 3, "range": (54, 62),
            "title": ["MUTATED APEX BEAST", "THUNDER VORTEX"],
            "fallback_color": (35, 25, 20),
            "prompt": (
                "Cinematic 3D fantasy action portrait of the protagonist alongside a towering mutated thunder-tiger beast "
                "with glowing horns and crackling violet lightning along its armored flanks, roaring at rival sect elders. "
                "Cracked mountain terrain, drifting spiritual embers, cinematic rim lighting, crisp 3D character design."
            )
        },
        {
            "index": 4, "range": (63, 70),
            "title": ["TERRITORIAL TRIUMPH", "CLAN PILLAR ESTABLISHED"],
            "fallback_color": (15, 25, 35),
            "prompt": (
                "Cinematic 3D epic fantasy view of the victorious young clan master seated in an ornate open-air mountain pavilion, "
                "surrounded by multiple docile mythical beasts and bowing clan disciples under a vibrant sunrise over misty karst peaks. "
                "Cherry blossom petals drifting on the wind, golden morning light, serene and commanding atmosphere, masterpiece 4k render."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
