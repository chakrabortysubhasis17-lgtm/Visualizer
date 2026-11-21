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


BUILD_DIR = "build_sign_in_invincible_physique_1_50"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/sign-in-system-starting-with-invincible-physique/chapter-1",
    "novel_slug": "sign-in-system-starting-with-invincible-physique",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Sign-In System: Starting With Invincible Physique",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Series Premiere: Chapters 1 to 50)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Rhain Voss)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Rhain Voss",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"The original owner of this body died hoping someone would save him... I won\'t make that mistake. With the Abyssal Sovereign Physique awakened, everyone who trampled me in the Azure Cloud Sect is going to pay!"',
            "tts_text": '"The original owner of this body died hoping someone would save him... I won\'t make that mistake. With the Abyssal Sovereign Physique awakened... everyone who trampled me in the Azure Cloud Sect is going to pay!"',
            "text": '"The original owner of this body died hoping someone would save him... I won\'t make that mistake. With the Abyssal Sovereign Physique awakened, everyone who trampled me in the Azure Cloud Sect is going to pay!"',
            "voice": "en-US-AndrewMultilingualNeural",
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
            "display_text": "Betrayed on Earth and transmigrated into a bruised, talentless outer disciple on the brutal cultivation world of Aethermere, Rhain Voss activates the Sign-In System on Day One—claiming the Sovereign-Grade Abyssal Sovereign Physique to crush sect bullies and rise from the dirt across Chapters 1 through 50!",
            "tts_text": "Betrayed on Earth and transmigrated into a bruised, talentless outer disciple on the brutal cultivation world of Aethermere, Rhain Voss activates the Sign-In System on Day One... claiming the Sovereign-Grade Abyssal Sovereign Physique to crush sect bullies and rise from the dirt across Chapters 1 through 50!",
            "text": "Betrayed on Earth and transmigrated into a bruised, talentless outer disciple on the brutal cultivation world of Aethermere, Rhain Voss activates the Sign-In System on Day One—claiming the Sovereign-Grade Abyssal Sovereign Physique to crush sect bullies and rise from the dirt across Chapters 1 through 50!",
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
            "display_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "tts_text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
            "text": "Welcome to Being a Bong. We narrate the unreal worlds to life.",
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
            "display_text": "Sign-In System Alert: To claim your daily divine reward and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. On Aethermere, only the ruthless reign.",
            "tts_text": "Sign-In System Alert: To claim your daily divine reward and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. On Aethermere, only the ruthless reign.",
            "text": "Sign-In System Alert: To claim your daily divine reward and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. On Aethermere, only the ruthless reign.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "chime",
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
        # Beat 4: Series Premiere Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Sign-In System: Starting With Invincible Physique. Step into the Azure Cloud Sect, awaken the Abyssal Sovereign Physique, and witness Rhain Voss carve his path to supremacy.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Sign-In System: Starting With Invincible Physique. Step into the Azure Cloud Sect, awaken the Abyssal Sovereign Physique, and witness Rhain Voss carve his path to supremacy.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Sign-In System: Starting With Invincible Physique. Step into the Azure Cloud Sect, awaken the Abyssal Sovereign Physique, and witness Rhain Voss carve his path to supremacy.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "intrigue"
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
            "sfx": "teleport",
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
    "final_audio": "output_sign_in_invincible_physique_1_50.mp3",
    "final_video": "final_sign_in_invincible_physique_1_50.mp4",
    "cover_image": "cover_sign_in_invincible_physique_1_50.jpg",
    "timestamps_file": "youtube_timestamps_sign_in_invincible_physique_1_50.txt",
    "subtitles_file": "subtitles_sign_in_invincible_physique_1_50.srt",
    "payload_file": "youtube_upload_payload_sign_in_invincible_physique_1_50.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "SIGN-IN SYSTEM: STARTING WITH INVINCIBLE PHYSIQUE! [Chapters 1-50] | Ruthless Cultivation LitRPG Audiobook",
    "tags": [
        "Sign-In System Starting With Invincible Physique", "Sign-In System Audiobook", "Invincible Physique LitRPG",
        "Cultivation System Novel", "Rhain Voss", "Abyssal Sovereign Physique", "Xuanhuan Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to the premiere of 'Sign-In System: Starting With Invincible Physique!' (Part 1), covering Chapters 1 through 50!\n\n"
        "Betrayed on Earth for uncovering a corporate fraud and killed in a sudden accident, former analyst Rhain Voss awakens "
        "in a damp stone cell on Aethermere—inside the battered body of a talentless outer disciple beaten to death by bullies "
        "of the Azure Cloud Sect. Moments after his awakening, the Sign-In System initializes and grants him the Sovereign-Grade "
        "Abyssal Sovereign Physique, igniting a ruthless rise from disposable laborer to unstoppable cultivator!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE SIGN-IN & SYSTEM CULTIVATION MARATHONS ON BEING A BONG:\n"
        "• Sign-In: Starting With the Ancient Holy Body! -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• Invincible After 100 Years of Seclusion -> https://www.youtube.com/playlist?list=PL1uT5oX8D9F4\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#SignInSystem #InvinciblePhysique #CultivationAudiobook #LitRPG #Xuanhuan #RhainVoss #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Xuanhuan Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (16, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital xuanhuan-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of young disciple Rhain Voss inside a damp stone sect cell, "
                "dark abyssal-violet meridians igniting across his arms and eyes as translucent silver-bordered system panels shimmer beside him. "
                "UPPER-RIGHT BACKGROUND: Moonlit mist drifting past rugged mountain cliffs and wooden pagodas of the Azure Cloud Sect. "
                "High-contrast abyssal-violet, silver-cyan, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital sect-confrontation book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss clad in tattered outer-disciple robes delivering a devastating abyssal palm strike "
                "that sends three arrogant sect bullies flying across a stone training courtyard in shockwaves of dark Aetheric Essence. "
                "UPPER-RIGHT & BACKGROUND: Gathered disciples watching in disbelief beneath ancient pine trees and curved sect eaves. "
                "High-contrast royal-purple, crimson-amber, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital cultivation-breakthrough book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Rhain Voss meditating cross-legged atop a secluded spirit-vein cliff at night, "
                "swirling vortices of liquid Aetheric Essence pouring into his Abyssal Sovereign Physique like dark starlight. "
                "UPPER-RIGHT & BACKGROUND: Twin crescent moons illuminating sea-of-clouds peaks in the Outer Frontier Territories. "
                "High-contrast celestial-violet, luminous-cyan, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (24, 16, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Rhain Voss standing inside an ancient Sutra Pavilion hall beside a poised silver-eyed senior sect maiden, "
                "subtle dark-gold system sign-in runes pulsing quietly in the air as he claims a hidden martial scripture. "
                "UPPER-RIGHT SKY: Sunbeams slanting through tall lattice windows across towering scrolls and incense smoke. "
                "High-contrast warm-gold, deep-violet, and charcoal-navy palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (16, 22, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted demonic-beast-forest expedition book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss dashing through a mist-shrouded spirit forest, cleaving an armored iron-horned beast with a blade wreathed in abyssal black fire. "
                "UPPER-RIGHT & BACKGROUND: Towering ancient spirit-trees, glowing spirit herbs, and crumbling stone ruins. "
                "High-contrast emerald-mist, abyssal-purple, and iron-slate palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted sect-tournament arena book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Rhain Voss standing unmoved at the center of a cracked marble martial stage as an inner-disciple prodigy's sword shatters against his invincible physique, "
                "dark sovereign aura rippling outward like black lightning. "
                "UPPER-RIGHT & BACKGROUND: Shocked sect elders rising from tiered stone pavilions beneath billowing Azure Cloud banners. "
                "High-contrast imperial-violet, blinding-gold, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted secret-realm-ruins book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Rhain Voss descending into a sunken subterranean altar lit by violet soul-lanterns, "
                "absorbing a floating primordial essence crystal into his palm. "
                "UPPER-RIGHT HORIZON: Colossal carved dragon pillars and glowing spatial seals stretching into cavernous darkness. "
                "High-contrast amethyst-purple, jade-cyan, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (24, 12, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted blood-oath-ambush book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss unleashing an overwhelming Abyssal Sovereign domain blast in a narrow canyon pass, "
                "obliterating an ambush of rival-sect elders and crimson-cloaked assassins. "
                "UPPER-RIGHT SKY: Storm clouds torn apart by pillars of dark-violet and gold Aetheric Essence. "
                "High-contrast crimson-violet, molten-gold, and charcoal-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (16, 18, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted sovereign-forging & alliance book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss standing beside a fierce sword-maiden ally on a high cliffside terrace, "
                "forging a dark-gold spirit weapon over an ancient cauldron as translucent system milestone windows gleam beside him. "
                "UPPER-RIGHT & BACKGROUND: Endless mountain ranges and floating cloud-islands of the Outer Frontier Territories. "
                "High-contrast silver-blue, royal-purple, and warm-amber palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (20, 14, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Abyssal-Sovereign ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss standing atop the highest summit peak of the Azure Cloud Sect at dawn in dark-violet and gold robes, "
                "an immense shadowy Sovereign phantom materializing behind him in the clouds as Aetheric Essence bows to his physique. "
                "UPPER-RIGHT HORIZON: Golden sunrise breaking across an endless sea of clouds and distant immortal peaks. "
                "High-contrast sunrise-gold, abyssal-violet, and celestial-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))