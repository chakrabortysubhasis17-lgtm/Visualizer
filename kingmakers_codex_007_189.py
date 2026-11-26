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
        print(f"[Pre-Flight Cleanup] [✓] Purged {removed} placeholder cache files to guarantee clean parsing.", flush=True)


BUILD_DIR = "build_kingmaker_system_001_237"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "pdf",
    "pdf_path": r"D:\Projects\visualer\ebooks\The_Kingmakers_Codex_Vol1.pdf",
    "start_url": r"D:\Projects\visualer\ebooks\The_Kingmakers_Codex_Vol1.pdf",
    "novel_slug": "kingmaker-system-vol1",
    "start_chapter": 1,
    "end_chapter": 35,
    "is_start": True,
    "default_topic": "Kingmaker System: The Pendragon Codex",

    "use_gemini_director": False,  # True = Gemini prompt + fallback on error; False = direct fallback director
    "generate_video": False,       # True = full MP4 render; False = stop after mastered MP3

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Episodes 1 to 237 Series Premiere)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Aedan)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Aedan",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"Whoever compiled this elven stabilization array either wrote the recursive loop during a three-day honey-mead bender or wanted the Starwood to choke on its own mana!"',
            "tts_text": '"Whoever compiled this elven stabilization array either wrote the recursive loop during a three-day honey-mead bender or wanted the Starwood to choke on its own mana!"',
            "text": '"Whoever compiled this elven stabilization array either wrote the recursive loop during a three-day honey-mead bender or wanted the Starwood to choke on its own mana!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
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
            "display_text": "Reincarnated onto the parallel high-fantasy world of Aethelon as hedge apprentice Aedan, an Earth systems architect inherits The Pendragon Codex and Arch-Druid Merlin's dying root clearance—debugging rotting World-Tree spires, freeing Oak-Dryad Briar and Storm-Lynx Morwenna, rigging the Sword in the Stone for young Arthur, and founding Camelot!",
            "tts_text": "Reincarnated onto the parallel high-fantasy world of Ay-the-lon as hedge apprentice Ay-dan, an Earth systems architect inherits The Pendragon Codex and Arch-Druid Merlin's dying root clearance... debugging rotting World-Tree spires, freeing Oak-Dryad Briar and Storm-Lynx Morwenna, rigging the Sword in the Stone for young Arthur, and founding Camelot!",
            "text": "Reincarnated onto the parallel high-fantasy world of Aethelon as hedge apprentice Aedan, an Earth systems architect inherits The Pendragon Codex and Arch-Druid Merlin's dying root clearance—debugging rotting World-Tree spires, freeing Oak-Dryad Briar and Storm-Lynx Morwenna, rigging the Sword in the Stone for young Arthur, and founding Camelot!",
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
            "display_text": "Kingmaker System Decree: To synchronize your leyline channels and support this brand new original Being a Bong marathon, hit that Like button and subscribe to the channel. In the Realm of Logres, only the true architect sets the plumb-line of destiny.",
            "tts_text": "Kingmaker System Decree: To synchronize your leyline channels and support this brand new original Being a Bong marathon, hit that Like button and subscribe to the channel. In the Realm of Logres, only the true architect sets the plumb-line of destiny.",
            "text": "Kingmaker System Decree: To synchronize your leyline channels and support this brand new original Being a Bong marathon, hit that Like button and subscribe to the channel. In the Realm of Logres, only the true architect sets the plumb-line of destiny.",
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
            "display_text": "Your immersion begins now, starting from Episode 1 through Episode 237 of Kingmaker System. Step into the Crystal Spires of Brocéliande, unlock The Pendragon Codex, and witness the birth of a legendary kingdom.",
            "tts_text": "Your immersion begins now, starting from Episode 1 through Episode 237 of Kingmaker System. Step into the Crystal Spires of Bro-say-lee-ahnd, unlock The Pendragon Codex, and witness the birth of a legendary kingdom.",
            "text": "Your immersion begins now, starting from Episode 1 through Episode 237 of Kingmaker System. Step into the Crystal Spires of Brocéliande, unlock The Pendragon Codex, and witness the birth of a legendary kingdom.",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "wonder"
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
            "sfx": "impact",
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
    "final_audio": "output_kingmaker_system_001_237.mp3",
    "final_video": "final_kingmaker_system_001_237.mp4",
    "cover_image": "cover_kingmaker_system_001_237.jpg",
    "timestamps_file": "youtube_timestamps_kingmaker_system_001_237.txt",
    "subtitles_file": "subtitles_kingmaker_system_001_237.srt",
    "payload_file": "youtube_upload_payload_kingmaker_system_001_237.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "KINGMAKER SYSTEM! [Episodes 1-237] | Original Arthurian LitRPG Kingdom Saga Full Audiobook",
    "tags": [
        "Kingmaker System", "The Kingmakers Codex", "Being A Bong Original", "Arthurian LitRPG",
        "Progression Fantasy Audiobook", "Aedan", "Arthur Pendragon", "Briar", "Morwenna", "Seraphina", "Full Audiobook"
    ],
    "desc_header": (
        "Welcome to 'Kingmaker System: The Pendragon Codex' (Part 1 — An Original Saga by Being a Bong), covering Episodes 1 through 237!\n\n"
        "Reincarnated onto the parallel high-fantasy world of Aethelon as hedge apprentice Aedan (Devlin Vance), an Earth systems architect "
        "inherits [The Pendragon Codex] and Arch-Druid Merlin's dying root clearance. From debugging Brocéliande's rotting World-Tree spires "
        "and freeing Oak-Dryad Briar, Storm-Lynx Morwenna, and Crimson Lamia Seraphina, to rigging the Sword in the Stone for young Arthur "
        "Pendragon and founding Camelot beneath the shadow of Morgan le Fay!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and [Pendragon Codex] system UI).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE PROGRESSION & LITRPG MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\n'Kingmaker System (The Kingmaker's Codex)' is an original progression fantasy series written and produced by Being a Bong. "
        "Subscribe for more continuous original and adapted audio releases!\n\n"
        "#KingmakerSystem #TheKingmakersCodex #BeingABong #ArthurianLitRPG #ProgressionFantasy #FullAudiobook"
    ),

    # 10 Textless 2D/2.5D Arthurian-LitRPG Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 24),
            "fallback_color": (14, 24, 38),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Arthurian-fantasy book-cover illustration in top-ranking Royal Road progression novel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-haired arcana engineer Aedan wearing a brass-rimmed monocle and star-embroidered apprentice cloak, "
                "etching glowing silver-and-sapphire leyline runes into a massive glowing World-Tree root beside towering twelve-foot milky elven crystal spires. "
                "UPPER-RIGHT BACKGROUND: Aged half-elf Arch-Druid Merlin Ambrosius leaning on a glowing white ash staff beneath arched lancet observatory windows at violet dusk. "
                "High-contrast sapphire-blue, emerald-jade, and twilight-violet palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (25, 48),
            "fallback_color": (14, 28, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital forest-fantasy book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and luminous rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Sunken mossy amphitheater in Brocéliande Deep Grove, Aedan channeling emerald Starwood mana with his silver stylus "
                "to shatter black siphon vines binding tall emerald-haired Oak-Dryad Briar in dark-oak armor plates against an ancient hollow oak. "
                "UPPER-RIGHT & BACKGROUND: Swirling spring-green fireflies, red-barked yew trees, and misty forest canopies at dawn. "
                "High-contrast emerald-green, amber-gold, and deep-forest palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (49, 72),
            "fallback_color": (12, 22, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Mist-Lake book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Crescent pebble shoreline of Avalon's Mist-Lake, Aedan repairing a glowing Moon-Elven granite obelisk "
                "while serene silver-haired Undine sovereign Nimue glides effortlessly over mirror-still water in translucent azure river-silks. "
                "UPPER-RIGHT & BACKGROUND: Luminous sapphire mist barrier arcing across silver reeds under twin pale moons. "
                "High-contrast moon-silver, electric-cyan, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (73, 96),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Rain-slicked cobblestone alleyway in Caer-Londin at night, agile silver-haired Tempest-Lynx beastgirl Morwenna leaping midair "
                "with tufted lynx ears and lightning-charged tail crackling electric blue beside Aedan and Oak-Dryad Briar. "
                "UPPER-RIGHT SKY: Gothic stone arches, swinging copper lanterns, and steam rising from subterranean aqueduct grates. "
                "High-contrast electric-azure, warm-amber, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (97, 120),
            "fallback_color": (30, 22, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted iconic Sword-in-the-Stone book-cover illustration in top-ranking Arthurian progression art style, "
                "explosive painterly energy streaks and dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Young Arthur Pendragon standing atop white snow-dusted Cathedral marble steps, drawing the gleaming silver broadsword Caliburn "
                "from a rune-carved basalt anvil as a sixty-foot pillar of molten gold Astral-Dragon fire erupts skyward. "
                "UPPER-RIGHT & BACKGROUND: Towering white marble Light-Cathedral facade and spectral seven-starred golden dragon unfurling through winter clouds. "
                "High-contrast celestial-gold, royal-sapphire, and ivory-white palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (121, 144),
            "fallback_color": (28, 12, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted subterranean citadel book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lantern lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Aedan standing on a limestone aqueduct walkway sixty feet beneath Caerleon Citadel, holding a glowing dwarven forge-key "
                "before regal crimson-haired Lamia Seraphina coiling ten yards of glistening crimson-and-obsidian serpent scales out of dark canal water. "
                "UPPER-RIGHT & BACKGROUND: Vaulted dwarven stone arches, glowing bronze mana-conduits, and mist rising off subterranean channels. "
                "High-contrast crimson-ruby, molten-gold, and deep-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (145, 168),
            "fallback_color": (26, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted valley battle book-cover illustration in top-ranking progression fantasy art style, "
                "rich painterly brushwork and sweeping battlefield scale, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Flooded Bedegraine valley battlefield, solar-maned Lion-Kin knight Gawain charging alongside young King Arthur wielding blazing Caliburn, "
                "while torrents of diverted aqueduct water sweep through rebel warlord banners. "
                "UPPER-RIGHT HORIZON: Dramatic noon sunbeams piercing storm clouds over jagged Welsh mountain ridges. "
                "High-contrast solar-gold, crimson-banner, and slate-blue palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (169, 192),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted arcane-duel book-cover illustration in top-ranking dark-fantasy art style, "
                "dramatic angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ravishing dark-elf Witch-Queen Morgan le Fay standing on a high obsidian gallery rail, violet eyes blazing "
                "as crimson-and-black corrupted rune lattices clash midair against Aedan's emerald-and-sapphire leyline firewall. "
                "UPPER-RIGHT SKY: Swirling violet lightning vortexes over Gothic cathedral spires at dusk. "
                "High-contrast violet-magenta, emerald-cyan, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (193, 216),
            "fallback_color": (16, 24, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted ancient vault discovery book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Aedan inside the subterranean Omega Observatory Vault beneath Brocéliande, projecting a massive three-dimensional golden holographic map "
                "of the Realm of Logres and its glowing planetary firewall from Merlin's final astral echo-log. "
                "UPPER-RIGHT & BACKGROUND: Towering crystal memory pillars, floating geometric runes, and ancient dwarven-elven brass machinery. "
                "High-contrast celestial-gold, electric-cyan, and void-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (217, 237),
            "fallback_color": (32, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic kingdom-founding book-cover illustration in top-ranking Arthurian progression art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Kingmaker Aedan standing atop the sunlit granite summit of the Triple Leyline Nexus beside newly crowned High King Arthur, "
                "flanked by Oak-Dryad Briar, Storm-Lynx Morwenna, and Crimson Lamia Seraphina as golden leyline spires ignite across the valley. "
                "UPPER-RIGHT HORIZON: White marble foundations of rising Camelot shining beneath a triumphant sunrise sky. "
                "High-contrast sunrise-gold, royal-sapphire, and emerald-jade palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
