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

BUILD_DIR = "build_beast_taming_clan_1_35"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "beast-taming-clan-i-have-a-jade-book",
    "start_url": "https://freewebnovel.com/novel/beast-taming-clan-i-have-a-jade-book/chapter-1",
    "start_chapter": 1,
    "end_chapter": 35,
    "default_topic": "Beast Taming Clan",

    # Concurrency Settings & Narrator Lock
    "batch_size": 7,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # 1-Liner Story Intro Hook
    "intro_hook": "Armed with a mysterious heavenly jade book capable of unravelling spiritual beast bloodlines, a young clan cultivator embarks on a journey to defy destiny and elevate his declining family to imperial glory.",

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_beast_taming_clan_1_35.mp3",
    "final_video": "final_beast_taming_clan_1_35.mp4",
    "cover_image": "cover_beast_taming_clan_1_35.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_clan_1_35.txt",
    "subtitles_file": "subtitles_beast_taming_clan_1_35.srt",
    "payload_file": "youtube_upload_payload_beast_taming_clan_1_35.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "HEAVENLY JADE BOOK & SPIRIT BEAST REFINEMENT! [Ch 1-35] | Beast Taming Clan Xianxia Full Audiobook",
    "tags": [
        "Beast Taming Clan", "Jade Book", "Xianxia Audiobook", "Cultivation Audiobook",
        "Beast Tamer", "Clan Building", "Progression Fantasy", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the opening marathon of 'Beast Taming Clan: I Have A Jade Book' covering Chapters 1 through 35!\n\n"
        "Reborn into a struggling spiritual beast-taming clan on the remote edges of the cultivation world, our young protagonist "
        "uncovers a primordial Jade Book that reveals hidden evolutionary paths, bloodline affinities, and ancient beast mutations. "
        "Follow his rise as he forms deep soul-bonds, refines mythical companions, and defends his kin against greedy rival factions. "
        "Experience this 35-chapter arc with multi-voice neural TTS, context-aware acoustic soundscapes, and full synchronized soft subtitles.\n\n"
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

    # Visual Prompts (4 thematic blocks covering Ch 1 to 35: 1-9, 10-18, 19-27, 28-35)
    "blocks": [
        {
            "index": 1, "range": (1, 9),
            "title": ["JADE BOOK AWAKENING", "SPIRIT BEAST PACT"],
            "fallback_color": (15, 35, 25),
            "prompt": (
                "Cinematic 3D xianxia fantasy illustration of a determined young male cultivator in flowing azure and white Daoist robes, "
                "holding an ancient glowing translucent green jade scripture hovering between his palms. "
                "A small winged spiritual serpent with iridescent scales coiled gently around his forearm, glowing golden spiritual runes in the air. "
                "Misty bamboo valley background, towering karst mountains, sharp morning sunlight, detailed face, 4k digital art style."
            )
        },
        {
            "index": 2, "range": (10, 18),
            "title": ["CLAN FOUNDATION", "BLOODLINE EVOLUTION"],
            "fallback_color": (30, 25, 15),
            "prompt": (
                "Cinematic 3D cultivation fantasy portrait of the young beast tamer meditating before a massive spiritual breeding pool in a mountain cavern, "
                "surrounded by glowing alchemical cauldrons and evolving spirit beasts covered in radiant elemental auras. "
                "Volumetric steam, glowing emerald spirit grass, ancient stone clan pavilions in background, crisp cloth textures, cinematic lighting."
            )
        },
        {
            "index": 3, "range": (19, 27),
            "title": ["TRIBULATION CLASH", "ANCIENT MUTATION"],
            "fallback_color": (35, 20, 20),
            "prompt": (
                "Cinematic 3D action scene of the protagonist standing atop a rocky precipice alongside a towering mutated thunder-tiger beast "
                "with crackling azure lightning across its armored fur, facing dark storm clouds and approaching rival sect cultivators. "
                "Swirling wind, floating talismans, dramatic hero stance, cinematic rim lighting, highly detailed 3D render."
            )
        },
        {
            "index": 4, "range": (28, 35),
            "title": ["TERRITORIAL ASCENT", "BEAST PACK CONVERGENCE"],
            "fallback_color": (20, 20, 35),
            "prompt": (
                "Cinematic 3D epic fantasy view of the young clan leader commanding a flying spiritual avian beast over a fortified mountain stronghold, "
                "defensive golden array domes shimmering across the clan valley while a loyal herd of spirit beasts guards the valley pass. "
                "Dusk sky with twin glowing moons, drifting cherry blossoms and spiritual embers, grand scale, masterpiece 4k rendering."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
