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


BUILD_DIR = "build_sss_goddess_summon_436_475"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/starting-with-an-sss-rank-goddess-summon/chapter-436",
    "novel_slug": "starting-with-an-sss-rank-goddess-summon",
    "start_chapter": 436,
    "end_chapter": 475,
    "is_start": False,
    "default_topic": "Starting With an SSS-Rank Goddess Summon",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 436 to 475 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Thor)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Thor",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"Awakening lightning mid-brawl just to hit me with my own thunder?! Step into the ring, Dread Queen—show me the crushing weight of your sunless abyss!"',
            "tts_text": '"Awakening lightning mid-brawl just to hit me with my own thunder?! Step into the ring, Dread Queen... show me the crushing weight of your sunless abyss!"',
            "text": '"Awakening lightning mid-brawl just to hit me with my own thunder?! Step into the ring, Dread Queen—show me the crushing weight of your sunless abyss!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+0Hz",
            "sfx": "thunder",
            "bgm_mood": "combat"
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
            "display_text": "Inside Aeliana's boundless dimensional dome, the Crimson Dragon Talira forces an evolutionary breakthrough mid-combat before Dread Queen Morwenna draws Tidebringer against the God of Thunder—igniting a forty-chapter clash of primordial goddesses, divine weapons, and sovereign ascension!",
            "tts_text": "Inside Aeliana's boundless dimensional dome, the Crimson Dragon Talira forces an evolutionary breakthrough mid-combat before Dread Queen Morwenna draws Tidebringer against the God of Thunder... igniting a forty-chapter clash of primordial goddesses, divine weapons, and sovereign ascension!",
            "text": "Inside Aeliana's boundless dimensional dome, the Crimson Dragon Talira forces an evolutionary breakthrough mid-combat before Dread Queen Morwenna draws Tidebringer against the God of Thunder—igniting a forty-chapter clash of primordial goddesses, divine weapons, and sovereign ascension!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "combat"
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
            "display_text": "Sovereign Contract Decree: To stabilize the dimensional dome and power this forty-chapter goddess marathon, strike that Like button and subscribe to the channel. Every contract strengthens the pantheon.",
            "tts_text": "Sovereign Contract Decree: To stabilize the dimensional dome and power this forty-chapter goddess marathon, strike that Like button and subscribe to the channel. Every contract strengthens the pantheon.",
            "text": "Sovereign Contract Decree: To stabilize the dimensional dome and power this forty-chapter goddess marathon, strike that Like button and subscribe to the channel. Every contract strengthens the pantheon.",
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
        # Beat 4: Continuation Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "pitch_tier": "narrator_anchor",
            "lung_reset": False,
            "rate": "+0%",
            "pause_duration": 0.4,
            "display_text": "Your immersion resumes now, covering Chapter 436 through Chapter 475 of Starting With an SSS-Rank Goddess Summon. Enter Aeliana's sub-space, witness Mjolnir collide with Tidebringer, and follow the Sovereign's ascendant campaign.",
            "tts_text": "Your immersion resumes now, covering Chapter 436 through Chapter 475 of Starting With an triple-S-Rank Goddess Summon. Enter Aeliana's sub-space, witness Mjolnir collide with Tidebringer, and follow the Sovereign's ascendant campaign.",
            "text": "Your immersion resumes now, covering Chapter 436 through Chapter 475 of Starting With an SSS-Rank Goddess Summon. Enter Aeliana's sub-space, witness Mjolnir collide with Tidebringer, and follow the Sovereign's ascendant campaign.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "tension"
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
    "final_audio": "output_sss_goddess_summon_436_475.mp3",
    "final_video": "final_sss_goddess_summon_436_475.mp4",
    "cover_image": "cover_sss_goddess_summon_436_475.jpg",
    "timestamps_file": "youtube_timestamps_sss_goddess_summon_436_475.txt",
    "subtitles_file": "subtitles_sss_goddess_summon_436_475.srt",
    "payload_file": "youtube_upload_payload_sss_goddess_summon_436_475.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "STARTING WITH AN SSS-RANK GODDESS SUMMON! [Chapters 436-475] | Thor, Talira & Morwenna | LitRPG Audiobook",
    "tags": [
        "Starting With an SSS-Rank Goddess Summon", "SSS-Rank Goddess Summon Audiobook", "Goddess Summon LitRPG",
        "Thor vs Talira", "Dread Queen Morwenna", "Aeliana", "Progression Fantasy Audiobook", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Starting With an SSS-Rank Goddess Summon!' (Chapters 436-475)!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLP-ValiTEJPQ\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/C36j-7Gp7l8\n\n"
        "Inside Aeliana's isolated dimensional dome, the Asgardian God of Thunder Thor pushes Crimson Dragon Talira to awaken "
        "True Lightning mid-combat before turning her gaze toward Dread Queen Morwenna and her abyssal saber Tidebringer! As Mjolnir "
        "clashes with the crushing hydrostatic pressure of the deep ocean, new divine trials and Sovereign conquests unfold across "
        "Chapters 436 through 475.\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE GODDESS SUMMON & BEAST BOND MARATHONS ON BEING A BONG:\n"
        "• Beast Taming: Reincarnated With The Ultimate Bond System! -> https://www.youtube.com/playlist?list=PLRP3GDBqBHCQ\n"
        "• Beast Taming: My Beasts Grind, Die, and Respawn -> https://www.youtube.com/playlist?list=PLDrNA05qJDyo\n"
        "• SSS Awakening: I Can Devour Gods to Evolve My Goddesses -> https://www.youtube.com/playlist?list=PLbZqGY7n335k\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#SSSRankGoddessSummon #GoddessSummon #LitRPGAudiobook #ProgressionFantasy #Morwenna #BeingABong"
    ),

    # 10 Textless 2D/2.5D Divine Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (436, 439),
            "fallback_color": (28, 16, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital divine-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of fierce blonde-maned thunder warrior Thor in silver-plated armor catching a diving fifty-foot crimson dragon, "
                "golden lightning arcs colliding with molten dragon-fire and blue-white lightning inside a luminous white dimensional void. "
                "UPPER-RIGHT BACKGROUND: Elven Archon Aeliana channeling stabilizing runes while Dread Queen Morwenna watches from the sideline. "
                "High-contrast incandescent-gold, volcanic-crimson, and electric-cyan palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (440, 443),
            "fallback_color": (16, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital goddess-duel book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dread Queen Morwenna in a flowing black leather coat drawing the glowing blue-runic saber Tidebringer "
                "as a phantom sunless ocean and crushing crimson gravity vortex clash against Thor's spinning golden war hammer Mjolnir. "
                "UPPER-RIGHT & BACKGROUND: Fractured white spatial planes and abyssal ocean waves suspending in midair. "
                "High-contrast blood-crimson, deep-abyssal-blue, and blinding-gold palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (444, 447),
            "fallback_color": (18, 22, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital pantheon-council book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of the Sovereign standing inside an astral sanctuary surrounded by his SSS-rank goddesses—"
                "elven Archon Aeliana, crimson-haired Talira, storm-eyed Morwenna, and battle-ready Thor—reviewing glowing celestial star-maps. "
                "UPPER-RIGHT & BACKGROUND: Floating translucent divine system panels and sweeping nebulae beyond crystal arches. "
                "High-contrast celestial-gold, astral-violet, and silver-blue palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (448, 451),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic martial pose of crimson-haired dragon-girl Talira channeling newly awakened True Lightning and emerald wind currents around her gauntlets, "
                "sparks of blue-white electricity dancing across her volcanic-red scales. "
                "UPPER-RIGHT SKY: Dramatic storm-lit mountain peaks and soaring draconic silhouettes in twilight clouds. "
                "High-contrast ruby-crimson, electric-cyan, and emerald-gold palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (452, 455),
            "fallback_color": (14, 24, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted ancient-realm expedition book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The Sovereign leading Eluned, Aurelia, and Aeliana across a floating marble bridge spanning a sunken celestial abyss, "
                "divine summoning runes glowing beneath their boots. "
                "UPPER-RIGHT & BACKGROUND: Colossal ruined titan statues, cascading waterfalls of starlight, and swirling arcane mist. "
                "High-contrast jade-cyan, radiant-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (456, 459),
            "fallback_color": (26, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted divine-siege confrontation book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Thor and Morwenna fighting back-to-back atop a shattered citadel wall, golden lightning bolts and tidal abyssal slashes "
                "obliterating an advancing legion of corrupted divine constructs. "
                "UPPER-RIGHT & BACKGROUND: Blazing war banners, falling meteors, and glowing defensive domes across a besieged horizon. "
                "High-contrast molten-gold, abyssal-teal, and crimson-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (460, 463),
            "fallback_color": (18, 16, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted goddess-contract resonance book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm magical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of the Sovereign channeling golden-violet soul chains with Isolde and Ariadne inside a moonlit shrine, "
                "floating SSS-rank contract sigils illuminating their determined faces. "
                "UPPER-RIGHT HORIZON: Luminous constellation rings rotating slowly above ancient marble pillars. "
                "High-contrast royal-violet, celestial-gold, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (464, 467),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted domain-shattering climax book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Elven Archon Aeliana hovering midair with radiant staff raised, unleashing a sweeping dimensional prism wave "
                "that traps an encroaching dark deity inside crystalline spatial mirrors. "
                "UPPER-RIGHT SKY: Shattering reality cracks revealing swirling galaxies and golden divine light. "
                "High-contrast prism-cyan, imperial-gold, and deep-violet palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (468, 471),
            "fallback_color": (26, 16, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted sovereign-citadel celebration book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The Sovereign resting on a starlit terrace overlooking his sprawling sky-citadel alongside Liana Starweaver, Thera, and Vespera, "
                "warm lantern glow reflecting off floating crystal fountains. "
                "UPPER-RIGHT & BACKGROUND: Twin moons hanging over distant cloud-wrapped mountain peaks. "
                "High-contrast warm-amber, rose-gold, and twilight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (472, 475),
            "fallback_color": (28, 20, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic pantheon-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The Sovereign standing atop a floating celestial altar at sunrise flanked by his peerless SSS-rank goddesses—"
                "Thor, Morwenna, Talira, and Aeliana—as divine banners unfurl across the heavens. "
                "UPPER-RIGHT HORIZON: Endless sea of golden morning clouds, soaring divine beasts, and radiant astral gateways. "
                "High-contrast sunrise-gold, royal-purple, and crimson-cyan palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
