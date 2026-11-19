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


BUILD_DIR = "build_weakest_beast_tamer_101_150"
purge_corrupt_cache(BUILD_DIR)

CONFIG = {
    "gemini_api_key": gemini_key,
    "cf_account_id": cf_id,
    "cf_api_token": cf_token,

    "source_type": "scrape",
    "start_url": "https://freewebnovel.com/novel/weakest-beast-tamer-gets-all-sss-dragons/chapter-101",
    "novel_slug": "weakest-beast-tamer-gets-all-sss-dragons",
    "start_chapter": 101,
    "end_chapter": 150,
    "is_start": False,
    "default_topic": "Weakest Beast Tamer Gets All SSS Dragons",

    "batch_size": 15,
    "parallel_chapters": 3,
    "global_max_tts": 6,
    "max_narration_merge": 650,
    "narrator_voice": "en-US-ChristopherNeural",
    "force_remaster": False,

    # Standard 5-Beat Intro Hook (Chapters 101 to 150 Continuation)
    "intro_hook": [
        # Beat 1a: Catchy In-Character Dialogue Hook (Ren)
        {
            "line_id": "intro_01a_dialogue",
            "speaker": "Ren",
            "gender": "Male",
            "line_type": "Dialogue",
            "pitch_tier": "lung_reset_entry",
            "lung_reset": True,
            "rate": "-2%",
            "pause_duration": 0.3,
            "display_text": '"People are not possessions you can claim by family decree—and right now, something far worse is shaking the shelter barriers!"',
            "tts_text": '"People are not possessions you can claim by family decree... and right now, something far worse is shaking the shelter barriers!"',
            "text": '"People are not possessions you can claim by family decree—and right now, something far worse is shaking the shelter barriers!"',
            "voice": "en-US-GuyNeural",
            "pitch": "+1Hz",
            "sfx": "hum",
            "bgm_mood": "tension"
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
            "display_text": "Mocked by arrogant noble heirs for his humble background and mysterious mushroom companion, Ren stands his ground in the academy shelter—just as violent tremors and an abyssal mercenary fusion erupt outside the walls, forcing Director Ignatius and his golden phoenix into a desperate clash!",
            "tts_text": "Mocked by arrogant noble heirs for his humble background and mysterious mushroom companion, Ren stands his ground in the academy shelter... just as violent tremors and an abyssal mercenary fusion erupt outside the walls, forcing Director Ignatius and his golden phoenix into a desperate clash!",
            "text": "Mocked by arrogant noble heirs for his humble background and mysterious mushroom companion, Ren stands his ground in the academy shelter—just as violent tremors and an abyssal mercenary fusion erupt outside the walls, forcing Director Ignatius and his golden phoenix into a desperate clash!",
            "voice": "en-US-ChristopherNeural",
            "pitch": "-2Hz",
            "sfx": "",
            "bgm_mood": "tension"
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
            "display_text": "Dragon Tamer Decree: To awaken SSS-rank draconic bloodlines and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. When abyssal war strikes, only true bonds command destiny.",
            "tts_text": "Dragon Tamer Decree: To awaken triple-S-rank draconic bloodlines and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. When abyssal war strikes, only true bonds command destiny.",
            "text": "Dragon Tamer Decree: To awaken SSS-rank draconic bloodlines and fuel this fifty-chapter marathon, hit that Like button and subscribe to the channel. When abyssal war strikes, only true bonds command destiny.",
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
            "display_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Weakest Beast Tamer Gets All SSS Dragons. Brace the protective barriers, analyze the enemy's mana, and watch Ren's legend soar.",
            "tts_text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Weakest Beast Tamer Gets All triple-S Dragons. Brace the protective barriers, analyze the enemy's mana, and watch Ren's legend soar.",
            "text": "Your immersion resumes now, covering Chapter 101 through Chapter 150 of Weakest Beast Tamer Gets All SSS Dragons. Brace the protective barriers, analyze the enemy's mana, and watch Ren's legend soar.",
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
    "final_audio": "output_weakest_beast_tamer_101_150.mp3",
    "final_video": "final_weakest_beast_tamer_101_150.mp4",
    "cover_image": "cover_weakest_beast_tamer_101_150.jpg",
    "timestamps_file": "youtube_timestamps_weakest_beast_tamer_101_150.txt",
    "subtitles_file": "subtitles_weakest_beast_tamer_101_150.srt",
    "payload_file": "youtube_upload_payload_weakest_beast_tamer_101_150.json",

    # Clean Background Configuration (No Logos or Burned-In Titles)
    "branding_assets": {
        "logo": None,
        "subscribe": None,
        "like": None,
        "voice": None
    },

    # YouTube Metadata
    "video_title": "WEAKEST BEAST TAMER GETS ALL SSS DRAGONS! [Chapters 101-150] | LitRPG Progression Audiobook",
    "tags": [
        "Weakest Beast Tamer Gets All SSS Dragons", "Weakest Beast Tamer Audiobook", "Ren",
        "Beast Tamer LitRPG", "SSS Dragons Audiobook", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Welcome back to 'Weakest Beast Tamer Gets All SSS Dragons' (Part 3), covering Chapters 101 through 150!\n\n"
        "Confronted in the shelter corridor by arrogant Goldcrest heir Klein and his roaring golden lion, Ren stands firm "
        "in defense of Luna—only for violent shockwaves to rattle the shelter's protective barriers. Outside, Director Ignatius "
        "and his golden phoenix clash against a ruthless mercenary unleashing abyssal mutations and true tamer fusion!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue and mana-analysis screens).\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "MORE BEAST TAMING & PROGRESSION MARATHONS ON BEING A BONG:\n"
        "• Five Element Overlord: I Can Upgrade Everything! -> https://www.youtube.com/playlist?list=PLe3rEPrQbet0\n"
        "• Copying Golden Traits: A LitRPG Cultivation Audio Drama -> https://www.youtube.com/playlist?list=PLMXchRJ2UDkQ\n"
        "• One Evolution Point Per Second: I Slay Gods with a Single Arrow -> https://www.youtube.com/playlist?list=PLfqw2zb3gGhI\n\n"
        "DISCLAIMER:\nThis dramatized audiobook adaptation is produced for educational, cultural commentary, "
        "and literary appreciation. Subscribe for more continuous audio releases!\n\n"
        "#WeakestBeastTamer #SSSDragons #BeastTamerAudiobook #LitRPG #ProgressionFantasy #BeingABong"
    ),

    # 10 Textless 2D/2.5D Beast-Tamer Fantasy Background Blocks (10 x 30s = 5-Minute Rolling HUD Loop)
    "blocks": [
        {
            "index": 1,
            "range": (101, 105),
            "fallback_color": (16, 22, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital beast-tamer fantasy book-cover illustration in top-ranking webnovel art style, "
                "crisp hand-painted brushwork, dramatic low-angle perspective, strictly zero 3D photorealism and no circular halo behind head, strictly no text or letters. "
                "FOREGROUND LEFT: Dynamic three-quarter medium close-up of calm young beast tamer Ren standing in a stone academy shelter corridor with small glowing spirit mushrooms nestled in his hair, "
                "facing down an arrogant noble boy flanked by a roaring golden-maned lion radiating bright solar mana. "
                "UPPER-RIGHT BACKGROUND: Flickering blue protective mana-barriers rippling across vaulted stone pillars as dust falls from tremors. "
                "High-contrast solar-gold, mystic-cyan, and slate-indigo palette --ar 16:9"
            )
        },
        {
            "index": 2,
            "range": (106, 110),
            "fallback_color": (30, 14, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital aerial-clash book-cover illustration in dynamic webnovel art style, "
                "rich painterly brushwork and explosive lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Blazing golden phoenix soaring through a stormy twilight sky, unleashing torrents of purifying golden fire "
                "against a feathered winged mercenary merged with a golden hippogriff and purple abyssal scorpion shadows. "
                "UPPER-RIGHT & BACKGROUND: Cracked ice barriers, swirling embers, and distant fortified academy domes. "
                "High-contrast phoenix-gold, abyssal-violet, and crimson-flame palette --ar 16:9"
            )
        },
        {
            "index": 3,
            "range": (111, 115),
            "fallback_color": (14, 26, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted digital mana-analysis book-cover illustration in top-ranking webnovel art style, "
                "dramatic chiaroscuro lighting and bold ink brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Three-quarter medium close-up of Ren resting one hand on a glowing spirit mushroom while translucent cyan mana-flow diagrams "
                "illuminate the air around him, analyzing beast cultivation pathways in a quiet sanctuary. "
                "UPPER-RIGHT & BACKGROUND: Bioluminescent spores drifting past ancient stone arches and glowing crystal lanterns. "
                "High-contrast emerald-cyan, warm-amber, and deep-teal palette --ar 16:9"
            )
        },
        {
            "index": 4,
            "range": (116, 120),
            "fallback_color": (24, 14, 30),
            "prompt": (
                "Masterpiece sharp anime-fantasy digital book-cover illustration in top-ranking progression fantasy style, "
                "dynamic composition and vibrant cel-shaded lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Ren standing defiantly beside young noblewoman Luna Starweaver beneath a shimmering star-barrier dome, "
                "small glowing mushrooms pulsing alertly as dark abyssal shockwaves slam against the outer shield. "
                "UPPER-RIGHT SKY: Storm clouds split by purple lightning and distant silhouettes of circling war-beasts. "
                "High-contrast starlight-silver, royal-violet, and midnight-black palette --ar 16:9"
            )
        },
        {
            "index": 5,
            "range": (121, 125),
            "fallback_color": (28, 18, 14),
            "prompt": (
                "Masterpiece 2D/2.5D painted dragon-awakening book-cover illustration in top-ranking webnovel art style, "
                "explosive painterly energy streaks and dramatic perspective, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ren raising his palm as a colossal spectral SSS-rank dragon silhouette unfurls behind him in blinding celestial fire, "
                "tiny glowing spirit mushrooms shimmering with ancient draconic resonance. "
                "UPPER-RIGHT & BACKGROUND: Shattered basalt cliffs, swirling elemental gales, and golden lightning arcs. "
                "High-contrast celestial-gold, crimson-ember, and obsidian-slate palette --ar 16:9"
            )
        },
        {
            "index": 6,
            "range": (126, 130),
            "fallback_color": (12, 24, 32),
            "prompt": (
                "Masterpiece 2D/2.5D painted ancient ruins expedition book-cover illustration in crisp digital webnovel art style, "
                "clean architectural lines and volumetric spotlighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "FOREGROUND LEFT: Ren leading his companion beasts through mist-shrouded dragon ruins, inspecting glowing runic pillars "
                "while small bioluminescent mushrooms light up hidden pathways in the dark. "
                "UPPER-RIGHT & BACKGROUND: Towering carved dragon statues, cascading underground waterfalls, and floating mana crystals. "
                "High-contrast mystic-blue, jade-green, and dark-slate palette --ar 16:9"
            )
        },
        {
            "index": 7,
            "range": (131, 135),
            "fallback_color": (26, 16, 24),
            "prompt": (
                "Masterpiece 2D/2.5D painted beast-arena duel book-cover illustration in top-ranking webnovel art style, "
                "rich painterly brushwork and warm dramatic lighting, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ren commanding a sleek young dragon companion in a grand academy arena, evading sweeping elemental claws "
                "with agile footwork honed through rigorous combat drills. "
                "UPPER-RIGHT HORIZON: Tiered stone coliseum stands packed with cheering spectators under sunlit banners. "
                "High-contrast molten-gold, royal-crimson, and deep-bronze palette --ar 16:9"
            )
        },
        {
            "index": 8,
            "range": (136, 140),
            "fallback_color": (14, 20, 34),
            "prompt": (
                "Masterpiece 2D/2.5D painted abyssal-frontiers defense book-cover illustration in top-ranking progression art style, "
                "dramatic worm's-eye angle and razor-sharp atmospheric brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ren standing atop a fortified rampart beside senior tamers as waves of corrupted abyssal beasts surge across a scorched valley below, "
                "channeling pure nature and dragon mana into defensive arrays. "
                "UPPER-RIGHT SKY: Dark crimson rift clouds pierced by beams of golden phoenix light. "
                "High-contrast electric-cyan, blazing-orange, and midnight-indigo palette --ar 16:9"
            )
        },
        {
            "index": 9,
            "range": (141, 145),
            "fallback_color": (20, 26, 18),
            "prompt": (
                "Masterpiece 2D/2.5D painted tranquil sanctuary campfire book-cover illustration in high-end webnovel art style, "
                "warm atmospheric rim lighting and sweeping brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ren sharing a quiet evening meal beside a warm forest camp with his spirit mushrooms and young draconic companions, "
                "soft golden firelight reflecting off smiling faces and shimmering scales. "
                "UPPER-RIGHT & BACKGROUND: Ancient silver-leafed trees, glowing fireflies, and a star-filled twilight sky. "
                "High-contrast warm-amber, emerald-moss, and twilight-blue palette --ar 16:9"
            )
        },
        {
            "index": 10,
            "range": (146, 150),
            "fallback_color": (32, 22, 12),
            "prompt": (
                "Masterpiece 2D/2.5D painted climactic dragon-tamer ascension book-cover illustration in top-ranking webnovel art style, "
                "grand panoramic composition and luminous celebratory brushwork, strictly zero 3D photorealism and no circular halo, strictly no text or letters. "
                "CENTER-LEFT FOREGROUND: Ren standing proudly atop a sunlit mountain overlook flanked by multiple majestic SSS-rank dragons of fire, storm, and starlight, "
                "tiny glowing spirit mushrooms shimmering atop his hair as wind sweeps his coat. "
                "UPPER-RIGHT HORIZON: Endless sea of golden sunrise clouds, distant academy spires, and soaring draconic silhouettes. "
                "High-contrast sunrise-gold, celestial-azure, and imperial-crimson palette --ar 16:9"
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))