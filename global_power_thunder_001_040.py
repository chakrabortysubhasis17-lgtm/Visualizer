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

BUILD_DIR = "build_global_power_thunder_001_040"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/global-power-awakening-of-the-purple-sky-divine-thunder-at-the-beginning/chapter-1-deep-blue-system-novice-gift-pack/",
    "novel_slug": "global-power-purple-thunder",
    "start_chapter": 1,
    "end_chapter": 40,
    "default_topic": "Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Standard 5-Beat Intro Hook with Split Character Dialogue & Narrative Teaser
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Character Voice)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Arrogant Classmate",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+2%",
            "pause_duration": 0.3,
            "display_text": '"With only an E-rank Weak Electricity, you\'re nothing more than a walking stun baton—give up on the university exam!"',
            "tts_text": '"With only an E-rank Weak Electricity... you\'re nothing more than a walking stun baton—give up on the university exam!"',
            "text": '"With only an E-rank Weak Electricity, you\'re nothing more than a walking stun baton—give up on the university exam!"',
            "voice": "en-US-EricNeural",
            "pitch": "+0Hz",
            "sfx": "thunder",
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
            "display_text": "Mocked on the eve of the high-stakes College Entrance Examination, an ordinary high schooler activates the supreme Deep Blue System—unleashing the apocalyptic S-rank Purple Sky Divine Thunder that will shock the entire world!",
            "tts_text": "Mocked on the eve of the high-stakes College Entrance Examination... an ordinary high schooler activates the supreme Deep Blue System... unleashing the apocalyptic S-rank Purple Sky Divine Thunder that will shock the entire world!",
            "text": "Mocked on the eve of the high-stakes College Entrance Examination, an ordinary high schooler activates the supreme Deep Blue System—unleashing the apocalyptic S-rank Purple Sky Divine Thunder that will shock the entire world!",
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
            "display_text": "Thunder Sovereign Decree: To supercharge today's massive release and claim your divine ability points, strike that Like button and subscribe to the channel. Defying beast tides and advancing through the nine tiers demands boundless heavenly energy.",
            "tts_text": "Thunder Sovereign Decree: To supercharge today's massive release and claim your divine ability points, strike that Like button and subscribe to the channel. Defying beast tides and advancing through the nine tiers demands boundless heavenly energy.",
            "text": "Thunder Sovereign Decree: To supercharge today's massive release and claim your divine ability points, strike that Like button and subscribe to the channel. Defying beast tides and advancing through the nine tiers demands boundless heavenly energy.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
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
            "display_text": "From an overlooked student wielding feeble static electricity to the inheritor of primordial purple lightning, a new legend begins in the Great Xia Nation. Now, entering Chapters 1 through 40 of Global Power, the novice gift pack unlocks. Steel yourselves, and let the storm descend.",
            "tts_text": "From an overlooked student wielding feeble static electricity to the inheritor of primordial purple lightning... a new legend begins in the Great Shah Nation. Now, entering Chapters 1 through 40 of Global Power, the novice gift pack unlocks. Steel yourselves, and let the storm descend.",
            "text": "From an overlooked student wielding feeble static electricity to the inheritor of primordial purple lightning, a new legend begins in the Great Xia Nation. Now, entering Chapters 1 through 40 of Global Power, the novice gift pack unlocks. Steel yourselves, and let the storm descend.",
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
            "sfx": "thunder",
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
    "final_audio": "output_global_power_thunder_001_040.mp3",
    "final_video": "final_global_power_thunder_001_040.mp4",
    "cover_image": "cover_global_power_thunder_001_040.jpg",
    "timestamps_file": "youtube_timestamps_global_power_thunder_001_040.txt",
    "subtitles_file": "subtitles_global_power_thunder_001_040.srt",
    "payload_file": "youtube_upload_payload_global_power_thunder_001_040.json",

    # Clean Branding Overlay Configuration
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "GLOBAL POWER: AWAKENING OF THE PURPLE SKY DIVINE THUNDER! [Chapters 1-40] | Urban Fantasy LitRPG Audiobook",
    "tags": [
        "Global Power", "Purple Sky Divine Thunder", "Deep Blue System", "Urban Cultivation",
        "LitRPG Audiobook", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Global Power: Awakening of the Purple Sky Divine Thunder at the Beginning', covering Chapters 1 through 40!\n\n"
        "Transmigrating into a world overrun by ferocious beasts where superpowers dictate status, Xu Jingming starts with "
        "only an E-rank Weak Electricity ability. But on the eve of the College Entrance Examination, the Deep Blue System "
        "activates—rewarding him with the supreme S-rank Purple Sky Divine Thunder and launching his rise to the peak.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#GlobalPower #PurpleSkyDivineThunder #DeepBlueSystem #UrbanFantasy #BeingABong #Audiobook"
    ),

    # 4 High-CTR Thematic Visual Blocks
    "blocks": [
        {
            "index": 1,
            "range": (1, 10),
            "title": ["PURPLE SKY DIVINE THUNDER", "THE NOVICE GIFT PACK"],
            "fallback_color": (20, 10, 30),
            "prompt": (
                "A cinematic wide 16:9 panoramic key visual set inside a high school cultivation training hall in Jiangcheng, "
                "designed with maximum visual contrast for high CTR. "
                "In the radiant center limelight stands the transmigrated hero, Xu Jingming—a handsome, focused young student in a modern "
                "white and navy school uniform, his right hand outstretched as blinding violet-indigo celestial lightning arcs and crackles violently "
                "between his fingers, shattering the concrete training pillars into smoking rubble. "
                "Floating beside him is a sleek, semi-translucent deep-blue holographic system interface detailing the S-rank Purple Sky Divine Thunder "
                "and ability points. "
                "In the shocked background, classmates and the burly head teacher Chen Fan recoil in disbelief, their faces illuminated by the purple glare. "
                "Dynamic chiaroscuro lighting (brilliant violet electric arcs contrasting against dark gymnasium shadows), "
                "volumetric lightning flashes, flying concrete debris, photorealistic anime-realism aesthetic, Unreal Engine 5 render style, 8k resolution --ar 16:9 --style raw --v 6.1"
            )
        },
        {
            "index": 2,
            "range": (11, 20),
            "title": ["COLLEGE ENTRANCE EXAM", "SHOCKING JIANGCHENG"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "An epic 16:9 grand cinematic combat trial visual inside a massive high-tech arena stadium under open daylight. "
                "Center-stage in the spotlight, Xu Jingming descends from mid-air enveloped in a colossal column of roaring purple divine thunder, "
                "decimating an armored iron-hide ferocious beast simulator in a single cataclysmic shockwave. "
                "Massive holographic evaluation scoreboards hovering above the stadium flash pure S-rank crimson alerts, while university scouts "
                "and guild representatives rise from their viewing boxes in astonishment. "
                "Intense energy shockwaves rippling across the sandy arena ground, flying scorched armor fragments, photorealistic electric particle trails, "
                "cinematic composition, sharp focus, 8k digital art --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (21, 30),
            "title": ["SUPERPOWER UNIVERSITY", "THUNDER REFINEMENT"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "A dramatic wide 16:9 cultivation chamber visual set inside a top-tier Superpower University underground research laboratory. "
                "In the confident center foreground, Xu Jingming sits cross-legged inside a spherical electromagnetic containment core, "
                "his skin radiating an ethereal violet sheen as he refines divine thunder essence through his meridians. "
                "Surrounding the dais are crystalline energy conduits and floating deep-blue system panels showing rapid stat advancement and ability mastery. "
                "High-tech chrome architecture, cool cyan lab lighting colliding with warm purple electric flashes, "
                "photorealistic subsurface skin scattering and metallic reflections, masterwork digital concept art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (31, 40),
            "title": ["WILDERNESS BEAST HUNT", "DEEP BLUE UPGRADE"],
            "fallback_color": (30, 15, 20),
            "prompt": (
                "A breathtaking 16:9 climactic wilderness battlefield visual set in a ruined post-apocalyptic forest outside the defensive safe zone at dusk. "
                "Center-stage in an authoritative spotlight, Xu Jingming stands atop the skull of a colossal felled beast monarch, "
                "wielding a crackling lance of pure purple lightning that pierces the stormy sky, summoning an apocalyptic thundercloud storm. "
                "In the background, retreating hordes of mutated ferocious beasts flee into the burning wasteland beneath a blood-orange sunset. "
                "High dynamic range, dramatic rim lighting from purple lightning strikes, flying embers and smoke plumes, "
                "cinematic matte painting, Unreal Engine 5 showcase, 8k resolution --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
