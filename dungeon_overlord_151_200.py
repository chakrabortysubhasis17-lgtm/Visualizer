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


BUILD_DIR = "build_dungeon_overlord_151_200"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dungeon-overlord-monster-girl-harem/chapter-151",
    "novel_slug": "dungeon-overlord-monster-girl-harem",
    "start_chapter": 151,
    "end_chapter": 200,
    "is_start": False,
    "default_topic": "Dungeon Overlord: Monster Girl Harem!",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Continuation: Chapters 151 to 200)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Leonhardt)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Leonhardt",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "seductive_commanding",
            "age_category": "young",
            "display_text": '"Welcome to my throne, my dear saintess. You could have turned back—yet here you stand between a succubus and a monster. Remember one rule in my dungeon: I expect loyalty... obedience is optional."',
            "tts_text": '"Welcome to my throne, my dear saintess. You could have turned back... yet here you stand between a succubus and a monster. Remember one rule in my dungeon: I expect loyalty... obedience is optional."',
            "text": '"Welcome to my throne, my dear saintess. You could have turned back—yet here you stand between a succubus and a monster. Remember one rule in my dungeon: I expect loyalty... obedience is optional."',
            "voice": "en-US-AndrewMultilingualNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "-1Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "portal",
            "bgm_mood": "intrigue"
        },
        # Beat 1b: Narrative Teaser Hook (Slower, atmospheric delivery)
        {
            "line_id": "intro_01b_narration",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "ominous",
            "age_category": "adult",
            "display_text": "Leaving Sylvie and Asuka tangled in silk sheets upstairs, Dungeon Overlord Leonhardt descends to his obsidian throne where jealous succubus Zafira and trembling saintess Erina await—preparing masked entry into a high-stakes underworld auction packed with rare treasures, monster-girl alliances, and ruthless domain warfare across Chapters 151 through 200!",
            "tts_text": "Leaving Sylvie and Asuka tangled in silk sheets upstairs, Dungeon Overlord Leonhardt descends to his obsidian throne where jealous succubus Zafira and trembling saintess Erina await... preparing masked entry into a high-stakes underworld auction packed with rare treasures, monster-girl alliances, and ruthless domain warfare across Chapters 151 through 200!",
            "text": "Leaving Sylvie and Asuka tangled in silk sheets upstairs, Dungeon Overlord Leonhardt descends to his obsidian throne where jealous succubus Zafira and trembling saintess Erina await—preparing masked entry into a high-stakes underworld auction packed with rare treasures, monster-girl alliances, and ruthless domain warfare across Chapters 151 through 200!",
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
            "display_text": "Dungeon Core Decree: To fill Leonhardt's treasury with platinum crests and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. Every tribute expands the Overlord's domain.",
            "tts_text": "Dungeon Core Decree: To fill Leonhardt's treasury with platinum crests and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. Every tribute expands the Overlord's domain.",
            "text": "Dungeon Core Decree: To fill Leonhardt's treasury with platinum crests and unlock this fifty-chapter dark fantasy marathon, hit that Like button and subscribe to the channel. Every tribute expands the Overlord's domain.",
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
            "display_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Dungeon Overlord: Monster Girl Harem. Don your mask, enter the underworld auction, and witness Leonhardt bend both saintess and monster to his will.",
            "tts_text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Dungeon Overlord: Monster Girl Harem. Don your mask, enter the underworld auction, and witness Leonhardt bend both saintess and monster to his will.",
            "text": "Your immersion resumes now, covering Chapter 151 through Chapter 200 of Dungeon Overlord: Monster Girl Harem. Don your mask, enter the underworld auction, and witness Leonhardt bend both saintess and monster to his will.",
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
    "final_audio": "output_dungeon_overlord_151_200.mp3",
    "final_video": "final_dungeon_overlord_151_200.mp4",
    "cover_image": "cover_dungeon_overlord_151_200.jpg",
    "timestamps_file": "youtube_timestamps_dungeon_overlord_151_200.txt",
    "subtitles_file": "subtitles_dungeon_overlord_151_200.srt",
    "payload_file": "youtube_upload_payload_dungeon_overlord_151_200.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DUNGEON OVERLORD: MONSTER GIRL HAREM! [Chapters 151-200] | Dark Fantasy LitRPG Audiobook",
    "tags": [
        "Dungeon Overlord Monster Girl Harem", "Dungeon Overlord Audiobook", "Monster Girl Harem LitRPG",
        "Dark Fantasy Progression Audiobook", "Leonhardt", "Zafira", "Sylvie", "Erina", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Dungeon Overlord: Monster Girl Harem!' (Part 4), covering Chapters 151 through 200!\n\n"
        "• Series Playlist: https://www.youtube.com/playlist?list=PLHTTdkIdTors\n"
        "• Start from Episode 1 (Chapters 1-50): https://youtu.be/eW0K-74v9eQ\n\n"
        "After a passionate night with ice-maiden Sylvie and dragonoid Asuka, Dungeon Overlord Leonhardt descends to his obsidian "
        "throne room to greet both his jealous succubus lieutenant Zafira and the trembling human saintess Erina. With goblin butler "
        "Griv's coffers overflowing with platinum crests and ornate masks prepared, Leonhardt steps into a dangerous underworld auction "
        "where rival lords, rare monster-girl contracts, and escalating warfare collide across Chapters 151 through 200!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE DARK FANTASY & HAREM LITRPG MARATHONS ON BEING A BONG:\n"
        "• Custom Made Demon King: Abyss Evolution LitRPG -> https://www.youtube.com/playlist?list=PLOhHao1NCFug\n"
        "• The Incubus System: Urban Fantasy Harem LitRPG -> https://www.youtube.com/playlist?list=PLYOPwavUi-DA\n"
        "• Dual Cultivation: Gathering SSS-Rank Wives -> https://www.youtube.com/playlist?list=PLaEbSwNtKKOQ\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DungeonOverlord #MonsterGirlHarem #DarkFantasyAudiobook #LitRPG #Leonhardt #BeingABong"
    ),

    # 10 Textless 2D/2.5D Dark Dungeon Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (151, 155),
            "fallback_color": (20, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital dark-fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-haired Dungeon Overlord Leonhardt in a black monster-hide coat and leather gauntlets "
                "standing beside his obsidian throne, flanked by alluring golden-eyed succubus Zafira in wine-red silk and wide-eyed green-eyed saintess Erina in a dusty traveling coat. "
                "UPPER-RIGHT BACKGROUND: Black marble dungeon walls etched with glowing silver mana veins and violet crystal lanterns. "
                "High-contrast royal-violet, crimson-wine, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (156, 160),
            "fallback_color": (24, 16, 26),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital masquerade-auction book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and dramatic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt, Zafira, and Erina wearing ornate silver-and-obsidian masquerade masks inside a shadow-draped VIP balcony "
                "overlooking a grand subterranean amphitheater lit by floating arcane chandeliers. "
                "UPPER-RIGHT & BACKGROUND: Cloaked underworld nobles and syndicate bidders raising glowing bidding tokens below. "
                "High-contrast molten-gold, abyssal-purple, and velvet-crimson palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (161, 165),
            "fallback_color": (16, 20, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital ice-and-flame chamber book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: White-haired frost maiden Sylvie with ice-blue eyes and drifting morning mist standing beside fierce caramel-skinned dragonoid Asuka "
                "on a moonlit dungeon balcony overlooking a subterranean forest of glowing magma-veined trees. "
                "UPPER-RIGHT & BACKGROUND: Swirling frost crystals colliding with rising amber embers in the cavern dome. "
                "High-contrast ice-cyan, ember-amber, and twilight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (166, 170),
            "fallback_color": (26, 14, 22),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Goblin butler Griv in a sharp monocle and tailored waistcoat presenting an overflowing chest of platinum crests and radiant monster cores "
                "to Leonhardt as translucent Dungeon Core upgrade panels shimmer beside the throne. "
                "UPPER-RIGHT SKY: Vaulted dark-stone treasury arches lined with ancient runes and gleaming arcane relics. "
                "High-contrast imperial-gold, emerald-green, and obsidian-purple palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (171, 175),
            "fallback_color": (18, 16, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted underworld-ambush book-cover illustration in top-ranking progression webnovel art style, "
                "luminous painterly brushwork and atmospheric depth, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt unleashing dark sovereign chains and abyssal blades in a torch-lit cobblestone alley outside the auction hall, "
                "shielding saintess Erina while succubus Zafira tears through cloaked mercenary assassins with dark-violet magic. "
                "UPPER-RIGHT & BACKGROUND: Gothic spires of the border city silhouetted against a crimson-streaked midnight sky. "
                "High-contrast blood-crimson, violet-shadow, and silver-steel palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (176, 180),
            "fallback_color": (22, 14, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted flaming-forest fortress book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Leonhardt standing atop the battlements of his hidden dungeon fortress overlooking disciplined regiments of goblin and kobold warriors "
                "marching through a glowing scarlet-leafed forest. "
                "UPPER-RIGHT & BACKGROUND: Towering obsidian watchtowers wreathed in swirling arcane mist and crimson embers. "
                "High-contrast infernal-orange, obsidian-black, and royal-purple palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (181, 185),
            "fallback_color": (16, 18, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted saintess-and-overlord intrigue book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Leonhardt and saintess Erina standing before an ancient glowing dungeon core crystal, "
                "soft golden divine light intertwining with dark abyssal mana between their outstretched hands. "
                "UPPER-RIGHT HORIZON: Crystalline cavern ceiling reflecting shimmering silver and gold magic circles. "
                "High-contrast holy-gold, deep-indigo, and violet-silver palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (186, 190),
            "fallback_color": (24, 12, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted dungeon-invasion clash book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Dragonoid Asuka and frost maiden Sylvie fighting side by side at the dungeon gate, "
                "a torrent of dragon-fire and razor-sharp ice spears obliterating an invading vanguard of armored templars and war beasts. "
                "UPPER-RIGHT SKY: Shattered barrier runes and billowing smoke over burning forest ridges. "
                "High-contrast blazing-crimson, glacial-blue, and charcoal-navy palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (191, 195),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece 2D/2.5D painted bloodline-evolution & pact book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt seated upon his obsidian throne channeling dark-violet sovereign energy into a newly awakened monster-girl vassal kneeling before him, "
                "floating translucent Dungeon Overlord status windows glowing in the shadows. "
                "UPPER-RIGHT & BACKGROUND: Towering rune-carved pillars and violet crystal braziers illuminating the throne hall. "
                "High-contrast royal-violet, molten-gold, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (196, 200),
            "fallback_color": (22, 16, 28),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Overlord-ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous dramatic brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Leonhardt standing on a high obsidian cliffside parapet at dawn surrounded by Zafira, Sylvie, Asuka, and Erina, "
                "a colossal shadowy Dungeon Overlord sigil pulsing in the sky above his sprawling monster dominion. "
                "UPPER-RIGHT HORIZON: First rays of crimson-gold sunrise breaking across endless dark mountains and mist-filled valleys. "
                "High-contrast sunrise-gold, abyssal-violet, and crimson-slate palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
