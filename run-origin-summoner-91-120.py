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


BUILD_DIR = "build_origin_summoner_91_120"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/origin-summoner-all-my-summons-are-broken/chapter-91",
    "novel_slug": "origin-summoner-all-my-summons-are-broken",
    "start_chapter": 91,
    "end_chapter": 120,
    "is_start": False,
    "default_topic": "Origin Summoner: All My Summons Are Broken!",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 91 to 120)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Katherine - Calm Defiance -> impact + dread)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Katherine",
            "gender": "Female",
            "line_type": "Dialogue",
            "emotion": "calm_defiant",
            "age_category": "young",
            "display_text": '"A Level 20 Webfiend Lord with twelve limbs and a hundred eyes... even if a single blow shakes my bones, I won\'t take one step back until my summoner arrives!"',
            "tts_text": '"A Level Twenty Webfiend Lord with twelve limbs and a hundred eyes... even if a single blow shakes my bones... I won\'t take one step back until my summoner arrives!"',
            "text": '"A Level 20 Webfiend Lord with twelve limbs and a hundred eyes... even if a single blow shakes my bones, I won\'t take one step back until my summoner arrives!"',
            "voice": "en-US-AriaNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "+0Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "impact",
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
            "display_text": "When a nightmarish, twelve-armed Webfiend Lord steps out of the dark dungeon rift with peak Elite-level strength, swordswoman Katherine stands alone against overwhelming pressure—setting the stage for broken myth-grade summons, dungeon boss slaughters, and rapid ascension across Chapters 91 through 120!",
            "tts_text": "When a nightmarish, twelve-armed Webfiend Lord steps out of the dark dungeon rift with peak Elite-level strength, swordswoman Katherine stands alone against overwhelming pressure... setting the stage for broken myth-grade summons, dungeon boss slaughters, and rapid ascension across Chapters 91 through 120!",
            "text": "When a nightmarish, twelve-armed Webfiend Lord steps out of the dark dungeon rift with peak Elite-level strength, swordswoman Katherine stands alone against overwhelming pressure—setting the stage for broken myth-grade summons, dungeon boss slaughters, and rapid ascension across Chapters 91 through 120!",
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
            "display_text": "Origin Summoner Alert: To open your dimensional summoning gate and unlock this thirty-chapter dungeon marathon, hit that Like button and subscribe to the channel. Every contract breaks the rules of this world.",
            "tts_text": "Origin Summoner Alert: To open your dimensional summoning gate and unlock this thirty-chapter dungeon marathon, hit that Like button and subscribe to the channel. Every contract breaks the rules of this world.",
            "text": "Origin Summoner Alert: To open your dimensional summoning gate and unlock this thirty-chapter dungeon marathon, hit that Like button and subscribe to the channel. Every contract breaks the rules of this world.",
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
            "display_text": "Your immersion resumes now, covering Chapter 91 through Chapter 120 of Origin Summoner: All My Summons Are Broken. Step into the abyssal rift, face the Webfiend Lord, and unleash broken myth-grade power.",
            "tts_text": "Your immersion resumes now, covering Chapter Ninety-One through Chapter One Hundred and Twenty of Origin Summoner: All My Summons Are Broken. Step into the abyssal rift, face the Webfiend Lord, and unleash broken myth-grade power.",
            "text": "Your immersion resumes now, covering Chapter 91 through Chapter 120 of Origin Summoner: All My Summons Are Broken. Step into the abyssal rift, face the Webfiend Lord, and unleash broken myth-grade power.",
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
    "final_audio": "output_origin_summoner_91_120.mp3",
    "final_video": "final_origin_summoner_91_120.mp4",
    "cover_image": "cover_origin_summoner_91_120.jpg",
    "timestamps_file": "youtube_timestamps_origin_summoner_91_120.txt",
    "subtitles_file": "subtitles_origin_summoner_91_120.srt",
    "payload_file": "youtube_upload_payload_origin_summoner_91_120.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "ORIGIN SUMMONER: ALL MY SUMMONS ARE BROKEN! [Chapters 91-120] | Broken Summoner LitRPG Audiobook",
    "tags": [
        "Origin Summoner All My Summons Are Broken", "Origin Summoner Audiobook", "Broken Summoner LitRPG",
        "Dungeon Boss Progression Audiobook", "Katherine", "Webfiend Lord", "Summoner LitRPG", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Origin Summoner: All My Summons Are Broken!' (Part 4), covering Chapters 91 through 120!\n\n"
        "When a horrifying twelve-armed, multi-eyed Level 20 Webfiend Lord emerges from the dark dungeon rift with peak Elite-level "
        "physical power, emerald-eyed swordswoman Katherine stands her ground against crushing pressure—igniting an explosive "
        "dungeon boss showdown, broken myth-grade summoning contracts, and relentless progression across Chapters 91 through 120!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system status screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE SUMMONER & SYSTEM LITRPG MARATHONS ON BEING A BONG:\n"
        "• Beast Taming: My Beasts Grind, Die, and Respawn! -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n"
        "• Kingmaker System: The Pendragon Codex -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#OriginSummoner #SummonerLitRPG #DungeonBoss #LitRPG #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Summoner & Dungeon Boss Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (91, 93),
            "fallback_color": (18, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy dungeon-boss book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of composed emerald-eyed female swordswoman Katherine in silver-trimmed leather armor "
                "bracing her vibrating longsword as shockwaves crack the stone earth beneath her boots. "
                "UPPER-RIGHT BACKGROUND: Towering nightmarish Level 20 Webfiend Lord emerging from a swirling black dimensional rift with ten elongated shadowy arms and dozens of glowing cold eyes across its skull. "
                "High-contrast abyssal-violet, emerald-cyan, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (94, 96),
            "fallback_color": (22, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital origin-summoning-gate book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dark-haired young Origin Summoner extending his hand as a colossal golden-and-crimson dimensional summoning array erupts across the cavern floor, "
                "unleashing an overwhelmingly powerful myth-grade summon wreathed in arcane lightning against the twelve-armed dungeon boss. "
                "UPPER-RIGHT & BACKGROUND: Shattered dark silk webs, flying stone debris, and glowing translucent system status windows. "
                "High-contrast royal-gold, electric-violet, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (97, 99),
            "fallback_color": (14, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital boss-loot-and-evolution book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of the Origin Summoner examining a levitating crystalline core harvested from the fallen Webfiend Lord, "
                "while emerald-eyed Katherine cleans her blade beside glowing golden summoning runes swirling around his wrist. "
                "UPPER-RIGHT & BACKGROUND: Collapsing abyssal rift portal dissolving into shimmering starlight inside a cavernous dungeon hall. "
                "High-contrast celestial-cyan, molten-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (100, 102),
            "fallback_color": (20, 16, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Origin Summoner standing inside an ancient rune-carved summoning sanctuary as a massive crimson-and-gold astral guardian materializes behind him, "
                "translucent system panels illuminating his calm eyes as he unlocks a broken tier-bypass trait. "
                "UPPER-RIGHT SKY: Twin arcane circles rotating beneath vaulted Gothic cathedral-like stone arches. "
                "High-contrast imperial-gold, crimson-violet, and charcoal-navy palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (103, 105),
            "fallback_color": (24, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted rival-guild-confrontation book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Origin Summoner and swordswoman Katherine standing side-by-side at the entrance of a mist-shrouded canyon ruin, "
                "facing an arrogant squad of heavily armored guild hunters backed by conventional elemental beasts. "
                "UPPER-RIGHT & BACKGROUND: Jagged cliffs, glowing mana-veins, and ominous storm clouds gathering overhead. "
                "High-contrast blood-crimson, silver-steel, and twilight-purple palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (106, 108),
            "fallback_color": (16, 18, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted broken-summon-rampage book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: A towering, celestial-armored Origin Summon cleaving through an entire vanguard of rival summons with a single sweeping astral halberd arc, "
                "while the Origin Summoner watches calmly from a rocky ridge with glowing golden pupils. "
                "UPPER-RIGHT & BACKGROUND: Blinding shockwaves of sapphire and gold energy shattering boulder formations across the valley. "
                "High-contrast electric-sapphire, blinding-gold, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (109, 111),
            "fallback_color": (18, 22, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted sunken-abyss-descent book-cover illustration in top-ranking progression fantasy art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Katherine and the Origin Summoner descending a spiral obsidian stair into a deeper dungeon stratum, "
                "emerald sword-aura and golden summoning lanterns lighting ancient dragon-carved pillars. "
                "UPPER-RIGHT HORIZON: Glowing subterranean sea of violet mist and hovering ruined monoliths. "
                "High-contrast emerald-jade, amethyst-violet, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (112, 114),
            "fallback_color": (26, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted multi-summon-synergy-battle book-cover illustration in top-ranking dark-fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three distinct myth-grade Origin Summons—a shadow assassin wraith, a golden flame colossus, and an astral seraph—converging simultaneously "
                "upon a massive multi-headed abyssal hydra inside a lava-lit cavern. "
                "UPPER-RIGHT SKY: Cascading firestorms, dark lightning, and radiant summoning chains binding the beast. "
                "High-contrast molten-orange, abyssal-violet, and gold-white palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (115, 117),
            "fallback_color": (16, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted soul-contract-ascension book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Origin Summoner standing at the center of a vast celestial astrolabe floor as a new transcendent contract seal locks onto his palm, "
                "translucent level-up panels and soaring attribute readouts shimmering around his silhouette. "
                "UPPER-RIGHT & BACKGROUND: Starlit astral rift opening into an endless cosmic ocean of ancient summon silhouettes. "
                "High-contrast starlight-gold, royal-blue, and violet-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (118, 120),
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Origin-Sovereign book-cover illustration in top-ranking progression art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Origin Summoner standing atop a high cliffside citadel at dawn beside swordswoman Katherine, "
                "colossal spectral silhouettes of his broken myth-grade summons towering behind him in golden morning light. "
                "UPPER-RIGHT HORIZON: Brilliant sunrise breaking across endless mountain ranges and distant dungeon spires. "
                "High-contrast sunrise-gold, royal-purple, and emerald-slate palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
