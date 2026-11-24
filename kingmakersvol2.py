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


BUILD_DIR = "build_kingmakers_codex_vol2_1_256"
purge_corrupt_cache(BUILD_DIR)

PDF_PATH = r"D:\Projects\visualer\ebooks\THE KINGMAKER'S CODEX Vol2.pdf"

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "pdf",
    "pdf_path": PDF_PATH,
    "start_url": PDF_PATH,
    "novel_slug": "kingmaker-system-vol2",
    "start_chapter": 1,
    "end_chapter": 256,
    "is_start": False,
    "default_topic": "Kingmaker System: The Pendragon Codex — Volume 2",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Volume 2 Continuation: Pages 1 to 256)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Aedan / Devlin Vance -> thunder + dread)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Aedan",
            "gender": "Male",
            "line_type": "Dialogue",
            "emotion": "commanding_cold",
            "age_category": "young",
            "display_text": '"Eleven rebel kings and two hundred Ashen warships think medieval siege iron can break Camelot before spring. Let them choke on First-Era steam-rails, sapphire sky-shields, and forty feet of awakened stone!"',
            "tts_text": '"Eleven rebel kings and two hundred Ashen warships think medieval siege iron can break Camelot before spring. Let them choke on First-Era steam-rails... sapphire sky-shields... and forty feet of awakened stone!"',
            "text": '"Eleven rebel kings and two hundred Ashen warships think medieval siege iron can break Camelot before spring. Let them choke on First-Era steam-rails, sapphire sky-shields, and forty feet of awakened stone!"',
            "voice": "en-US-GuyNeural",
            "pitch_tier": "lung_reset_entry",
            "pitch": "+1Hz",
            "rate": "-4%",
            "lung_reset": True,
            "pause_duration": 0.3,
            "sfx": "thunder",
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
            "display_text": "An original Arthurian magi-tech progression LitRPG written exclusively by Being a Bong. As Volume 2 of The Kingmaker's Codex opens with Iron Rails and Broken Crowns, Grand Architect Aedan and High King Arthur forge Starlight locomotives, raise Sky-Beacon Alpha, hijack Admiral Malakor's obsidian dreadnought, and unleash the forty-foot colossus WARDEN-01 against Morgan le Fay's coalition!",
            "tts_text": "An original Arthurian magi-tech progression LitRPG written exclusively by Being a Bong. As Volume Two of The Kingmaker's Codex opens with Iron Rails and Broken Crowns, Grand Architect Ay-dan and High King Arthur forge Starlight locomotives, raise Sky-Beacon Alpha, hijack Admiral Malakor's obsidian dreadnought... and unleash the forty-foot colossus Warden-Zero-One against Morgan le Fay's coalition!",
            "text": "An original Arthurian magi-tech progression LitRPG written exclusively by Being a Bong. As Volume 2 of The Kingmaker's Codex opens with Iron Rails and Broken Crowns, Grand Architect Aedan and High King Arthur forge Starlight locomotives, raise Sky-Beacon Alpha, hijack Admiral Malakor's obsidian dreadnought, and unleash the forty-foot colossus WARDEN-01 against Morgan le Fay's coalition!",
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
            "display_text": "Welcome back to Being a Bong. We write and narrate the unreal worlds to life.",
            "tts_text": "Welcome back to Being a Bong. We write and narrate the unreal worlds to life.",
            "text": "Welcome back to Being a Bong. We write and narrate the unreal worlds to life.",
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
            "display_text": "Pendragon Codex Alert: To reinforce Camelot's Planetary Firewall and unlock this complete Volume 2 original marathon, hit that Like button and subscribe to the channel. In the Realm of Logres, only the true architect sets the plumb-line of destiny.",
            "tts_text": "Pendragon Codex Alert: To reinforce Camelot's Planetary Firewall and unlock this complete Volume Two original marathon, hit that Like button and subscribe to the channel. In the Realm of Logres, only the true architect sets the plumb-line of destiny.",
            "text": "Pendragon Codex Alert: To reinforce Camelot's Planetary Firewall and unlock this complete Volume 2 original marathon, hit that Like button and subscribe to the channel. In the Realm of Logres, only the true architect sets the plumb-line of destiny.",
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
        # Beat 4: Volume 2 Continuation Bridge
        {
            "line_id": "intro_04_bridge",
            "speaker": "Narrator",
            "gender": "Neutral",
            "line_type": "Narration",
            "emotion": "dramatic",
            "age_category": "adult",
            "display_text": "Your immersion resumes now, covering Volume 2 of The Kingmaker's Codex: Iron Rails and Broken Crowns. Step onto Camelot's snowy ridge, ignite the Starlight boilers, and witness the Siege of Camelot.",
            "tts_text": "Your immersion resumes now, covering Volume Two of The Kingmaker's Codex: Iron Rails and Broken Crowns. Step onto Camelot's snowy ridge, ignite the Starlight boilers, and witness the Siege of Camelot.",
            "text": "Your immersion resumes now, covering Volume 2 of The Kingmaker's Codex: Iron Rails and Broken Crowns. Step onto Camelot's snowy ridge, ignite the Starlight boilers, and witness the Siege of Camelot.",
            "voice": "en-US-ChristopherNeural",
            "pitch_tier": "authoritative_low",
            "pitch": "-2Hz",
            "rate": "-3%",
            "lung_reset": False,
            "pause_duration": 0.4,
            "sfx": "",
            "bgm_mood": "wonder"
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
            "sfx": "impact",
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
    "final_audio": "output_kingmaker_system_vol2_1_256.mp3",
    "final_video": "final_kingmaker_system_vol2_1_256.mp4",
    "cover_image": "cover_kingmaker_system_vol2_1_256.jpg",
    "timestamps_file": "youtube_timestamps_kingmaker_system_vol2_1_256.txt",
    "subtitles_file": "subtitles_kingmaker_system_vol2_1_256.srt",
    "payload_file": "youtube_upload_payload_kingmaker_system_vol2_1_256.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "KINGMAKER SYSTEM: VOLUME 2! [Iron Rails & Broken Crowns] | Original Arthurian LitRPG Full Audiobook",
    "tags": [
        "Kingmaker System Volume 2", "The Kingmakers Codex Vol 2", "Iron Rails and Broken Crowns",
        "Being A Bong Original", "Arthurian LitRPG", "Progression Fantasy Audiobook",
        "Aedan", "Arthur Pendragon", "Nimue", "Vespera", "WARDEN-01", "Full Audiobook"
    ],
    "desc_header": (
        "Welcome back to 'Kingmaker System: The Pendragon Codex' (Volume 2: Iron Rails & Broken Crowns — An Original Saga by Being a Bong)!\n\n"
        "With High King Arthur crowned and Camelot rising above the Triple Leyline Nexus, Grand Architect Aedan (Devlin Vance) "
        "races against winter to forge First-Era Starlight steam-rails, ignite Sky-Beacon Alpha's planetary shield, and seal a naval "
        "treaty with Avalon's Mist-Lady Nimue. When eleven rebel kings and Admiral Malakor's two hundred obsidian dreadnoughts strike "
        "early under Morgan le Fay's corrupted banners, Aedan hijacks the flagship Obsidian Leviathan, wins over Dark-Elf Navigatrix "
        "Vespera, and unleashes the forty-foot First-Era colossus WARDEN-01!\n\n"
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

    # 10 Textless 2D/2.5D Arthurian-LitRPG Volume 2 Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 26),
            "fallback_color": (16, 22, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Arthurian-magitech book-cover illustration in top-ranking Royal Road progression novel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of dark-haired arcana engineer Aedan wearing a brass-rimmed monocle and wool command coat, "
                "guiding Dwarven master smith Thrain and Oak-Dryad Briar along gleaming frost-covered Starlight iron rails beside a billowing brass-and-iron steam locomotive. "
                "UPPER-RIGHT BACKGROUND: Unfinished white granite towers of Camelot ridge under twin pale winter moons and falling sleet. "
                "High-contrast sapphire-blue, warm-brass, and winter-slate palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (27, 52),
            "fallback_color": (12, 24, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital river-harbor treaty book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and luminous rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Rain-swept stone docks of Caer-Londin at dawn, Aedan draping his warm wool cloak over serene silver-haired Undine sovereign Nimue "
                "wearing flowing river-blue silks beside a translucent glowing silver Avalon mist-galley gliding past massive iron harbor boom-chains. "
                "UPPER-RIGHT & BACKGROUND: Crimson-haired Lamia Seraphina and Storm-Lynx Morwenna standing vigilant behind Aedan against river fog. "
                "High-contrast moon-silver, cerulean-blue, and crimson-amber palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (53, 78),
            "fallback_color": (14, 20, 38),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital Sky-Beacon ignition book-cover illustration in top-ranking progression webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Atop Camelot's hundred-twenty-foot octagonal granite spire, High King Arthur Pendragon touching blazing golden Excalibur to a twelve-ton Starlight crystal prism "
                "beside Aedan as a massive sapphire-and-gold beam erupts skyward to form a luminous hexagonal energy dome over the mountain citadel. "
                "UPPER-RIGHT & BACKGROUND: Winter storm clouds parted by dazzling cerulean geometry above terraced hydro-gardens. "
                "High-contrast celestial-sapphire, molten-gold, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (79, 104),
            "fallback_color": (20, 14, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Sixty feet beneath Camelot inside the steaming white quartz Triple Leyline Nexus, Aedan, Oak-Dryad Briar, and Crimson Lamia Seraphina "
                "channeling synchronized sapphire, emerald, and scarlet magic to incinerate a thrashing purple polymorphic void-worm inside the central crystal basin. "
                "UPPER-RIGHT SKY: Vaulted First-Era stone arches lit by cascading rivers of glowing liquid starlight. "
                "High-contrast emerald-green, scarlet-flame, and electric-sapphire palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (105, 130),
            "fallback_color": (18, 16, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted dreadnought-hijacking book-cover illustration in top-ranking Arthurian progression art style, "
                "explosive painterly energy streaks and dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Inside the purple-lit Void-Reactor Hold of the flagship Obsidian Leviathan, Aedan clashing sapphire First-Era code lattices "
                "against sleek silver-braided Dark-Elf Navigatrix Vespera beside a levitating ten-foot violet reactor sphere while freezing her obsidian neck-collar in blue stasis. "
                "UPPER-RIGHT & BACKGROUND: Brass catwalks, spinning gyroscopes, and sparking armored bulkheads. "
                "High-contrast electric-violet, ice-cyan, and obsidian-black palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (131, 156),
            "fallback_color": (16, 22, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted forty-foot colossus book-cover illustration in crisp digital webnovel art style, "
                "dramatic perspective and volumetric lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Striding through Camelot's smoking eastern stone breach, the forty-foot white-marble and golden-orichalcum First-Era colossus WARDEN-01 "
                "with Aedan standing atop its armored right shoulder, smashing massive void-quenched battering rams apart with nine-foot sapphire-lit bronze gauntlets. "
                "UPPER-RIGHT & BACKGROUND: High King Arthur, solar-maned Gawain, and living ironbark ramparts holding back twenty thousand northern rebel spears. "
                "High-contrast royal-sapphire, solar-gold, and slate-crimson palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (157, 182),
            "fallback_color": (26, 16, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted ash-field parley book-cover illustration in top-ranking progression fantasy art style, "
                "rich painterly brushwork and sweeping battlefield scale, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Across a snow-and-ash battlefield outside Camelot, High King Arthur and Grand Architect Aedan facing ravishing dark-elf Witch-Queen Morgan le Fay "
                "beside her hovering black-silk palanquin and six shadow-wyverns while Aedan projects a glaring blue hologram exposing her blood-siphoning war-banners. "
                "UPPER-RIGHT HORIZON: Looming forty-foot silhouette of WARDEN-01 and eleven stunned rebel monarchs on distant snowy ridges. "
                "High-contrast violet-crimson, celestial-blue, and ivory-snow palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (183, 208),
            "fallback_color": (28, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted bridge-duel & underground-express book-cover illustration in top-ranking dark-fantasy art style, "
                "dramatic angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: On the blazing oak bridge of Eastford at sunrise, solar-maned Lion-Kin champion Gawain cleaving his father King Lot's corrupted crimson war-standard in half "
                "with a blinding golden dawn-blade while an armored steam locomotive bursts out of a concealed quarry tunnel behind the rebel camp. "
                "UPPER-RIGHT SKY: First rays of golden sunrise piercing storm clouds over thousands of cheering northern Wolfkin warriors. "
                "High-contrast dawn-gold, fire-amber, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (209, 234),
            "fallback_color": (16, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted sea-raid-under-eclipse book-cover illustration in high-end webnovel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: The refitted three-hundred-foot flagship Obsidian Leviathan flying golden Pendragon dragon banners and glowing sapphire broadside ports, "
                "sailing beneath towering jagged black basalt sea-cliffs of Tintagel under a dramatic violet-rimmed eclipse. "
                "UPPER-RIGHT & BACKGROUND: Lady Nimue's silver mist-fleet and Storm-Lynx Morwenna perched above swirling ocean swells. "
                "High-contrast eclipse-violet, sapphire-cyan, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (235, 256),
            "fallback_color": (22, 16, 36),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Astral-Leviathan & Awakening-Sky book-cover illustration in top-ranking Arthurian progression art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Grand Architect Aedan and High King Arthur standing beside Dark-Elf Vespera and their sovereign guardians as shattered Void-Anchors release "
                "an ancient luminous Astral-Sea Leviathan into the heavens, restoring the golden-sapphire Planetary Firewall across Aethelon's sky. "
                "UPPER-RIGHT HORIZON: Brilliant starlight lattice sealing the orbital horizon above sunlit coastal cliffs. "
                "High-contrast starlight-gold, celestial-sapphire, and royal-violet palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
