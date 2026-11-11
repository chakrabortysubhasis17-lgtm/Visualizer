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
                if len(rows) < 8 or any("Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", "")) for r in rows):
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

BUILD_DIR = "build_rebirth_60_hk_001_040"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/rebirth-60-i-created-a-business-empire-in-hong-kong/chapter-1-reborn-starting-with-a-usury-debt/",
    "novel_slug": "rebirth-60-hk",
    "start_chapter": 1,
    "end_chapter": 40,
    "default_topic": "Rebirth 60: I Created a Business Empire in Hong Kong",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Standard 5-Beat Intro Hook with Split Character Dialogue & Narrative Teaser
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Gritty Triad Enforcer Voice)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Triad Enforcer",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": '"Pay back the usury loan today, or leave both your arms in Wanchai!"',
            "tts_text": '"Pay back the usury loan today... or leave both your arms in Wahn-chye!"',
            "text": '"Pay back the usury loan today, or leave both your arms in Wanchai!"',
            "voice": "en-US-GuyNeural",
            "pitch": "-1Hz",
            "sfx": "slam",
            "bgm_mood": "tension"
        },
        # Beat 1b: Narrative Teaser Hook (Christopher Anchor)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "authoritative_low",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Pounded by debt collectors in a cramped 1960s Hong Kong tenement, a reborn commercial strategist stares down the triad thugs with icy contempt—ready to turn a death sentence into a multi-billion dollar trade empire!",
            "tts_text": "Pounded by debt collectors in a cramped nineteen-sixties Hong Kong tenement... a reborn commercial strategist stares down the triad thugs with icy contempt... ready to turn a death sentence into a multi-billion dollar trade empire!",
            "text": "Pounded by debt collectors in a cramped 1960s Hong Kong tenement, a reborn commercial strategist stares down the triad thugs with icy contempt—ready to turn a death sentence into a multi-billion dollar trade empire!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 2: Channel Trademark Signature
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "engaged_alert",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "whoosh",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 3: In-Universe Call to Action
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Tycoon Syndicate Decree: To build your commercial empire and support today's massive release, smash the Like button and subscribe to the channel. Conquering Victoria Harbour and out-maneuvering colonial syndicates demands absolute financial vision.",
            "tts_text": "Tycoon Syndicate Decree: To build your commercial empire and support today's massive release, smash the Like button and subscribe to the channel. Conquering Victoria Harbour and out-maneuvering colonial syndicates demands absolute financial vision.",
            "text": "Tycoon Syndicate Decree: To build your commercial empire and support today's massive release, smash the Like button and subscribe to the channel. Conquering Victoria Harbour and out-maneuvering colonial syndicates demands absolute financial vision.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "coin",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 4: Recap Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, decades of modern economic foresight met the turbulent dawn of Hong Kong manufacturing. Now, entering Chapters 1 through 40 of Rebirth 60, the industrial takeover begins. Settle in, and witness the rise of a billionaire.",
            "tts_text": "Previously, decades of modern economic foresight met the turbulent dawn of Hong Kong manufacturing. Now, entering Chapters 1 through 40 of Rebirth 60... the industrial takeover begins. Settle in, and witness the rise of a billionaire.",
            "text": "Previously, decades of modern economic foresight met the turbulent dawn of Hong Kong manufacturing. Now, entering Chapters 1 through 40 of Rebirth 60, the industrial takeover begins. Settle in, and witness the rise of a billionaire.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
        },
        # Beat 5: Transition SFX & Lead-in Silence
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.2,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "rain",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 1.0,
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_rebirth_60_hk_001_040.mp3",
    "final_video": "final_rebirth_60_hk_001_040.mp4",
    "cover_image": "cover_rebirth_60_hk_001_040.jpg",
    "timestamps_file": "youtube_timestamps_rebirth_60_hk_001_040.txt",
    "subtitles_file": "subtitles_rebirth_60_hk_001_040.srt",
    "payload_file": "youtube_upload_payload_rebirth_60_hk_001_040.json",

    # Clean Branding Overlay Configuration
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "REBIRTH 60: I CREATED A BUSINESS EMPIRE IN HONG KONG! [Chapters 1-40] | Tycoon Progression Audiobook",
    "tags": [
        "Rebirth 60", "Business Empire in Hong Kong", "Tycoon Novel", "Progression Fantasy",
        "Hong Kong 1960s", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Rebirth 60: I Created a Business Empire in Hong Kong', covering Chapters 1 through 40!\n\n"
        "Transmigrating back to 1960s British Hong Kong burdened by a high-interest usury debt, a former commercial "
        "strategist uses his knowledge of future market trends, industrial shifts, and colonial finance to break out "
        "of poverty and build the foundation of a multi-billion dollar trade dynasty.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and narration).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#Rebirth60 #BusinessEmpire #HongKong #TycoonAudiobook #BeingABong #Audiobook"
    ),

    # 4 High-CTR Thematic Visual Blocks
    "blocks": [
        {
            "index": 1,
            "range": (1, 10),
            "title": ["USURY DEBT", "THE 1960S TENEMENT"],
            "fallback_color": (20, 15, 15),
            "prompt": (
                "A cinematic wide 16:9 panoramic key visual set on a rain-slicked, neon-lit alleyway in 1960s British Hong Kong, "
                "designed with maximum visual contrast for high CTR. "
                "In the sharp radiant center limelight stands the transmigrated hero—a sharp-eyed, resolute young entrepreneur in a soaked "
                "white rolled-sleeve cotton shirt and dark vintage trousers, standing defiantly on the threshold of a wooden tenement house. "
                "Before him are menacing Triad loan sharks in floral shirts and slacks holding wooden clubs and usury promissory notes in the pouring rain. "
                "Surrounding the perimeter in the misty background are overhead glowing red and emerald neon signs, bamboo scaffolding, "
                "vintage green double-decker trams rattling along wet cobblestones, and laundry poles hanging between cramped colonial buildings. "
                "Dynamic chiaroscuro lighting (vibrant neon red and teal reflections cutting through rain and gaslamp amber), "
                "glistening puddle reflections, photorealistic 1960s retro aesthetic, Unreal Engine 5 render style, sharp focus, 8k resolution --ar 16:9 --style raw --v 6.1"
            )
        },
        {
            "index": 2,
            "range": (11, 20),
            "title": ["FIRST POT OF GOLD", "STREET STALLS AND FACTORY FLOORS"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "An epic 16:9 grand cinematic vintage commercial scene inside a bustling Kowloon textile workshop and plastics factory in the 1960s. "
                "Center-stage in the warm spotlight of hanging industrial enamel lamps, the young business protagonist inspects an innovative consumer mold "
                "and fresh batches of manufactured goods, surrounded by busy workers, spinning sewing machines, and stacked wooden shipping crates. "
                "Spread across his sturdy wooden desk are accounting ledgers, stacks of vintage Hong Kong dollar banknotes, and blueprints for export expansion. "
                "Through the large industrial multi-pane windows, the bustling Victoria Harbour docks and smoking steam cargo freighters are visible under daytime sun. "
                "Warm amber factory illumination, atmospheric airborne dust motes, authentic machinery steel and aged paper textures, "
                "cinematic composition, sharp focus, 8k digital art --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (21, 30),
            "title": ["COMMERCIAL MANEUVERS", "THE WHARVES OF VICTORIA HARBOUR"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "A dramatic wide 16:9 maritime trade visual overlooking the bustling Victoria Harbour docks at twilight in 1960. "
                "In the confident center foreground, the protagonist, now sharply dressed in a tailored British grey wool suit with a silk tie, "
                "stands on an elevated wooden pier pier-walk overlooking the harbor, clipboard and contract in hand. "
                "Behind him, heavy iron cranes load crates onto towering ocean steamships, traditional wooden junks glide across golden-hour waters, "
                "and dockworkers move cargo under the shadow of the soaring Peak hills. "
                "Golden sunset rim lighting gleaming across the ocean waves, silhouettes of colonial British trading offices in Central, "
                "photorealistic maritime textures, atmospheric sea spray, masterwork digital concept art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (31, 40),
            "title": ["THE RISE OF A TYCOON", "CONQUERING CENTRAL FINANCE"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "A breathtaking 16:9 climactic boardroom visual inside a high-floor colonial office building in Central, Hong Kong, at golden hour. "
                "Center-stage in an authoritative spotlight, the hero sits at the head of a massive mahogany conference table, "
                "calmly signing a landmark corporate takeover agreement surrounded by nervous British colonial bank directors and legal counsels in pinstripe suits. "
                "Behind him, floor-to-ceiling panoramic glass windows reveal the skyline of 1960s Hong Kong, the shimmering harbor, "
                "and the iconic clocktower beneath a dramatic golden-orange sky. "
                "High dynamic range, rich wood grain and polished marble reflections, photorealistic tailored wool fabric, "
                "cinematic matte painting, Unreal Engine 5 showcase, 8k resolution --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
