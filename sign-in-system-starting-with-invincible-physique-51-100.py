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


BUILD_DIR = "build_sign_in_invincible_physique_51_100"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/sign-in-system-starting-with-invincible-physique/chapter-51",
    "novel_slug": "sign-in-system-starting-with-invincible-physique",
    "start_chapter": 51,
    "end_chapter": 100,
    "is_start": False,
    "default_topic": "Sign-In System: Starting With Invincible Physique",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 51 to 100)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Rhain Voss - Ruthless Dominance -> clash + combat)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Rhain Voss",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "ruthless_cold",
            "age_category": "young",
            "display_text": '"Peak Essence Condensation experts ganging up on an Awakening Realm youth... and this is all you have? Get up, Vargas—I am not done torturing you yet!"',
            "tts_text": '"Peak Essence Condensation experts ganging up on an Awakening Realm youth... and this is all you have? Get up, Vargas... I am not done torturing you yet!"',
            "text": '"Peak Essence Condensation experts ganging up on an Awakening Realm youth... and this is all you have? Get up, Vargas—I am not done torturing you yet!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "clash",
            "bgm_mood": "combat"
        },
        # Beat 1b: Narrative Teaser Hook (Slow, weighty delivery)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "ominous",
            "age_category": "adult",
            "display_text": "With Seris and the freed elders watching, Rhain Voss unleashes Shadow Flicker Steps and the internal-detonating Void Fist—crushing Level 9 Condensation commanders Drask and Vargas single-handedly before stepping into the Essence Condensation Realm and larger frontier wars across Chapters 51 through 100!",
            "tts_text": "With Seris and the freed elders watching, Rhain Voss unleashes Shadow Flicker Steps and the internal detonating Void Fist... crushing Level 9 Condensation commanders Drask and Vargas single handedly before stepping into the Essence Condensation Realm and larger frontier wars across Chapters 51 through 100!",
            "text": "With Seris and the freed elders watching, Rhain Voss unleashes Shadow Flicker Steps and the internal-detonating Void Fist—crushing Level 9 Condensation commanders Drask and Vargas single-handedly before stepping into the Essence Condensation Realm and larger frontier wars across Chapters 51 through 100!",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "grim_rumble",
            "pitch": "-2Hz",
            "rate": "-6%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "combat"
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
            "display_text": "Sign-In System Alert: To claim your daily sovereign reward and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. On Aethermere, only the ruthless reign.",
            "tts_text": "Sign-In System Alert: To claim your daily sovereign reward and unlock this fifty chapter cultivation marathon, hit that Like button and subscribe to the channel. On Aethermere, only the ruthless reign.",
            "text": "Sign-In System Alert: To claim your daily sovereign reward and unlock this fifty-chapter cultivation marathon, hit that Like button and subscribe to the channel. On Aethermere, only the ruthless reign.",
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
            "display_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Sign-In System: Starting With Invincible Physique. Step into the bloodstained hall, shatter the Ironpeak and Barlowe alliances, and witness Rhain Voss ascend beyond mortal limits.",
            "tts_text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Sign-In System: Starting With Invincible Physique. Step into the bloodstained hall, shatter the Ironpeak and Barlowe alliances, and witness Rhain Voss ascend beyond mortal limits.",
            "text": "Your immersion resumes now, covering Chapter 51 through Chapter 100 of Sign-In System: Starting With Invincible Physique. Step into the bloodstained hall, shatter the Ironpeak and Barlowe alliances, and witness Rhain Voss ascend beyond mortal limits.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-3%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "intrigue"
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
    "final_audio": "output_sign_in_invincible_physique_51_100.mp3",
    "final_video": "final_sign_in_invincible_physique_51_100.mp4",
    "cover_image": "cover_sign_in_invincible_physique_51_100.jpg",
    "timestamps_file": "youtube_timestamps_sign_in_invincible_physique_51_100.txt",
    "subtitles_file": "subtitles_sign_in_invincible_physique_51_100.srt",
    "payload_file": "youtube_upload_payload_sign_in_invincible_physique_51_100.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "SIGN-IN SYSTEM: STARTING WITH INVINCIBLE PHYSIQUE! [Chapters 51-100] | Ruthless Cultivation LitRPG Audiobook",
    "tags": [
        "Sign-In System Starting With Invincible Physique", "Sign-In System Audiobook", "Invincible Physique LitRPG",
        "Cultivation System Novel", "Rhain Voss", "Void Fist", "Abyssal Sovereign Physique", "Xuanhuan Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Sign-In System: Starting With Invincible Physique!' (Part 2), covering Chapters 51 through 100!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLqM14-u73g9U\n\n"
        "When Rhain Voss gives the order to kill inside the besieged grand hall, Roderick Graves and the freed Azure Cloud elders "
        "clash head-on with the Ironpeak and Barlowe forces—while Rhain blitzes across the battlefield with Gale-Treading Steps and "
        "Shadow Flicker Steps! Unleashing his compressed dark Void Fist to shatter Level 9 Essence Condensation commanders Drask and "
        "Vargas from the inside out, Rhain pushes toward the Essence Condensation Realm and claims new Sign-In System treasures "
        "across Chapters 51 through 100!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE SIGN-IN & SYSTEM CULTIVATION MARATHONS ON BEING A BONG:\n"
        "• Dual Cultivation: Gathering SSS-Rank Wives -> https://www.youtube.com/playlist?list=PLaEbSwNtKKOQ\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#SignInSystem #InvinciblePhysique #CultivationAudiobook #LitRPG #Xuanhuan #RhainVoss #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Xuanhuan Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (51, 55),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital xuanhuan-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-robed cultivator Rhain Voss with golden-lit eyes flicking into three shadow afterimages "
                "as he drives a compressed dark-violet Void Fist into the armored back of a stunned Level 9 enemy commander inside a golden-pillared hall. "
                "UPPER-RIGHT BACKGROUND: Roderick Graves swinging a bloodstained heavy broadsword alongside Seris and four freed sect elders battling crimson-robed enemies. "
                "High-contrast abyssal-violet, molten-gold, and blood-crimson palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (56, 60),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital sect-victory & sign-in-reward book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss standing calmly in the aftermath of a shattered grand hall surrounded by defeated Ironpeak and Barlowe foes, "
                "a translucent silver-bordered Sign-In System reward panel hovering beside him as dark sovereign runes pulse over his palm. "
                "UPPER-RIGHT & BACKGROUND: Sunbeams piercing through broken stone arches onto victorious Azure Cloud disciples. "
                "High-contrast royal-purple, silver-cyan, and warm-amber palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (61, 65),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital realm-breakthrough book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Rhain Voss seated in deep meditation inside a secluded subterranean spirit-vein chamber, "
                "a dense vortex of liquid Aetheric Essence condensing into a dark-violet core within his dantian as his Abyssal Sovereign Physique radiates metallic sheen. "
                "UPPER-RIGHT & BACKGROUND: Glowing spirit crystals embedded in obsidian cavern walls casting rippling starlight reflections. "
                "High-contrast celestial-violet, luminous-cyan, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (66, 70),
            "fallback_color": (24, 16, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Rhain Voss walking beside poised dark-haired companion Seris along a high mountain precipice overlooking the Outer Frontier Territories, "
                "subtle dark-gold system sign-in runes glinting quietly in the mist as they prepare for an expedition beyond sect borders. "
                "UPPER-RIGHT SKY: Dramatic sea of clouds pierced by towering immortal peaks and distant flying spirit vessels. "
                "High-contrast warm-gold, deep-violet, and twilight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (71, 75),
            "fallback_color": (16, 22, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted ancient-battlefield-ruins book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss dashing across sunken titan sword monuments with Gale-Treading Steps, "
                "splitting a roaring crimson-scaled spirit beast with an abyssal palm strike wreathed in black lightning. "
                "UPPER-RIGHT & BACKGROUND: Colossal broken divine weapons jutting out of misty canyon cliffs under storm-lit skies. "
                "High-contrast emerald-mist, abyssal-purple, and iron-slate palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (76, 80),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted frontier-city-auction & intrigue book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Rhain Voss cloaked in a dark-violet hood inside a shadow-draped pavilion balcony overlooking a grand frontier city auction hall, "
                "examining an ancient blackened relic emitting faint sovereign resonance. "
                "UPPER-RIGHT & BACKGROUND: Lantern-lit tiered galleries filled with rival clan patriarchs and roaming mercenary experts. "
                "High-contrast imperial-violet, molten-gold, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (81, 85),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted nocturnal-ambush-slaughter book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Rhain Voss standing unharmed in a rain-drenched bamboo gorge as enemy blades shatter against his invincible physique, "
                "shadow afterimages darting through the mist to strike down black-clad assassins. "
                "UPPER-RIGHT HORIZON: Jagged lightning illuminating storm clouds over towering bamboo stalks. "
                "High-contrast electric-violet, silver-steel, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (86, 90),
            "fallback_color": (24, 12, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted sect-war-vanguard book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss hovering midair above a crumbling fortress gate, unleashing an overwhelming Void Fist shockwave "
                "that shatters a rival sect's grand defensive formation in a blast of dark-violet and gold essence. "
                "UPPER-RIGHT SKY: Marching banners and soaring cultivators clashing above smoke-filled mountain ridges. "
                "High-contrast crimson-violet, blinding-gold, and charcoal-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (91, 95),
            "fallback_color": (16, 18, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted forbidden-vault-sign-in book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss standing before a sealed celestial monolith inside a hidden ancestral tomb, "
                "golden-violet Sign-In System runes unlocking ancient dragon-carved doors as primordial essence pours outward. "
                "UPPER-RIGHT & BACKGROUND: Floating rune rings and luminous jade braziers illuminating vast subterranean halls. "
                "High-contrast jade-cyan, royal-purple, and warm-gold palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (96, 100),
            "fallback_color": (20, 14, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Frontier-Sovereign ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rhain Voss standing atop a sky-piercing peak at sunrise in dark-violet and gold martial robes, "
                "an immense shadowy Abyssal Sovereign phantom towering behind him in the clouds as Aetheric Essence bows to his newly ascended realm. "
                "UPPER-RIGHT HORIZON: Golden dawn light breaking across endless mountain chains and floating immortal citadels. "
                "High-contrast sunrise-gold, abyssal-violet, and celestial-indigo palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))