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

BUILD_DIR = "build_starting_with_sss_rank_goddess_251_300"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    # Credentials
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    # Novel & Episode Parameters
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-251",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "SSS Goddess Summon",

    # Concurrency Settings
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_starting_with_sss_rank_goddess_251_300.mp3",
    "final_video": "final_starting_with_sss_rank_goddess_251_300.mp4",
    "cover_image": "cover_starting_with_sss_rank_goddess_251_300.jpg",
    "timestamps_file": "youtube_timestamps_starting_with_sss_rank_goddess_251_300.txt",
    "subtitles_file": "subtitles_starting_with_sss_rank_goddess_251_300.srt",
    "payload_file": "youtube_upload_payload_starting_with_sss_rank_goddess_251_300.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "PRIMORDIAL PANTHEON AWAKENING! APEX GODDESS REIGN [Ch 251-300] | Progression Fantasy LitRPG Marathon",
    "tags": [
        "Starting With An SSS-Rank Goddess Summon", "SSS Rank Goddess Summon", "Progression Fantasy",
        "Goddess Summoning", "LitRPG Audiobook", "System Audiobook", "Audiobook Marathon", "Full Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Entering the highest echelons of the Primordial Pantheon, our master summoner commands the fabric of cosmic law!\n\n"
        "With his SSS-rank goddesses reaching their ultimate divinity stages, his summoning array manifests reality-altering authorities. "
        "Overcoming ancient cosmic entities, conquering forbidden void rifts, and shattering the seals of fallen creators, he secures "
        "an everlasting epoch of sovereignty for his allied deities.\n\n"
        "Welcome to Chapters 251 to 300 of 'Starting with an SSS-Rank Goddess Summon' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 251: Arrival at the Origin Well: Primordial Divine Energy Attunement\n"
        "• Ch 257: Goddess of War Transcendence: Supreme Domain Cleave\n"
        "• Ch 264: Cosmic Law Crucible: Forging the Infinite Summoner Grimoire\n"
        "• Ch 271: Primordial Rift Incursion: Repelling the Void Behemoths\n"
        "• Ch 278: Chrono-Goddess Union: Mastering the River of Time\n"
        "• Ch 285: Grand Pantheon Tournament: Crushing Elder Deities with Absolute Synergy\n"
        "• Ch 292: Genesis Relic Reclamation: Unlocking the Origin Domain Core\n"
        "• Ch 300: Apex Cosmic Sovereignty: The Immortal Summoner's Eternal Realm\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#StartingWithAnSSSRankGoddessSummon #SSSRankGoddessSummon #LitRPG #ProgressionFantasy #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (251, 255),
            "title": ["ORIGIN WELL", "PRIMORDIAL FLUX"],
            "fallback_color": (15, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of a powerful young summoner standing at the edge of a swirling cosmic pool of liquid starlight, "
                "calm authoritative eyes, dressed in midnight-blue sovereign robes trimmed with celestial gold filigree. "
                "Set upon a floating crystal platform in deep space, revealing multiple ethereal goddess silhouettes hovering with divine halos in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 2, "range": (256, 260),
            "title": ["WAR GODDESS", "SUPREME CLEAVE"],
            "fallback_color": (30, 15, 25),
            "prompt": (
                "Cinematic 3D portrait of the summoner standing proudly beside a fierce warrior goddess wielding a giant greatsword of white flame, "
                "confident commanding expression, surrounded by floating scarlet battle runes. Set atop a scorched obsidian plateau under a crimson aurora, "
                "revealing shattered mountains split by divine sword light in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 3, "range": (261, 265),
            "title": ["COSMIC CRUCIBLE", "INFINITE GRIMOIRE"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of the summoner holding open a massive floating golden grimoire radiating prismatic divine script, "
                "analytical intense focus, golden runes reflecting brightly off his face. Set inside an ancient cosmic clockwork library, "
                "revealing floating planetary orbs and constellation maps in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 4, "range": (266, 270),
            "title": ["VOID RIFT", "BEHEMOTH PURGE"],
            "fallback_color": (20, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the summoner raising an ornate staff of pure celestial light, fearless resolute posture, "
                "translucent protective ward rings humming around him. Set on the precipice of a torn spatial rift in a shattered galaxy, "
                "revealing colossal dark void beasts being vaporized by holy divine light in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 5, "range": (271, 275),
            "title": ["TIME GODDESS", "CHRONO MATRIX"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner observing a beautiful goddess of time manipulating a floating hourglass of silver sand, "
                "serene contemplative smile, subtle spatial ripple waves distorting the air around them. Set in a quiet sanctum with reflective mirror floors, "
                "revealing frozen celestial constellations hanging motionlessly in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 6, "range": (276, 280),
            "title": ["PANTHEON ARENA", "DUAL MASTERY"],
            "fallback_color": (20, 25, 50),
            "prompt": (
                "Cinematic 3D portrait of the summoner watching from an ornate imperial terrace, relaxed victorious demeanor, "
                "wearing ceremonial embroidered master robes. Set overlooking a colossal celestial colosseum suspended above a glowing nebula, "
                "revealing his twin summoned goddesses driving back rival elder deities in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 7, "range": (281, 285),
            "title": ["GENESIS RELIC", "ORIGIN CORE"],
            "fallback_color": (35, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of the summoner reaching out to grasp a floating crystalline genesis cube of pure rainbow energy, "
                "intense awe and determination, brilliant divine rays illuminating his face. Set in a primordial chamber built from carved celestial bedrock, "
                "revealing ancient guardian statues bowing in solemn reverence in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 8, "range": (286, 290),
            "title": ["DIVINE TRIBULATION", "CELESTIAL REFORGE"],
            "fallback_color": (25, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner channeling descending cosmic thunderbolts into his summoner core, unyielding iron will, "
                "eyes glowing with brilliant white lightning. Set upon a cracked floating asteroid during a cosmic storm, "
                "revealing multiple divine barrier shields deflecting celestial lightning strikes in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 9, "range": (291, 295),
            "title": ["CELESTIAL LEGION", "GRAND FORMATION"],
            "fallback_color": (20, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of the summoner drawing his ceremonial blade and directing cosmic battle formations, commanding authoritative gaze, "
                "cloak billowing in an ethereal solar wind. Set upon the prow of a grand flying astral warship, "
                "revealing thousands of golden armored valkyries and angels soaring into formation in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        },
        {
            "index": 10, "range": (296, 300),
            "title": ["COSMIC SOVEREIGN", "ETERNAL THRONE"],
            "fallback_color": (15, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of the supreme sovereign summoner seated upon an elevated carved throne of starlight and white gold, "
                "serene invincible gaze, draped in flowing dark platinum robes adorned with cosmic star charts. "
                "Set in a vast cosmic throne sanctuary overlooking countless galaxy spirals under golden dawn light, "
                "revealing his full pantheon of SSS-rank goddesses standing loyally beside him in the distance. "
                "Crisp detailed facial features, realistic skin textures, medium close-up shot."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
