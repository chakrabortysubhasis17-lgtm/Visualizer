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


BUILD_DIR = "build_custom_made_demon_king_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/custom-made-demon-king/chapter-101",
    "novel_slug": "custom-made-demon-king",
    "start_chapter": 101,
    "end_chapter": 150,
    "is_start": False,
    "default_topic": "Custom Made Demon King",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 101 to 150 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Roy)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Roy",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-4%",
            "pause_duration": 0.3,
            "display_text": '"Kid, I\'ll let you live on one condition—spread the word across every port! Until we find the crew that murdered her, revenge will never stop!"',
            "tts_text": '"Kid, I\'ll let you live on one condition... spread the word across every port! Until we find the crew that murdered her, revenge will nee-ver stop!"',
            "text": '"Kid, I\'ll let you live on one condition—spread the word across every port! Until we find the crew that murdered her, revenge will never stop!"',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch": "-1Hz",
            "sfx": "wind",
            "bgm_mood": "dread"
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
            "display_text": "Encasing an entire galleon in indestructible black ice, Demon Roy, the vengeful lich Cassandra, and the three-headed hellhound Fat Tiger unleash the terror of the Frozen Ghost Ship across the Caribbean seas—baiting Pirate Lords into a deadly storm of souls and Abyssal evolution!",
            "tts_text": "Encasing an entire galleon in indestructible black ice, Demon Roy, the vengeful lich Cassandra, and the three-headed hellhound Fat Tiger unleash the terror of the Frozen Ghost Ship across the Caribbean seas... baiting Pirate Lords into a deadly storm of souls and Abyssal evolution!",
            "text": "Encasing an entire galleon in indestructible black ice, Demon Roy, the vengeful lich Cassandra, and the three-headed hellhound Fat Tiger unleash the terror of the Frozen Ghost Ship across the Caribbean seas—baiting Pirate Lords into a deadly storm of souls and Abyssal evolution!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "dread"
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
            "display_text": "Abyssal Forge Decree: To fuel Roy's soul-creation altar and keep this fifty-chapter dark fantasy marathon sailing forward, hit that Like button and subscribe to the channel. Every soul fuels the next evolution.",
            "tts_text": "Abyssal Forge Decree: To fuel Roy's soul-creation altar and keep this fifty-chapter dark fantasy marathon sailing forward, hit that Like button and subscribe to the channel. Every soul fuels the next evolution.",
            "text": "Abyssal Forge Decree: To fuel Roy's soul-creation altar and keep this fifty-chapter dark fantasy marathon sailing forward, hit that Like button and subscribe to the channel. Every soul fuels the next evolution.",
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
            "display_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Custom Made Demon King. Board the Frozen Ghost Ship, hunt the Pirate Lords of Tortuga, and witness Roy harvest his way toward Demon Lord supremacy.",
            "tts_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Custom Made Demon King. Board the Frozen Ghost Ship, hunt the Pirate Lords of Tortuga, and witness Roy harvest his way toward Demon Lord supremacy.",
            "text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Custom Made Demon King. Board the Frozen Ghost Ship, hunt the Pirate Lords of Tortuga, and witness Roy harvest his way toward Demon Lord supremacy.",
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
            "sfx": "ocean",
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
    "final_audio": "output_custom_made_demon_king_101_150.mp3",
    "final_video": "final_custom_made_demon_king_101_150.mp4",
    "cover_image": "cover_custom_made_demon_king_101_150.jpg",
    "timestamps_file": "youtube_timestamps_custom_made_demon_king_101_150.txt",
    "subtitles_file": "subtitles_custom_made_demon_king_101_150.srt",
    "payload_file": "youtube_upload_payload_custom_made_demon_king_101_150.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "CUSTOM MADE DEMON KING [Chapters 101-150] | Dark Fantasy Abyss Evolution LitRPG Audiobook",
    "tags": [
        "Custom Made Demon King", "Abyss Evolution Audiobook", "Dark Fantasy LitRPG", "Demon Evolution Novel",
        "Soul Creation System", "Roy Demon King", "Lich Cassandra", "Fat Tiger Hellhound", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Custom Made Demon King' (Part 3), covering Chapters 101 through 150!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLOhHao1NCFug\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/q6cA74E9LH0\n\n"
        "After sealing a captured pirate galleon in indestructible black ice, Roy takes to the high seas alongside the vengeful lich "
        "Cassandra and the three-headed hellhound Fat Tiger—turning the Frozen Ghost Ship into a floating nightmare that forces "
        "the Pirate Lords of Tortuga into a high-stakes showdown!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK EVOLUTION & DUNGEON MARATHONS ON BEING A BONG:\n"
        "• Dungeon Overlord: Monster Girl Harem! -> https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• Blood Tyrant: Reborn as a Vampire Bat -> https://www.youtube.com/playlist?list=PLOBsw8kC9nH8\n"
        "• The Incubus System: Urban Fantasy LitRPG -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#CustomMadeDemonKing #DarkFantasyAudiobook #AbyssEvolution #LitRPG #DemonEvolution #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (101, 105),
            "fallback_color": (12, 22, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of horned black-armored demon Roy hovering with leathery wings above a pirate deck, "
                "channeling swirling black frost magic as a three-headed Cerberus hellhound lands beside a robed skeletal lich. "
                "UPPER-RIGHT BACKGROUND: A massive wooden galleon being rapidly encased in jagged black ice across a stormy ocean. "
                "High-contrast glacier-cyan, abyssal-violet, and midnight-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (106, 110),
            "fallback_color": (14, 24, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy naval-battle book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The colossal Frozen Ghost Ship encased in razor-sharp black ice ramming through ocean waves, "
                "with Roy and lich Cassandra standing on the frosted prow unleashing necromantic frost waves. "
                "UPPER-RIGHT & BACKGROUND: Panicked pirate schooners firing cannons into rolling mist and supernatural black fog. "
                "High-contrast frost-blue, obsidian-black, and ember-orange palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (111, 115),
            "fallback_color": (26, 16, 20),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy port-intrigue book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of ruthless Pirate Lords gathered around a lantern-lit war table in a weathered Tortuga harbor fortress, "
                "examining nautical charts surrounded by cutlasses and flintlock pistols. "
                "UPPER-RIGHT & BACKGROUND: Moonlit harbor windows revealing eerie blue-black frost mist creeping across the distant sea. "
                "High-contrast lantern-amber, deep-crimson, and shadow-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (116, 120),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic combat pose of lich Cassandra floating over dark waves, bony hands raised as swirling blue-black soul wisps spiral toward her staff, "
                "while three-headed hellhound Fat Tiger breathes hellfire across the ice deck. "
                "UPPER-RIGHT SKY: Storm clouds torn open by demon Roy descending with blazing abyssal claws. "
                "High-contrast spectral-cyan, hellfire-crimson, and obsidian-navy palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (121, 125),
            "fallback_color": (24, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy soul-forging book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Horned demon Roy standing before a floating crimson-and-violet Abyssal creation altar inside an ice-walled cabin, "
                "forging gleaming demonic armaments from harvested luminous soul orbs. "
                "UPPER-RIGHT & BACKGROUND: Floating translucent dark-system blueprints, arcane runes, and swirling spirit essence. "
                "High-contrast soul-violet, molten-crimson, and deep-obsidian palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (126, 130),
            "fallback_color": (14, 26, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy sea-monster clash book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Demon Roy soaring midair with wings spread wide, firing concentrated beams of frost-fire at colossal kraken tentacles "
                "erupting from turbulent black ocean waters around the Frozen Ghost Ship. "
                "UPPER-RIGHT & BACKGROUND: Jagged ice spires, crashing tidal waves, and lightning-lit storm clouds. "
                "High-contrast abyssal-teal, lightning-silver, and deep-charcoal palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (131, 135),
            "fallback_color": (26, 18, 16),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy fleet-showdown book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Roy standing calmly atop the frozen crow's nest, clawed hand extended as cursed gold and dark magic "
                "swirl around him while an armada of Pirate Lord galleons closes in. "
                "UPPER-RIGHT HORIZON: Burning cannon volleys illuminating a blood-red sunset over jagged coastal reefs. "
                "High-contrast blood-orange, frost-cyan, and iron-slate palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (136, 140),
            "fallback_color": (18, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy necromancy & vengeance book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Lich Cassandra unleashing an absolute-zero frost nova across an enemy flagship deck, "
                "freezing cursed pirate captains in mid-strike while Roy watches from above with glowing crimson eyes. "
                "UPPER-RIGHT SKY: Swirling vortex of harvested souls ascending into the night sky. "
                "High-contrast spectral-blue, royal-purple, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (141, 145),
            "fallback_color": (28, 14, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted dark-fantasy demonic-evolution book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Demon Roy undergoing a ferocious Abyssal bloodline evolution inside a cocoon of black flames and frost runes, "
                "his demonic armor and horns growing sharper as massive soul energy surges into his chest. "
                "UPPER-RIGHT & BACKGROUND: Three-headed hellhound Fat Tiger standing guard on the ice deck under a towering crimson full moon. "
                "High-contrast hellfire-crimson, abyssal-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (146, 150),
            "fallback_color": (22, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Abyssal-sovereign book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Evolved Demon Roy standing triumphant at the helm of the Frozen Ghost Ship alongside lich Cassandra and three-headed hellhound Fat Tiger, "
                "gazing toward a shimmering dimensional portal opening over the conquered sea. "
                "UPPER-RIGHT HORIZON: Dawn light breaking through parting storm clouds over wreckage-strewn waters. "
                "High-contrast abyssal-violet, sunrise-amber, and glacier-blue palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
