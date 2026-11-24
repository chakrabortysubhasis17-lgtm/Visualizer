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


BUILD_DIR = "build_beast_taming_376_410"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/beast-taming-my-beasts-grind-die-and-respawn/chapter-376",
    "novel_slug": "beast-taming-my-beasts-grind-die-and-respawn",
    "start_chapter": 376,
    "end_chapter": 410,
    "is_start": False,
    "default_topic": "Beast Taming: My Beasts Grind, Die, and Respawn",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 376 to 410)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Jin - Tactical Calm -> roar + tension)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Jin",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "calm_tactical",
            "age_category": "young",
            "display_text": '"A Rank 2 Stoneback Boar just wrecked our trap and scared off our target—good thing Glitch never backs down from a fight! Hold the line, buddy, we\'re capturing that rare beast before sundown!"',
            "tts_text": '"A Rank Two Stoneback Boar just wrecked our trap and scared off our target... good thing Glitch never backs down from a fight! Hold the line, buddy... we\'re capturing that rare beast before sundown!"',
            "text": '"A Rank 2 Stoneback Boar just wrecked our trap and scared off our target—good thing Glitch never backs down from a fight! Hold the line, buddy, we\'re capturing that rare beast before sundown!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "roar",
            "bgm_mood": "tension"
        },
        # Beat 1b: Narrative Teaser Hook (Slow, weighty delivery)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "ominous",
            "age_category": "adult",
            "display_text": "Deep in the rocky scree slopes alongside Lucian, Jin commands his drake Glitch, Flicker, and Kite through treacherous wilderness captures, high-stakes beast evolutions, and relentless respawn-dungeon grinds across Chapters 376 through 410!",
            "tts_text": "Deep in the rocky scree slopes alongside Lucian, Jin commands his drake Glitch, Flicker, and Kite through treacherous wilderness captures... high-stakes beast evolutions, and relentless respawn-dungeon grinds across Chapters 376 through 410!",
            "text": "Deep in the rocky scree slopes alongside Lucian, Jin commands his drake Glitch, Flicker, and Kite through treacherous wilderness captures, high-stakes beast evolutions, and relentless respawn-dungeon grinds across Chapters 376 through 410!",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-6%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "tension"
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
            "display_text": "Sovereign Game Engine Alert: To sync your soul-bond and unlock this thirty-five-chapter beast-taming marathon, hit that Like button and subscribe to the channel. Every respawn forges an apex monster.",
            "tts_text": "Sovereign Game Engine Alert: To sync your soul-bond and unlock this thirty-five-chapter beast-taming marathon, hit that Like button and subscribe to the channel. Every respawn forges an apex monster.",
            "text": "Sovereign Game Engine Alert: To sync your soul-bond and unlock this thirty-five-chapter beast-taming marathon, hit that Like button and subscribe to the channel. Every respawn forges an apex monster.",
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
            "display_text": "Your immersion resumes now, covering Chapter 376 through Chapter 410 of Beast Taming: My Beasts Grind, Die, and Respawn. Step onto the mountain scree, command your soul-beasts, and watch Jin push toward the pinnacle.",
            "tts_text": "Your immersion resumes now, covering Chapter Three Hundred and Seventy-Six through Chapter Four Hundred and Ten of Beast Taming: My Beasts Grind, Die, and Respawn. Step onto the mountain scree, command your soul-beasts, and watch Jin push toward the pinnacle.",
            "text": "Your immersion resumes now, covering Chapter 376 through Chapter 410 of Beast Taming: My Beasts Grind, Die, and Respawn. Step onto the mountain scree, command your soul-beasts, and watch Jin push toward the pinnacle.",
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
    "final_audio": "output_beast_taming_376_410.mp3",
    "final_video": "final_beast_taming_376_410.mp4",
    "cover_image": "cover_beast_taming_376_410.jpg",
    "timestamps_file": "youtube_timestamps_beast_taming_376_410.txt",
    "subtitles_file": "subtitles_beast_taming_376_410.srt",
    "payload_file": "youtube_upload_payload_beast_taming_376_410.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "BEAST TAMING: MY BEASTS GRIND, DIE, AND RESPAWN! [Chapters 376-410] | Monster Evolution LitRPG Audiobook",
    "tags": [
        "Beast Taming My Beasts Grind Die and Respawn", "Beast Taming Audiobook", "Monster Evolution LitRPG",
        "Progression Fantasy Audiobook", "Jin", "Glitch", "Lucian", "Flicker", "Kite", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Beast Taming: My Beasts Grind, Die, and Respawn!' (Part 8), covering Chapters 376 through 410!\n\n"
        "On a rugged mountain scree slope with his rival-turned-partner Lucian, Jin's carefully rigged trap for an elusive marten "
        "is suddenly smashed apart by a charging Rank 2 Stoneback Boar! With Glitch holding the armored beast back, Flicker and Kite "
        "scouting the cliffs, and Jin deploying Gravity Press to recover their gear, the duo regroups for a sharper capture strategy "
        "and pushes deeper into high-rank wilds across Chapters 376 through 410!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system status screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE BEAST-TAMING & PROGRESSION LITRPG MARATHONS ON BEING A BONG:\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n"
        "• Kingmaker System: The Pendragon Codex -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#BeastTaming #MonsterEvolution #LitRPG #ProgressionFantasy #Audiobook #BeingABong"
    ),

    # 10 Textless 2D/2.5D Beast-Taming Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (376, 379),
            "fallback_color": (18, 22, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital beast-taming progression book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-haired young beast tamer Jin crouching behind a boulder on a rocky mountain scree slope, "
                "channeling purple Gravity Press runes as his armored drake Glitch clashes shoulder-to-shoulder with a grey-plated Rank 2 Stoneback Boar. "
                "UPPER-RIGHT BACKGROUND: Agile tamer Lucian leaping with blue Stormstep static while agile bird companions Flicker and Kite circle rocky cliffs above. "
                "High-contrast slate-grey, electric-cyan, and amber-gold palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (380, 383),
            "fallback_color": (16, 24, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital wilderness-hunt book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and luminous rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Jin and Lucian perched atop a sun-dappled limestone overhang studying a hand-drawn mountain ridge map "
                "while nimble scout bird Flicker perches on Jin's gloved wrist and armored drake Glitch rests beside them. "
                "UPPER-RIGHT & BACKGROUND: Sweeping alpine valleys, mist-shrouded crags, and hidden beast trails winding through pine ridges. "
                "High-contrast emerald-pine, warm-sunlight, and stone-slate palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (384, 387),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital sovereign-game-engine book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Jin meditating beside a midnight campfire while translucent golden-and-sapphire system panels "
                "project a spectral virtual dungeon simulation where Glitch battles and respawns amidst swirling soul-essence sparks. "
                "UPPER-RIGHT & BACKGROUND: Starry mountain night sky and glowing bond threads linking Jin to his three resting beasts. "
                "High-contrast celestial-blue, molten-gold, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (388, 391),
            "fallback_color": (20, 18, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: High-speed aerial pursuit through a narrow canyon gorge, Flicker and Kite diving through wind currents "
                "to herd a glowing silver-furred spirit marten toward a camouflaged mana-net trap set by Jin and Lucian below. "
                "UPPER-RIGHT SKY: Dramatic sunbeams slicing through canyon clouds and swirling wind trails. "
                "High-contrast silver-cyan, amber-gold, and deep-slate palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (392, 395),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted beast-evolution-breakthrough book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and explosive energy streaks, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Armored drake Glitch roaring skyward inside a swirling vortex of crimson-gold and obsidian evolution flames, "
                "heavy metallic scales reforging into a higher combat rank as Jin channels soul-bond energy with an outstretched palm. "
                "UPPER-RIGHT & BACKGROUND: Translucent system milestone notifications gleaming across a rocky forest clearing. "
                "High-contrast molten-gold, obsidian-violet, and crimson-amber palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (396, 399),
            "fallback_color": (16, 22, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted beast-tamer-academy-trial book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Jin and Lucian standing back-to-back inside a grand stone beast-taming arena surrounded by their summoned combat beasts, "
                "facing rival upperclassmen commanding towering armored griffons and flame hounds. "
                "UPPER-RIGHT & BACKGROUND: Tiered coliseum galleries packed with spectators beneath fluttering academy banners. "
                "High-contrast royal-blue, blazing-orange, and marble-white palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (400, 403),
            "fallback_color": (22, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyssal-rift-expedition book-cover illustration in top-ranking progression fantasy art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Jin leading his beast squad into a mist-choked subterranean crystal cavern lit by bioluminescent fungi, "
                "Glitch's hardened scales deflecting toxic spore blasts from an ambush of giant subterranean crystal-arachnids. "
                "UPPER-RIGHT HORIZON: Jagged violet mana-crystals jutting from cavernous ceilings above an underground river. "
                "High-contrast amethyst-violet, emerald-cyan, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (404, 406),
            "fallback_color": (26, 16, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted apex-boss-clash book-cover illustration in top-ranking dark-fantasy art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Jin unleashing amplified Gravity Press alongside Lucian's crackling lightning palm strike, "
                "pinning a colossal Rampaging Iron-Horned Behemoth while Glitch charges in with blazing draconic jaws and Kite dives from above. "
                "UPPER-RIGHT SKY: Storm clouds torn open by golden and sapphire shockwaves over shattered boulders. "
                "High-contrast crimson-gold, electric-blue, and charcoal-slate palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (407, 408),
            "fallback_color": (18, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted bloodline-awakening & soul-contract book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Jin forming a glowing geometric soul-taming contract circle in midair "
                "with a newly tamed silver-and-gold spirit beast bowing respectfully before him as system rank-up panels shimmer beside his shoulder. "
                "UPPER-RIGHT & BACKGROUND: Moonlit ancient sanctuary ruins overlooking a serene mountain lake. "
                "High-contrast starlight-gold, silver-cyan, and twilight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (409, 410),
            "fallback_color": (20, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Sovereign-Tamer-summit book-cover illustration in top-ranking progression art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Jin standing atop a high mountain peak at dawn flanked by his evolved armored drake Glitch, Flicker, and Kite, "
                "gazing out over an endless frontier of uncharted beast territories as golden sunrise illuminates their synchronized soul-bond aura. "
                "UPPER-RIGHT HORIZON: Brilliant dawn light breaking across towering cloud-piercing peaks and distant wilderness valleys. "
                "High-contrast sunrise-gold, royal-sapphire, and emerald-slate palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
