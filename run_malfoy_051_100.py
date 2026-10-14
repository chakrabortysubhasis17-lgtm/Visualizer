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

CONFIG = {
    # Credentials (Loaded dynamically from api_credentials.json with env fallback)
    "gemini_api_key": creds.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", ""),
    "cf_account_id": creds.get("cloudflare_account_id") or os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
    "cf_api_token": creds.get("cloudflare_api_token") or os.environ.get("CLOUDFLARE_API_TOKEN", ""),

    # Novel & Episode Parameters
    "novel_slug": "hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation",
    "start_url": "https://mtl-novel.com/novel/hp-miss-malfoy-doesnt-want-to-romance-her-parents-generation/chapter-51/",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Miss Malfoy",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_hp_miss_malfoy_051_100",
    "final_audio": "output_hp_miss_malfoy_051_100.mp3",
    "final_video": "final_hp_miss_malfoy_051_100.mp4",
    "cover_image": "cover_hp_miss_malfoy_051_100.jpg",
    "timestamps_file": "youtube_timestamps_hp_miss_malfoy_051_100.txt",
    "subtitles_file": "subtitles_hp_miss_malfoy_051_100.srt",
    "payload_file": "youtube_upload_payload_hp_miss_malfoy_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "REFUSING TO ROMANCE THE MARAUDERS! PUREBLOOD SCHOLAR REWRITES DESTINY [Ch 51-100] | HP Fanfiction Audiobook Marathon",
    "tags": [
        "Harry Potter Fanfiction", "Miss Malfoy", "Marauders Era", "Slytherin",
        "Severus Snape", "Sirius Black", "Regulus Black", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Reincarnated into the treacherous Marauders era as a daughter of the Malfoy dynasty, "
        "she has zero interest in entangled teenage drama with her parents' generation!\n\n"
        "While Gryffindors pull immature corridor pranks and Slytherin purists blindly pledge loyalty "
        "to the looming shadow of the First Wizarding War, Miss Malfoy focuses on what truly matters: "
        "unmatched academic supremacy, forbidden ancient runes, alchemical innovations, and shielding "
        "her family from economic and political ruination.\n\n"
        "Surrounded by young Sirius Black, James Potter, Severus Snape, and Regulus Black, watch her deflect "
        "cloying romantic tropes with aristocratic poise and cold hexes while consolidating independent magical power!\n\n"
        "Welcome to Chapters 51 to 100 of 'HP: Miss Malfoy Doesn’t Want to Romance Her Parents’ Generation' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Term Break Innovations & Deciphering Ancient Nordic Defensive Wards\n"
        "• Ch 58: Confronting the Marauders' Corridors Prank with Effortless Non-Verbal Counter-Curses\n"
        "• Ch 64: Advanced Potions Masterclass: Out-Brewing Young Severus Snape\n"
        "• Ch 71: Malfoy Manor Winter Soiree: Manipulating Aristocratic Social Dynamics\n"
        "• Ch 78: Secret Incursions in the Restricted Section & Ancient Soul Magic Research\n"
        "• Ch 85: Black Lake Secrets & Awakening Dormant Silver-Serpent Familiars\n"
        "• Ch 92: Regulus Black's Warning & Neutralizing Radical Blood-Purist Factions\n"
        "• Ch 100: Sovereign Pureblood Scholar: Establishing Autonomous Power Outside the Dark Lord's Reach\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#HPFanfiction #MissMalfoy #MaraudersEra #Slytherin #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["ANCIENT RUNES STUDY", "SLYTHERIN SCHOLAR"],
            "fallback_color": (15, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of young Miss Malfoy, platinum-blonde hair styled in an elegant half-up braid, "
                "sharp aristocratic facial planes, piercing icy-grey pupils, wearing tailored emerald-and-silver Hogwarts Slytherin robes "
                "with an immaculate silk collar. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside the subterranean Slytherin common room beneath the Black Lake, revealing glowing water-filtered greenish light "
                "streaming through arched gothic glass with ancient rune parchment floating across heavy mahogany desks in the distance. "
                "Illumination from flickering emerald fireplace flames and floating magical silver quills, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["MARAUDERS DEFLECTED", "CORRIDOR CONFRONTATION"],
            "fallback_color": (25, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy with a composed disdainful smirk, raising an ornate hawthorn wand with fluid grace, "
                "hair ribbons fluttering in an abrupt draft of kinetic magic. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set within a dimly lit stone corridor of Hogwarts castle, revealing arrogant Gryffindor students "
                "reeling backward as a deflected trick hex detonates into colorful smoke against cobblestone walls in the distance. "
                "Illumination from golden wall sconce torches and crackling silver shield charms, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["DUNGEON CAULDRON", "POTIONS MASTERY"],
            "fallback_color": (15, 30, 25),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy in deep academic concentration, delicate brow furrowed slightly, "
                "holding a crystal phial filled with shimmering pearlescent potion, platinum curls framing her high cheekbones. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the cold stone dungeon potions classroom, "
                "revealing rows of brass cauldrons, pickled specimen jars on wooden shelves, and a young brooding Severus Snape observing in the distance. "
                "Illumination from soft violet brewing steam and glowing amber embers beneath cauldrons, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["MALFOY MANOR GALA", "ARISTOCRATIC STRATEGY"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy at a formal pureblood gala, serene untouchable expression, "
                "wearing an opulent emerald-velvet evening gown embroidered with silver peacocks and diamond-drop earrings. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the grand ballroom of Malfoy Manor, "
                "revealing crystal chandeliers, gilded mirrors, and masked aristocratic pureblood guests whispering behind champagne flutes in the distance. "
                "Illumination from warm golden candle chandeliers reflecting off polished marble floors, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["RESTRICTED SECTION", "FORBIDDEN SCROLLS"],
            "fallback_color": (15, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy holding an enchanted glass lantern, watchful calculating eyes, "
                "fingers gently turning the aged parchment of a chained forbidden grimoire. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set within the shadowy restricted section of the Hogwarts library at night, revealing towering oak bookshelves "
                "reaching into gothic vaulting and ethereal dust motes suspended in silence in the distance. "
                "Illumination from cool blue lantern rays cutting through deep library shadows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["BLACK LAKE SHORE", "SILVER SERPENT"],
            "fallback_color": (20, 30, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy standing by water's edge, dark-green winter travelling cloak lined with white ermine fur, "
                "calm noble gaze overlooking misty waters. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set along the rocky shores of the Black Lake at twilight, revealing a sleek silver water serpent coiling gracefully "
                "around a submerged stone pillar under the Scottish mountains in the distance. "
                "Illumination from pale silver twilight reflected on misty water ripples, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["ASTRONOMY TOWER", "STORMY DUEL"],
            "fallback_color": (25, 20, 40),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy in an offensive spellcasting stance, platinum hair whipped by stormy winds, "
                "intense steely glare, wand tip crackling with azure kinetic lightning. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the high open parapet of the Astronomy Tower during a midnight thunderstorm, revealing heavy rain, "
                "shattered stone masonry, and distant lightning strikes illuminating Hogwarts spires in the distance. "
                "Illumination from sharp flashes of lightning and vibrant electric-blue spell light, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["SECRET ENCOUNTER", "REGULUS BLACK'S DILEMMA"],
            "fallback_color": (20, 20, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy in discreet conversation, dignified cautious posture, arms crossed inside long silk sleeves, "
                "sharp discerning expression. Flawless facial features, crisp detailed skin textures, medium close-up shot. "
                "Set inside an abandoned stone classroom draped in cobwebs and vintage celestial globes, revealing a young Regulus Black "
                "in dark tailored robes clutching a family signet ring in hesitant discussion in the distance. "
                "Illumination from soft moonlight slanting through leaded lancet windows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["ALCHEMICAL TRANSCENDENCE", "ANCIENT CIRCLE"],
            "fallback_color": (30, 25, 35),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy conducting complex ritual alchemy, composed commanding presence, "
                "eyes shimmering with golden magic reflection as geometric runic rings hover about her palms. Flawless facial features, "
                "crisp detailed skin textures, medium close-up shot. Set inside a concealed chamber behind Slytherin dungeon tapestries, "
                "revealing carved stone floor arrays glowing with molten-gold light and floating alchemical apparatus in the distance. "
                "Illumination from bright golden ritual glyphs and deep emerald ambient shadows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["SOVEREIGN SCHOLAR", "REWRITING DESTINY"],
            "fallback_color": (15, 25, 30),
            "prompt": (
                "Cinematic 3D portrait of Miss Malfoy standing at the pinnacle of her school years, serene sovereign aura, "
                "windswept platinum-blonde hair crowned with a delicate silver serpent circlet, wearing an immaculate emerald silk high-collared mantle. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set on the viaduct bridge overlooking the vast expanse "
                "of Hogwarts Castle under an awe-inspiring dawn sky, with golden sunrise breaking over the Great Lake in the distance. "
                "Illumination from radiant morning sunlight, soft silver mist, and rich emerald reflections, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
