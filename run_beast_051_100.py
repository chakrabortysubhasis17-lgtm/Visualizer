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

BUILD_DIR = "build_hanged_up_beast_master_051_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://mtl-novel.com/novel/after-i-hanged-up-i-became-the-strongest-beast-master/chapter-51-burning-bee/",
    "novel_slug": "hanged-up-beast-master",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "After I Hanged Up, I Became the Strongest Beast Master: Ze City Secret Realm",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Standard 5-Beat Intro Hook with Split Character Dialogue & Narrative Teaser
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Stern Veteran Instructor Voice)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Coach Kuang",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": '"Over a thousand Beastmasters die in the Ze City Secret Realm every single year! This is not an amusement park—you must be mentally prepared!"',
            "tts_text": '"Over a thousand Beastmasters die in the Zeh City Secret Realm every single year! This is not an amusement park... you must be mentally prepared!"',
            "text": '"Over a thousand Beastmasters die in the Ze City Secret Realm every single year! This is not an amusement park—you must be mentally prepared!"',
            "voice": "en-US-GuyNeural",
            "pitch": "-1Hz",
            "sfx": "whoosh",
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
            "display_text": "Stepping into the flooded, monster-infested ruins of Ze City beside an instructor commanding a two-meter Scorching Hunter Bee, Chen Xing unleashes his idle AFK training system—turning every swamp predator into fuel for his mythical crocodile Taotie!",
            "tts_text": "Stepping into the flooded, monster-infested ruins of Zeh City beside an instructor commanding a two-meter Scorching Hunter Bee... Chen Shing unleashes his idle A-F-K training system... turning every swamp predator into fuel for his mythical crocodile Tow-tyeh!",
            "text": "Stepping into the flooded, monster-infested ruins of Ze City beside an instructor commanding a two-meter Scorching Hunter Bee, Chen Xing unleashes his idle AFK training system—turning every swamp predator into fuel for his mythical crocodile Taotie!",
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
            "display_text": "Beastmaster Guild Decree: To boost your AFK skill proficiency and support today's massive release, hit that Like button and subscribe to the channel. Conquering uncharted Secret Realms and awakening ancient bloodlines demands relentless evolution.",
            "tts_text": "Beastmaster Guild Decree: To boost your A-F-K skill proficiency and support today's massive release, hit that Like button and subscribe to the channel. Conquering uncharted Secret Realms and awakening ancient bloodlines demands relentless evolution.",
            "text": "Beastmaster Guild Decree: To boost your AFK skill proficiency and support today's massive release, hit that Like button and subscribe to the channel. Conquering uncharted Secret Realms and awakening ancient bloodlines demands relentless evolution.",
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
            "display_text": "Previously, Chen Xing unlocked automated AFK grinding slots that catapulted his fledgling crocodile past every bottleneck. Now, entering Chapters 51 through 100 of After I Hanged Up, I Became the Strongest Beast Master, the gates of Ze City open. Prepare yourselves, and let the hunt begin.",
            "tts_text": "Previously, Chen Shing unlocked automated A-F-K grinding slots that catapulted his fledgling crocodile past every bottleneck. Now, entering Chapters 51 through 100 of After I Hanged Up, I Became the Strongest Beast Master... the gates of Zeh City open. Prepare yourselves, and let the hunt begin.",
            "text": "Previously, Chen Xing unlocked automated AFK grinding slots that catapulted his fledgling crocodile past every bottleneck. Now, entering Chapters 51 through 100 of After I Hanged Up, I Became the Strongest Beast Master, the gates of Ze City open. Prepare yourselves, and let the hunt begin.",
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
            "sfx": "wind",
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
    "final_audio": "output_hanged_up_beast_master_051_100.mp3",
    "final_video": "final_hanged_up_beast_master_051_100.mp4",
    "cover_image": "cover_hanged_up_beast_master_051_100.jpg",
    "timestamps_file": "youtube_timestamps_hanged_up_beast_master_051_100.txt",
    "subtitles_file": "subtitles_hanged_up_beast_master_051_100.srt",
    "payload_file": "youtube_upload_payload_hanged_up_beast_master_051_100.json",

    # Clean Branding Overlay Configuration
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "AFTER I HANGED UP, I BECAME THE STRONGEST BEAST MASTER! [Chapters 51-100] | AFK LitRPG Audiobook",
    "tags": [
        "After I Hanged Up I Became the Strongest Beast Master", "Beast Taming", "AFK System",
        "Progression Fantasy", "LitRPG Audiobook", "Chen Xing", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'After I Hanged Up, I Became the Strongest Beast Master', covering Chapters 51 through 100!\n\n"
        "Entering the flooded, ancient ruins of the Ze City Secret Realm alongside Coach Kuang and his terrifying "
        "Scorching Hunter Bee, Chen Xing puts his AFK idle training system to the ultimate test. Amidst treacherous "
        "swamps and lurking aquatic predators, his fierce crocodile Taotie awakens ancient bloodline instincts.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#BeastMaster #AFKSystem #LitRPG #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # 4 High-CTR Thematic Visual Blocks for Chapters 51 to 100
    "blocks": [
        {
            "index": 1,
            "range": (51, 62),
            "title": ["ZE CITY SECRET REALM", "THE SCORCHING HUNTER BEE"],
            "fallback_color": (20, 25, 20),
            "prompt": (
                "A cinematic wide 16:9 panoramic key visual set on a reed-lined wooden pontoon bridge leading toward the flooded, "
                "mud-coated ancient stone walls of Ze City inside a Secret Realm, designed with maximum visual contrast for high CTR. "
                "In the sharp radiant center limelight stands young Beastmaster Chen Xing in sleek dark tactical training gear, "
                "holding a freshly inked Secret Realm map while his fierce, muscular juvenile crocodile beast Taotie snarls defensively beside his boots. "
                "Hovering menacingly above them is a colossal, 2.1-meter-long Scorching Hunter Bee—a reddish-brown giant fire wasp with glowing magma-red "
                "wavy carapace patterns, translucent buzzing wings, and a gleaming lethal stinger radiating intense heat waves. "
                "In the background, armed Beastmasters patrol the misty reed marshes and weathered city gates under a crisp azure sky. "
                "Dynamic chiaroscuro lighting (fiery amber bio-luminescence from the giant bee contrasting against cool marsh mist and ancient stone), "
                "glistening water reflections, intricate reptile scale and chitin textures, Unreal Engine 5 render style, 8k resolution --ar 16:9 --style raw --v 6.1"
            )
        },
        {
            "index": 2,
            "range": (63, 75),
            "title": ["SWAMP PREDATORS", "WATER TYRANT AWAKENING"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "An epic 16:9 grand cinematic monster battle visual inside the submerged, moss-draped avenues of sunken Ze City. "
                "Center-stage in an intense spotlight of shattering water spray, Chen Xing's crocodile beast Taotie surges forward with glowing "
                "primordial runes across its armored dorsal plates, tearing through mutated aquatic predators including giant armored tiger shrimp "
                "and scythe-clawed ghost crabs. "
                "Floating beside Chen Xing is a crisp, semi-translucent holographic AFK system panel displaying rapid skill proficiency breakthroughs "
                "and bloodline energy absorption. "
                "Half-submerged ancient pagodas, swaying reeds, and dramatic shafts of sunlight piercing through misty swamp canopies frame the perimeter. "
                "High-speed water droplets frozen in mid-air, dynamic rim lighting, photorealistic scale and water textures, "
                "cinematic composition, sharp focus, 8k digital art --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (76, 87),
            "title": ["AFK SKILL MASTERY", "BREAKING BLOODLINE LIMITS"],
            "fallback_color": (25, 20, 15),
            "prompt": (
                "A dramatic wide 16:9 nocturnal cultivation visual inside a fortified ruined watchtower overlooking the moonlit swamps of Ze City. "
                "In the confident center foreground, Chen Xing sits beside a crackling spirit-wood campfire, calibrating glowing translucent AFK hang-up slots "
                "hovering in mid-air as streams of golden and azure spiritual essence pour directly into the sleeping, rapidly growing Taotie. "
                "Surrounding the perimeter, fellow students rest under faint stone-like defensive aura shields while distant glowing eyes of nocturnal swamp beasts "
                "peer from the foggy reeds below. "
                "Warm firelight colliding with cool silver moonlight, floating ember particles, intricate ancient brickwork and metallic armor textures, "
                "masterwork digital concept art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (88, 100),
            "title": ["DEPTHS OF THE REALM", "RISE OF THE APEX TAMER"],
            "fallback_color": (30, 15, 15),
            "prompt": (
                "A breathtaking 16:9 climactic boss-battle visual set in the flooded central plaza of the Ze City Secret Realm at sunset. "
                "Center-stage in an authoritative spotlight, Chen Xing commands the battlefield with outstretched hand as an evolved, towering Taotie "
                "unleashes a devastating primordial devouring vortex against a colossal, multi-tiered swamp overlord leviathan. "
                "Overhead, fiery meteor-like fireballs from Coach Kuang's Scorching Hunter Bee streak across the crimson-and-violet twilight sky. "
                "High dynamic range, dramatic chiaroscuro lighting, shattering stone pillars and surging tidal waves, "
                "cinematic matte painting, Unreal Engine 5 showcase, 8k resolution --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
