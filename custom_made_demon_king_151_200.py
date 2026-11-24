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
                if len(rows) < 8 or any(
                    "Exposition details continue" in (r.get("display_text") or r.get("tts_text") or r.get("text", ""))
                    for r in rows
                ):
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


BUILD_DIR = "build_custom_made_demon_king_151_200"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/custom-made-demon-king/chapter-151",
    "novel_slug": "custom-made-demon-king",
    "start_chapter": 151,
    "end_chapter": 200,
    "is_start": False,
    "default_topic": "Custom Made Demon King",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 151 to 200)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Roy - Cold Calculating Demon)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Roy",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "cold_calculating",
            "age_category": "young",
            "display_text": '"Let those fools chase the black dragon into the meat grinder. With a hundred thousand souls in my grasp and the Cold Winter Armor forged, I am the true Lord of Darkness and Winter!"',
            "tts_text": '"Let those fools chase the black dragon into the meat grinder. With a hundred thousand souls in my grasp and the Cold Winter Armor forged... I am the true Lord of Darkness and Winter!"',
            "text": '"Let those fools chase the black dragon into the meat grinder. With a hundred thousand souls in my grasp and the Cold Winter Armor forged, I am the true Lord of Darkness and Winter!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "roar",
            "bgm_mood": "dread"
        },
        # Beat 1b: Narrative Teaser Hook (Slow, weighty delivery)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "ominous",
            "age_category": "adult",
            "display_text": "As the fallen black dragon Destroyer descends upon the End War and draws both angel armies and high-rank demons toward the main battlefield, Roy seizes the empty coastal city—harvesting one hundred thousand souls to forge his indestructible Cold Winter Armor across Chapters 151 through 200!",
            "tts_text": "As the fallen black dragon Destroyer descends upon the End War and draws both angel armies and high rank demons toward the main battlefield, Roy seizes the empty coastal city... harvesting one hundred thousand souls to forge his indestructible Cold Winter Armor across Chapters 151 through 200!",
            "text": "As the fallen black dragon Destroyer descends upon the End War and draws both angel armies and high-rank demons toward the main battlefield, Roy seizes the empty coastal city—harvesting one hundred thousand souls to forge his indestructible Cold Winter Armor across Chapters 151 through 200!",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "grim_rumble",
            "pitch": "-2Hz",
            "rate": "-6%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "dread"
        },
        {
            "line_id": "intro_pause_01",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 2: Channel Trademark Signature
        {
            "line_id": "intro_02_trademark",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "confident",
            "age_category": "adult",
            "display_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome back to Being a Bong. We narrate the unreal worlds to life.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "engaged_alert",
            "pitch": "-2Hz",
            "rate": "+2%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "whoosh",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_02",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 3: In-Universe Call to Action
        {
            "line_id": "intro_03_cta",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "persuasive",
            "age_category": "adult",
            "display_text": "Abyss System Tribute: To feed Roy's soul reserves and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. In the Abyss, custom evolution rules all.",
            "tts_text": "Abyss System Tribute: To feed Roy's soul reserves and unlock this fifty chapter dark fantasy marathon, hit that Like button and subscribe to the channel. In the Abyss, custom evolution rules all.",
            "text": "Abyss System Tribute: To feed Roy's soul reserves and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. In the Abyss, custom evolution rules all.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "conversational_mid",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "chime",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_pause_03",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "",
            "bgm_mood": "no_mood"
        },
        # Beat 4: Continuation Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Custom Made Demon King. Equip the Cold Winter Armor, command the black ice storm, and witness Roy climb toward the Demon King throne.",
            "tts_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Custom Made Demon King. Equip the Cold Winter Armor, command the black ice storm, and witness Roy climb toward the Demon King throne.",
            "text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Custom Made Demon King. Equip the Cold Winter Armor, command the black ice storm, and witness Roy climb toward the Demon King throne.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-3%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "tension"
        },
        # Beat 5: Transition SFX & Lead-in Silence
        {
            "line_id": "intro_05_scene_sfx",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.2,
            "sfx": "teleport",
            "bgm_mood": "no_mood"
        },
        {
            "line_id": "intro_06_lead_in_silence",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "neutral",
            "age_category": "adult",
            "display_text": "",
            "tts_text": "",
            "text": "",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "narrator_anchor",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 1.0,
            "sfx": "",
            "bgm_mood": "no_mood"
        }
    ],

    # Filepaths & Outputs
    "build_dir": BUILD_DIR,
    "final_audio": "output_custom_made_demon_king_151_200.mp3",
    "final_video": "final_custom_made_demon_king_151_200.mp4",
    "cover_image": "cover_custom_made_demon_king_151_200.jpg",
    "timestamps_file": "youtube_timestamps_custom_made_demon_king_151_200.txt",
    "subtitles_file": "subtitles_custom_made_demon_king_151_200.srt",
    "payload_file": "youtube_upload_payload_custom_made_demon_king_151_200.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "CUSTOM MADE DEMON KING [Chapters 151-200] | Abyss Evolution & Villain LitRPG Audiobook",
    "tags": [
        "Custom Made Demon King", "Custom Made Demon King Audiobook", "Abyss Evolution LitRPG",
        "Villain Protagonist Audiobook", "Demon Evolution Novel", "Roy Demon King", "Dark Fantasy LitRPG", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Custom Made Demon King' (Part 4), covering Chapters 151 through 200!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLOhHao1NCFug\n\n"
        "When the colossal fallen black dragon Destroyer appears on the End War battlefield and lures both angel legions "
        "and rival high-rank demons away from the coast, Roy seizes the golden opportunity. Harvesting one hundred thousand souls "
        "in the abandoned metropolis, he materializes his custom Cold Winter Armor—unleashing a terrifying black ice storm "
        "and entering the deadliest phase of the angel-demon war across Chapters 151 through 200!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE VILLAIN & DARK FANTASY LITRPG MARATHONS ON BEING A BONG:\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• The Incubus System: Urban Fantasy Harem LitRPG -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#CustomMadeDemonKing #AbyssEvolution #VillainLitRPG #DarkFantasyAudiobook #LitRPG #RoyDemonKing #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Abyssal Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (151, 155),
            "fallback_color": (14, 18, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of demon protagonist Roy soaring above a ruined coastal metropolis clad in domineering black-ice Cold Winter Armor "
                "with skull pauldrons, horn-like wing protrusions, and glowing scarlet pentagram eyes inside a T-slit visor, summoning a storm of razor-sharp black ice blades. "
                "UPPER-RIGHT BACKGROUND: Colossal silhouette of the fallen black dragon Destroyer flying across storm-wracked clouds toward a distant burning capital. "
                "High-contrast glacial-cyan, obsidian-black, and blood-crimson palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (156, 160),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital abyssal-forging book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy standing before a floating glowing Horadric Cube transmuting swirling crimson-and-blue soul flames into custom demonic weapons and runes, "
                "translucent dark-bordered Demon King system customization panels hovering around his clawed gauntlets. "
                "UPPER-RIGHT & BACKGROUND: Frozen skyscrapers coated in black frost under an eerie overcast sky. "
                "High-contrast soul-cyan, abyssal-violet, and charcoal-slate palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (161, 165),
            "fallback_color": (22, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital angel-demon-war clash book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Armored frost-and-darkness demon Roy spreading massive black-and-frost wings in midair, "
                "clashing head-on against an armored multi-winged archangel wielding a blazing golden holy greatsword. "
                "UPPER-RIGHT & BACKGROUND: Falling white feathers and shards of black ice exploding across a smoke-filled battlefield. "
                "High-contrast holy-gold, midnight-indigo, and frost-blue palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (166, 170),
            "fallback_color": (16, 20, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Roy standing atop a shattered highway overpass overlooking an army of subservient low-rank demons and frost creatures, "
                "dark cold aura freezing the concrete beneath his spiked ice boots while scarlet eyes gleam beneath his demonic helm. "
                "UPPER-RIGHT SKY: Twin dimensional rifts—one bleeding golden celestial light, the other swirling with abyssal sulfur smoke. "
                "High-contrast arctic-blue, sulfur-amber, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (171, 175),
            "fallback_color": (24, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted apocalyptic-dragon-siege book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The mountain-sized fallen black dragon Destroyer unleashing a torrent of violet-black hellfire across a fortified human metropolis, "
                "while Roy watches calmly from a distant frozen spire with swirling dark magic coiling around his fingertips. "
                "UPPER-RIGHT & BACKGROUND: Exploding artillery barrages and angelic legions descending through burning clouds. "
                "High-contrast infernal-violet, molten-orange, and deep-navy palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (176, 180),
            "fallback_color": (14, 18, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyssal-realm-return book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Roy stepping through a jagged obsidian portal into the endless wasteland of the Abyss, "
                "his Cold Winter Armor radiating a chilling blue-black aura across volcanic plains and bone-strewn canyons. "
                "UPPER-RIGHT & BACKGROUND: Towering jagged demon citadels illuminated by a blood-red abyssal eclipse. "
                "High-contrast blood-crimson, glacial-cyan, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (181, 185),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted demon-lord-duel book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Roy unleashing a devastating frost-lightning beam from his clawed gauntlet, "
                "shattering the magma shield of a towering horned Demon Lord inside an abyssal arena. "
                "UPPER-RIGHT HORIZON: Rivers of lava freezing instantly into jagged black glaciers under Roy's domain. "
                "High-contrast electric-cyan, magma-crimson, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (186, 190),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted custom-bloodline-evolution book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy suspended midair inside a swirling vortex of pure soul energy and frost-fire magic circles, "
                "new demonic wings and arcane armor plates crystallizing around his muscular silhouette. "
                "UPPER-RIGHT SKY: Cascading translucent custom-creation blueprints and dark starlight piercing abyssal storm clouds. "
                "High-contrast soul-violet, frost-cyan, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (191, 195),
            "fallback_color": (24, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted underworld-legion-march book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy standing beside loyal demon lieutenants on a frozen obsidian cliff overlooking thousands of armored abyssal warriors "
                "marching across a bridge of solid black ice. "
                "UPPER-RIGHT & BACKGROUND: Colossal floating demon fortresses drifting through crimson-lit clouds. "
                "High-contrast crimson-slate, arctic-blue, and deep-violet palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (196, 200),
            "fallback_color": (16, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Lord-of-Winter-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Roy seated upon a jagged throne of black ice and obsidian in full Cold Winter Armor, "
                "scarlet pentagram eyes burning through his visor as a colossal phantom sovereign of frost and darkness towers behind him. "
                "UPPER-RIGHT HORIZON: Endless blizzard of dark ice blades swirling beneath twin crimson moons of the Abyss. "
                "High-contrast scarlet-crimson, glacial-cyan, and abyssal-black palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))