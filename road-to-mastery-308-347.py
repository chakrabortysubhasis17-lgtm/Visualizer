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

BUILD_DIR = "build_road_to_mastery_308_347"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/road-to-mastery-a-litrpg-apocalypse/chapter-307",
    "novel_slug": "road-to-mastery-a-litrpg-apocalypse",
    "start_chapter": 308,
    "end_chapter": 347,
    "default_topic": "Road to Mastery: Continental Commander & The Ice Peak War",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",

    # Standard 5-Beat Intro Hook (Aligned with Probable-Age & Gender Deterministic Casting)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Vlossana - Female, Age 20-29 / young_adult)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Vlossana",
            "gender": "Female",
            "probable_age": "20-29",
            "age_category": "young_adult",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"My name is Vlossana... and I am here to kill you."',
            "tts_text": '"My name is Vlo-sah-nah... and I am here to kill you."',
            "text": '"My name is Vlossana... and I am here to kill you."',
            "voice": "en-US-AvaMultilingualNeural",
            "pitch": "+0Hz",
            "sfx": "blade",
            "bgm_mood": "tension"
        },
        # Beat 1b: Narrative Teaser Hook (Christopher Anchor)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "probable_age": "n/a",
            "age_category": "n/a",
            "line_type": "Narration",
            "pitch_tier": "authoritative_low",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "As Continental Commander Margaret Rust orchestrates a desperate defensive war against the overwhelming Ice Peak army, a mysterious sapphire-haired Level 124 powerhouse pierces Edgar's mind—while everyone awaits the return of Jack Rust!",
            "tts_text": "As Continental Commander Margaret Rust orchestrates a desperate defensive war against the overwhelming Ice Peak army... a mysterious sapphire-haired Level 124 powerhouse pierces Edgar's mind... while everyone awaits the return of Jack Rust!",
            "text": "As Continental Commander Margaret Rust orchestrates a desperate defensive war against the overwhelming Ice Peak army, a mysterious sapphire-haired Level 124 powerhouse pierces Edgar's mind—while everyone awaits the return of Jack Rust!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "tension"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Neutral",
            "probable_age": "n/a",
            "age_category": "n/a",
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
            "probable_age": "n/a",
            "age_category": "n/a",
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
            "probable_age": "n/a",
            "age_category": "n/a",
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
            "probable_age": "n/a",
            "age_category": "n/a",
            "line_type": "Narration",
            "pitch_tier": "conversational_mid",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.3,
            "display_text": "Dao Comprehension Decree: To temper your Will and support today's massive release, smash that Like button and subscribe to the channel. Surviving the LitRPG Apocalypse and forging an unstoppable Physical Dao demands relentless battle spirit.",
            "tts_text": "Dow Comprehension Decree: To temper your Will and support today's massive release, smash the Like button and subscribe to the channel. Surviving the Lit-R-P-G Apocalypse and forging an unstoppable Physical Dow demands relentless battle spirit.",
            "text": "Dao Comprehension Decree: To temper your Will and support today's massive release, smash that Like button and subscribe to the channel. Surviving the LitRPG Apocalypse and forging an unstoppable Physical Dao demands relentless battle spirit.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "interface",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Neutral",
            "probable_age": "n/a",
            "age_category": "n/a",
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
            "probable_age": "n/a",
            "age_category": "n/a",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Previously, Earth's alliance clashed head-on with the ruthless cultivators of Ice Peak while Jack Rust vanished into the unknown. Now, entering Chapters 308 through 347 of Road to Mastery, blood soaks the white stone battlefield. Brace yourselves, and let the war rage on.",
            "tts_text": "Previously, Earth's alliance clashed head-on with the ruthless cultivators of Ice Peak while Jack Rust vanished into the unknown. Now, entering Chapters 308 through 347 of Road to Mastery... blood soaks the white stone battlefield. Brace yourselves, and let the war rage on.",
            "text": "Previously, Earth's alliance clashed head-on with the ruthless cultivators of Ice Peak while Jack Rust vanished into the unknown. Now, entering Chapters 308 through 347 of Road to Mastery, blood soaks the white stone battlefield. Brace yourselves, and let the war rage on.",
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
            "probable_age": "n/a",
            "age_category": "n/a",
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
            "sfx": "wardrum",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Neutral",
            "probable_age": "n/a",
            "age_category": "n/a",
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
    "final_audio": "output_road_to_mastery_308_347.mp3",
    "final_video": "final_road_to_mastery_308_347.mp4",
    "cover_image": "cover_road_to_mastery_308_347.jpg",
    "timestamps_file": "youtube_timestamps_road_to_mastery_308_347.txt",
    "subtitles_file": "subtitles_road_to_mastery_308_347.srt",
    "payload_file": "youtube_upload_payload_road_to_mastery_308_347.json",

    # Clean Branding Overlay Configuration
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "ROAD TO MASTERY: CONTINENTAL COMMANDER & THE ICE PEAK WAR! [Chapters 308-347] | LitRPG Audiobook",
    "tags": [
        "Road to Mastery", "LitRPG Apocalypse", "Jack Rust", "Progression Fantasy",
        "Cultivation LitRPG", "Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Road to Mastery: A LitRPG Apocalypse', covering Chapters 308 through 347!\n\n"
        "On a white-stone battlefield torn apart by magic missiles, heavy metal war anthems, and roaring brorillas, "
        "Continental Commander Margaret Rust directs Earth's outnumbered alliance against the relentless Ice Peak forces—"
        "while Edgar confronts a deadly sapphire-haired assassin and awaits Jack Rust's return.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#RoadToMastery #LitRPGApocalypse #ProgressionFantasy #Cultivation #Audiobook #BeingABong"
    ),

    # 4 High-CTR Thematic Visual Blocks for Chapters 308 to 347
    "blocks": [
        {
            "index": 1,
            "range": (308, 317),
            "title": ["CONTINENTAL COMMANDER", "CLASH ON THE WHITE STONE"],
            "fallback_color": (20, 25, 35),
            "prompt": (
                "A cinematic wide 16:9 panoramic key visual set on a vast white-stone battlefield engulfed in chaotic LitRPG magic and martial warfare, "
                "designed with maximum visual contrast for high CTR. "
                "In the sharp radiant center limelight stands Margaret Rust—a fierce, commanding silver-haired female strategist with eyes closed in supreme mental focus, "
                "surrounded by a hundred translucent tactical light-threads linking her to the battlefield while six ancient martial monks form a protective perimeter around her. "
                "Charging across the foreground are muscular pugilist warriors and Oz, a massive, battle-scarred armored brorilla smashing through a towering glacial ice wall "
                "as Flame River wizards unleash a roaring torrent of crimson fire from above. "
                "Dynamic chiaroscuro lighting (blazing orange fire rivers and golden aura threads colliding with blinding glacial blue ice shards), "
                "billowing steam clouds, intricate armor and fur textures, Unreal Engine 5 render style, 8k resolution --ar 16:9 --style raw --v 6.1"
            )
        },
        {
            "index": 2,
            "range": (318, 327),
            "title": ["SUN-EYED WIZARD VS SAPHIRA", "THE WILL DUEL"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "An epic 16:9 grand cinematic magical duel visual set amidst shattered white-stone ruins on a war-torn plain. "
                "Center-stage in an intense spotlight stands Edgar, a battle-hardened wizard with blazing sun-like golden eyes, conjuring flaming meteors from the sky "
                "and summoning swirling sand devils behind translucent blue arcane shields. "
                "Facing him across a storm of shattering hailstones is Vlossana, a deadly Level 124 Saphira woman with fair skin, flowing sapphire hair, and glowing "
                "inhuman purple eyes emerging from a dark brown cloak, unleashing waves of dark violet Will energy that warp the surrounding air. "
                "High in the stormy sky above, an ice bird and a blazing fire phoenix collide in explosive plumes of frost and flame. "
                "Dramatic rim lighting, flying stone debris, photorealistic arcane particle effects, cinematic composition, sharp focus, 8k digital art --ar 16:9 --style raw"
            )
        },
        {
            "index": 3,
            "range": (328, 337),
            "title": ["THE PUGILIST'S RETURN", "SHATTERING THE HEAVENS"],
            "fallback_color": (30, 20, 15),
            "prompt": (
                "A dramatic wide 16:9 action climax visual set in the center of a devastated crater on the battlefield. "
                "In the confident center limelight descends Jack Rust—a towering, muscular martial cultivator radiating an overwhelming golden-crimson Physical Dao aura, "
                "his clenched fist unleashing a shockwave that vaporizes incoming ice spears and sends enemy cultivators flying backward. "
                "Behind him, a lone bard stands atop a raised stone stage shredding an electric guitar that sends visible golden soundwaves rippling across the allied ranks. "
                "Shattered glaciers, rising dust plumes, and radiant golden energy arcs frame the perimeter under a fractured sky. "
                "Photorealistic muscle and aura lighting, flying rock fragments, masterwork digital concept art, 8k --ar 16:9 --style raw"
            )
        },
        {
            "index": 4,
            "range": (338, 347),
            "title": ["ROAD TO MASTERY", "ASCENDING BEYOND LIMITS"],
            "fallback_color": (20, 15, 25),
            "prompt": (
                "A breathtaking 16:9 climactic cultivation breakthrough visual set atop a high mountain peak overlooking a sea of clouds at twilight. "
                "Center-stage in an authoritative spotlight, Jack Rust stands amidst a swirling vortex of primordial Dao laws and golden lightning, "
                "his body tempered like indestructible divine jade as a translucent LitRPG system screen illuminates his monumental level advancement. "
                "In the distant background, celestial rifts and towering floating monoliths glow beneath a dramatic violet-and-gold horizon. "
                "High dynamic range, dramatic chiaroscuro lighting, photorealistic celestial energy and atmospheric clouds, "
                "cinematic matte painting, Unreal Engine 5 showcase, 8k resolution --ar 16:9 --style raw"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))