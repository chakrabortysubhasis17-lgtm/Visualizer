import os
import re
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

WATERMARK_PATTERNS = [
    re.compile(r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*", re.IGNORECASE),
    re.compile(r"https?://(?:m\.)?webnovel\.com/[^\s\"']+", re.IGNORECASE),
    re.compile(r"Ads\s+by\s+Pubfuture", re.IGNORECASE),
    re.compile(r"Pubfuture\s+Ads", re.IGNORECASE),
]


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
                has_watermark = any(
                    any(
                        pat.search(r.get("display_text") or r.get("tts_text") or r.get("text", ""))
                        for pat in WATERMARK_PATTERNS
                    )
                    for r in rows
                )
                if len(rows) < 8 or has_watermark or any(
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
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} stale/watermark cache files to guarantee clean scraping.", flush=True)


BUILD_DIR = "build_dungeon_overlord_201_250"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-overlord-monster-girl-harem/chapter-201",
    "novel_slug": "dungeon-overlord-monster-girl-harem",
    "start_chapter": 201,
    "end_chapter": 250,
    "is_start": False,
    "default_topic": "Dungeon Overlord: Monster Girl Harem!",

    "batch_size": 15,
    "parallel_chapters": 1,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Scraper & Line Sanitization Rules
    "strip_patterns": [
        r"Please\s+read\s+the\s+original\s+on\s+WebNovel[^\n]*",
        r"https?://(?:m\.)?webnovel\.com/[^\s\"']+",
        r"Ads\s+by\s+Pubfuture",
        r"Pubfuture\s+Ads",
        r"Read\s+latest\s+Chapters\s+at\s+FreeWebNovel[^\n]*",
    ],

    # Standard 5-Beat Intro Hook (Continuation: Chapters 201 to 250)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Leonhardt)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Leonhardt",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "arrogant_confident",
            "age_category": "young",
            "display_text": '"I\'ll bet an A-Grade Core that my dark elf Nyxara crushes you—my summoned monster will never lose to the likes of you!"',
            "tts_text": '"I\'ll bet an A-Grade Core that my dark elf Nyxara crushes you... my summoned monster will never lose to the likes of you!"',
            "text": '"I\'ll bet an A-Grade Core that my dark elf Nyxara crushes you—my summoned monster will never lose to the likes of you!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-3%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "chime",
            "bgm_mood": "intrigue"
        },
        # Beat 1b: Narrative Teaser Hook (Slow, weighty delivery)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "ominous",
            "age_category": "adult",
            "display_text": "Flouting the Dungeon Masters' code of conduct and wagering an entire A-Grade Core on his fierce dark elf Nyxara in a no-rules ranked duel, Leonhardt steps into the cutthroat arena of high-rank Dungeon Lords—expanding his monster girl legion and crushing rival clans across Chapters 201 through 250!",
            "tts_text": "Flouting the Dungeon Masters' code of conduct and wagering an entire A-Grade Core on his fierce dark elf Nyxara in a no-rules ranked duel... Leonhardt steps into the cutthroat arena of high-rank Dungeon Lords... expanding his monster girl legion and crushing rival clans across Chapters 201 through 250!",
            "text": "Flouting the Dungeon Masters' code of conduct and wagering an entire A-Grade Core on his fierce dark elf Nyxara in a no-rules ranked duel, Leonhardt steps into the cutthroat arena of high-rank Dungeon Lords—expanding his monster girl legion and crushing rival clans across Chapters 201 through 250!",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-6%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "intrigue"
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
            "display_text": "Dungeon Core Directive: To fortify Leonhardt's abyssal domain and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Overlord's dominion.",
            "tts_text": "Dungeon Core Directive: To fortify Leonhardt's abyssal domain and unlock this fifty chapter dark fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Overlord's dominion.",
            "text": "Dungeon Core Directive: To fortify Leonhardt's abyssal domain and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. Every soul fuels the Overlord's dominion.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "conversational_mid",
            "pitch": "-2Hz",
            "rate": "+0%",
            "lung_reset": False,
            "pause_duration": 0.3,
            "sfx": "interface",
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
            "display_text": "Your immersion resumes now, covering Chapter 201 through Chapter 250 of Dungeon Overlord: Monster Girl Harem. Witness Nyxara's deadly Shadow Step, dominate rival Dungeon Masters, and follow Leonhardt's ascent.",
            "tts_text": "Your immersion resumes now, covering Chapter 201 through Chapter 250 of Dungeon Overlord: Monster Girl Harem. Witness Nyxara's deadly Shadow Step, dominate rival Dungeon Masters, and follow Leonhardt's ascent.",
            "text": "Your immersion resumes now, covering Chapter 201 through Chapter 250 of Dungeon Overlord: Monster Girl Harem. Witness Nyxara's deadly Shadow Step, dominate rival Dungeon Masters, and follow Leonhardt's ascent.",
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
    "final_audio": "output_dungeon_overlord_201_250.mp3",
    "final_video": "final_dungeon_overlord_201_250.mp4",
    "cover_image": "cover_dungeon_overlord_201_250.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_overlord_201_250.txt",
    "subtitles_file": "subtitles_dungeon_overlord_201_250.srt",
    "payload_file": "youtube_upload_payload_dungeon_overlord_201_250.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUNGEON OVERLORD: MONSTER GIRL HAREM! [Chapters 201-250] | Dark Fantasy & Dungeon Core LitRPG Audiobook",
    "tags": [
        "Dungeon Overlord Monster Girl Harem", "Dungeon Core Audiobook", "Dark Fantasy LitRPG",
        "Monster Girl Harem", "Leonhardt", "Nyxara", "Ifrit", "Dravanna", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dungeon Overlord: Monster Girl Harem!' (Part 5), covering Chapters 201 through 250!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLHTTdkIdTors\n\n"
        "Ignoring the strict code of conduct inside the Dungeon Masters' enclave, Unranked Leonhardt provokes the D-Ranked "
        "Oni Vellod into a no-rules ranked duel—sending his dark elf warrior Nyxara into the rising arena while wagering "
        "an entire A-Grade Core on her victory! With Ifrit and Dravanna whispering in his mind and trembling Kobold Rock "
        "at his side, Leonhardt begins his ruthless climb past the lower ranks across Chapters 201 through 250!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, center-locked vocal clarity, stereo spatial ambience).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK FANTASY & HAREM LITRPG MARATHONS ON BEING A BONG:\n"
        "• The Incubus System -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n"
        "• Sign-In System: Starting With Invincible Physique -> https://www.youtube.com/playlist?list=PLqM14-u73g9U\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DungeonOverlord #MonsterGirlHarem #DungeonCore #DarkFantasyLitRPG #Leonhardt #Nyxara #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Fantasy Dungeon Overlord Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (201, 205),
            "fallback_color": (24, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dynamic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Agile golden-brown-skinned dark elf warrior maiden Nyxara with long pointed ears and twin purple-glowing daggers "
                "using Shadow Step across a rising circular obsidian duel arena against a towering muscular blue-skinned Oni warlord. "
                "UPPER-RIGHT BACKGROUND: Smirking dark-haired Dungeon Master Leonhardt watching calmly from a velvet balcony beside a small nervous Kobold. "
                "High-contrast royal-violet, blood-crimson, and obsidian-gold palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (206, 210),
            "fallback_color": (22, 12, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dungeon-enclave-gamble book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic chiaroscuro lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Leonhardt raising a blazing radiant A-Grade Dungeon Core amidst swirling golden contract threads, "
                "while spectral flame-spirit Ifrit and serpentine shadow-spirit Dravanna shimmer faintly behind his shoulders. "
                "UPPER-RIGHT & BACKGROUND: Ornate Gothic VIP balconies and shadowed upper-rank chambers overlooking the cavern lounge. "
                "High-contrast molten-gold, scarlet-crimson, and abyssal-purple palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (211, 215),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital subterranean-citadel book-cover illustration in top-ranking webnovel art style, "
                "dramatic rim lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt striding across a crystal-lit dungeon sanctum bridge flanked by loyal dark elf Nyxara and fierce monster-girl commanders, "
                "translucent crimson Dungeon Overlord management panels glowing beside his outstretched hand. "
                "UPPER-RIGHT & BACKGROUND: Colossal underground caverns lit by floating mana braziers and waterfalls of luminous blue mist. "
                "High-contrast sapphire-cyan, imperial-purple, and crimson-slate palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (216, 220),
            "fallback_color": (26, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking dark progression style, "
                "vibrant cel-shaded lighting and dynamic composition, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Alluring dragonkin and succubus generals kneeling before Leonhardt's obsidian throne in a candle-lit war room, "
                "unfolding a glowing three-dimensional arcane map of rival dungeon territories. "
                "UPPER-RIGHT BACKGROUND: Stained-glass demon-crest windows and towering obsidian pillars wrapped in crimson banners. "
                "High-contrast blood-crimson, antique-gold, and twilight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (221, 225),
            "fallback_color": (16, 20, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dungeon-raid-defense book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic action brushwork and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Nyxara and a fierce wolf-eared berserker maiden leading an ambush inside a trap-filled labyrinth corridor, "
                "unleashing purple shadow-blades and emerald hellfire against invading rival Dungeon Master troops. "
                "UPPER-RIGHT & BACKGROUND: Ancient rune-carved stone arches erupting with arcane lightning and smoke. "
                "High-contrast emerald-flame, electric-violet, and charcoal-stone palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (226, 230),
            "fallback_color": (24, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital monster-evolution-ritual book-cover illustration in crisp digital webnovel art style, "
                "luminous atmospheric depth and painterly brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Leonhardt channeling pure abyssal mana from a levitating Dungeon Core into his devoted monster-girl champions inside an arcane summoning circle, "
                "swirling ribbons of scarlet and silver light ascending around them. "
                "UPPER-RIGHT & BACKGROUND: Vaulted crystal dome reflecting swirling nebulae of dark mana. "
                "High-contrast rose-crimson, silver-violet, and midnight-blue palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (231, 235),
            "fallback_color": (20, 14, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted high-rank-enclave-clash book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt confronting an arrogant Rank-B aristocratic Dungeon Mistress on a marble terrace overlooking the subterranean city, "
                "crushing her intimidating aura with his own surging overlord pressure as Nyxara stands poised behind him. "
                "UPPER-RIGHT HORIZON: Floating fortress spires and glowing mana conduits spanning an abyssal chasm. "
                "High-contrast royal-gold, blood-crimson, and obsidian-violet palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (236, 240),
            "fallback_color": (26, 14, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital labyrinth-warfare book-cover illustration in top-ranking progression art style, "
                "dramatic low-angle framing and razor-sharp brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt wielding a dark-forged runic blade alongside his winged harpy and lamia commanders on a volcanic dungeon rampart, "
                "unleashing waves of crimson shadow-fire against an advancing horde of armored demon constructs. "
                "UPPER-RIGHT SKY: Molten magma rivers and glowing arcane barrier domes illuminating the cavernous ceiling. "
                "High-contrast molten-orange, crimson-violet, and dark-basalt palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (241, 245),
            "fallback_color": (22, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital core-ascension book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Leonhardt standing before his colossal pulsing Abyssal Dungeon Core, "
                "golden-crimson rank-up sigils orbiting his body while Nyxara and his loyal monster-girl retinue gaze up in devotion. "
                "UPPER-RIGHT & BACKGROUND: Towering obsidian monoliths inscribed with glowing demonic runes. "
                "High-contrast imperial-gold, scarlet-crimson, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (246, 250),
            "fallback_color": (18, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Dungeon-Overlord-dominion book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt standing triumphantly atop the grand citadel balcony of his expanded subterranean empire surrounded by his radiant monster-girl harem, "
                "looking out over conquered dungeon territories as crimson banners flutter in the warm mana breeze. "
                "UPPER-RIGHT HORIZON: Luminous bioluminescent crystal peaks and golden light beams piercing the cavern mists. "
                "High-contrast sunrise-gold, royal-violet, and crimson-scarlet palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))