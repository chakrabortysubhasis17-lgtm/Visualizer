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


BUILD_DIR = "build_dominate_super_bowl_001_050"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/dominate-the-super-bowl/chapter-1",
    "novel_slug": "dominate-the-super-bowl",
    "start_chapter": 1,
    "end_chapter": 50,
    "is_start": True,
    "default_topic": "Dominate the Super Bowl: Gridiron System",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 1 to 50 Premiere)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Coach Burton Burns)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Coach Burton Burns",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"Your instantaneous start, acceleration, and body control are unseen—believe me, Li Wei, you are a natural-born running back!"',
            "tts_text": '"Your instantaneous start, acceleration, and body control are unseen... believe me, Lee Way, you are a natural-born running back!"',
            "text": '"Your instantaneous start, acceleration, and body control are unseen—believe me, Li Wei, you are a natural-born running back!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "cheer",
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
            "display_text": "After accidentally snapping a mugger's arm outside the University of Alabama library and unlocking the Football Training System, Chinese-American martial arts prodigy Li Wei steps onto the Crimson Tide gridiron—with zero football experience and the Super Bowl in his sights!",
            "tts_text": "After accidentally snapping a mugger's arm outside the University of Alabama library and unlocking the Football Training System, Chinese-American martial arts prodigy Lee Way steps onto the Crimson Tide gridiron... with zero football experience and the Super Bowl in his sights!",
            "text": "After accidentally snapping a mugger's arm outside the University of Alabama library and unlocking the Football Training System, Chinese-American martial arts prodigy Li Wei steps onto the Crimson Tide gridiron—with zero football experience and the Super Bowl in his sights!",
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
            "display_text": "Crimson Tide Dynasty Decree: To activate your Football Training System and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. Under the stadium lights, only champions claim the Lombardi Trophy.",
            "tts_text": "Crimson Tide Dynasty Decree: To activate your Football Training System and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. Under the stadium lights, only champions claim the Lombardi Trophy.",
            "text": "Crimson Tide Dynasty Decree: To activate your Football Training System and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. Under the stadium lights, only champions claim the Lombardi Trophy.",
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
            "display_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dominate the Super Bowl. Step onto the Tuscaloosa turf, claim your newbie gift package, and watch Li Wei take over American football.",
            "tts_text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dominate the Super Bowl. Step onto the Tuscaloosa turf, claim your newbie gift package, and watch Lee Way take over American football.",
            "text": "Your immersion begins now, starting from Chapter 1 through Chapter 50 of Dominate the Super Bowl. Step onto the Tuscaloosa turf, claim your newbie gift package, and watch Li Wei take over American football.",
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
    "final_audio": "output_dominate_super_bowl_001_050.mp3",
    "final_video": "final_dominate_super_bowl_001_050.mp4",
    "cover_image": "cover_dominate_super_bowl_001_050.jpg",
    "timestamps_file": "youtube_timestamps_dominate_super_bowl_001_050.txt",
    "subtitles_file": "subtitles_dominate_super_bowl_001_050.srt",
    "payload_file": "youtube_upload_payload_dominate_super_bowl_001_050.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "DOMINATE THE SUPER BOWL! [Chapters 1-50] | Sports LitRPG Progression Full Audiobook",
    "tags": [
        "Dominate the Super Bowl", "Dominate the Super Bowl Audiobook", "Li Wei", "American Football Novel",
        "Sports LitRPG Audiobook", "Progression Fantasy", "Crimson Tide Football", "NFL System Novel", "Being A Bong"
    ],
    "desc_header": (
        "Welcome to 'Dominate the Super Bowl' (Part 1), covering Chapters 1 through 50!\n\n"
        "Transmigrated to Tuscaloosa in 2016, Chinese-American martial arts student Li Wei accidentally breaks a mugger's arm "
        "outside the University of Alabama library—catching the eye of Crimson Tide coach Burton Burns and awakening the "
        "Football Training System. With zero football experience, a 6'1\" 216-pound frame, and explosive instincts, "
        "a new running back legend begins his march toward the Super Bowl!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and system screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE PROGRESSION & LITRPG MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#DominateTheSuperBowl #SportsLitRPG #ProgressionFantasy #LiWei #FootballAudiobook #BeingABong"
    ),

    # 10 Textless 2D/2.5D Sports-Fantasy Gridiron Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (1, 5),
            "fallback_color": (28, 12, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital sports-fantasy book-cover illustration in top-ranking progression novel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of athletic 20-year-old Chinese-American running back Li Wei on a rain-slicked stadium turf at night, "
                "sharp dark eyes glowing with electric-gold system vision, wearing sleek crimson-and-white football shoulder pads and jersey, gripping a leather football under one arm. "
                "UPPER-RIGHT SKY: Towering collegiate stadium floodlights piercing dark storm clouds over a roaring packed coliseum. "
                "High-contrast crimson-scarlet, electric-gold, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (6, 10),
            "fallback_color": (18, 28, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital sports-progression book-cover illustration in dynamic anime-fantasy webnovel art style, "
                "rich painterly brushwork and dramatic rim lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Explosive low-angle action shot of Chinese-American running back Li Wei bursting through a defensive line on white-striped green turf, "
                "kicking up blades of grass and glowing golden sparks, tucking the football tight as cyan tactical vision trajectories map open running lanes ahead. "
                "UPPER-RIGHT & BACKGROUND: Charging rival defenders in navy jerseys blurred in motion beneath bright afternoon stadium sunlight. "
                "High-contrast emerald-turf, tactical-cyan, and crimson-gold palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (11, 15),
            "fallback_color": (24, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital sports-drama book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up inside a massive collegiate athletic weight room at dusk, Li Wei chalking his hands beside heavy iron squat racks, "
                "sweat glistening, faint golden-amber system stat ribbons swirling around his forearms. "
                "UPPER-RIGHT & BACKGROUND: Tall industrial gym windows overlooking a twilight Alabama campus skyline and practice field goalposts. "
                "High-contrast molten-amber, crimson-slate, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (16, 20),
            "fallback_color": (14, 18, 36),
            "prompt": (
                "Masterpiece sharp anime-sports digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic Dutch-angle composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic juke-cut pose of running back Li Wei planting his cleat on the turf, sending a shockwave of crimson-and-gold kinetic energy as a diving defender misses completely. "
                "UPPER-RIGHT SKY: Massive roaring collegiate stadium bowl under dramatic Saturday night lights and swirling autumn wind. "
                "High-contrast crimson-red, blazing-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (21, 25),
            "fallback_color": (30, 14, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted gridiron clash book-cover illustration in top-ranking progression webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Fierce goal-line collision on a muddy championship field, running back Li Wei delivering a martial-arts-infused stiff-arm to an incoming linebacker with a burst of golden shockwave energy, "
                "flying mud droplets and turf pellets frozen in midair. "
                "UPPER-RIGHT & BACKGROUND: End-zone pylons, towering stadium bleachers ablaze with camera flashes, and crimson sunset clouds. "
                "High-contrast crimson-scarlet, molten-gold, and charcoal-black palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (26, 30),
            "fallback_color": (12, 24, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted combine showcase book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Li Wei crouched in a three-point sprint stance on a sleek indoor forty-yard dash track, silver-gold lightning crackling along his cleats, "
                "focused dark eyes locked down the lane. "
                "UPPER-RIGHT & BACKGROUND: High-tech domed stadium interior with holographic stopwatch arcs, upper-deck scouting booths, and dramatic overhead spotlights. "
                "High-contrast silver-gold, cobalt-blue, and obsidian palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (31, 35),
            "fallback_color": (26, 20, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted draft-night spectacle book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm theatrical lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Confident Chinese-American football prodigy Li Wei in a tailored dark charcoal suit and crimson-gold tie stepping onto a grand illuminated auditorium stage, "
                "holding up a pristine team jersey while golden spotlights and camera flashes erupt around him. "
                "UPPER-RIGHT HORIZON: Sweeping theater balconies filled with cheering crowds and glowing golden light beams. "
                "High-contrast champagne-gold, crimson-accent, and midnight-charcoal palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (36, 40),
            "fallback_color": (16, 24, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted blizzard playoff book-cover illustration in top-ranking progression sports art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Running back Li Wei hurdling over a diving tackler in a swirling winter snowstorm near the sideline, clutching the football tightly, "
                "breath steaming in the freezing air with an aura of incandescent gold willpower. "
                "UPPER-RIGHT SKY: Howling winter blizzard swirling beneath towering stadium light towers at night. "
                "High-contrast glacier-blue, blinding-white, and warm-gold palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (41, 45),
            "fallback_color": (28, 12, 22),
            "prompt": (
                "Masterpiece 2D/2.5D painted championship semifinal book-cover illustration in high-end progression novel art style, "
                "intense dramatic rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Running back Li Wei lined up in the backfield during a tense two-minute drill, eyes blazing gold as tactical system geometry illuminates the turf ahead, "
                "facing down a wall of imposing armored defenders. "
                "UPPER-RIGHT & BACKGROUND: Colossal domed megastadium packed with eighty thousand fans under dramatic crimson and indigo lights. "
                "High-contrast royal-crimson, celestial-gold, and deep-indigo palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (46, 50),
            "fallback_color": (32, 24, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic Super Bowl triumph book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Champion running back Li Wei standing victorious at the fifty-yard line in a crimson-and-gold championship jersey, helmet off, wind sweeping his black hair, "
                "raising a gleaming silver football trophy toward the sky amid falling golden confetti. "
                "UPPER-RIGHT HORIZON: Fireworks bursting above an open-roof megastadium into a triumphant twilight sky. "
                "High-contrast championship-gold, gleaming-silver, and royal-crimson palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
