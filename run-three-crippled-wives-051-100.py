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
    "novel_slug": "investing-in-my-three-crippled-wives-get-10000x-times-return",
    "start_url": "https://freewebnovel.com/novel/investing-in-my-three-crippled-wives-get-10000x-times-return/chapter-51",
    "start_chapter": 51,
    "end_chapter": 100,
    "default_topic": "Cultivation",

    # Concurrency Throttles
    "batch_size": 5,
    "parallel_chapters": 1,  # Sequential processing to prevent rate limit spikes
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_investing_three_wives_051_100",
    "final_audio": "output_investing_three_wives_051_100.mp3",
    "final_video": "final_investing_three_wives_051_100.mp4",
    "cover_image": "cover_investing_three_wives_051_100.jpg",
    "timestamps_file": "youtube_timestamps_investing_three_wives_051_100.txt",
    "subtitles_file": "subtitles_investing_three_wives_051_100.srt",
    "payload_file": "youtube_upload_payload_investing_three_wives_051_100.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "AWAKENING THREE PEERLESS EMPRESSES! 10,000X RETURN DOMINANCE [Ch 51-100] | Cultivation LitRPG Marathon",
    "tags": [
        "LitRPG Audiobook", "Investing In My Three Crippled Wives", "10000x Return System", "Gu Chen",
        "Cultivation Audiobook", "Xianxia", "Harem Cultivation", "Progression Fantasy", "Being A Bong"
    ],
    "desc_header": (
        "Having overturned the contempt of the entire clan, Gu Chen steps onto the grand stage of the cultivation world!\n\n"
        "With the continuous yields from the 10,000x Investment Return System, his three wives undergo complete physical and spiritual re-ascension. "
        "First Wife Ye Qingxue brandishes supreme primordial sword intent capable of severing mountain ranges; "
        "Second Wife Jiang Luoli fully transmutes the deadly Nine-Yin poison into an invincible Absolute Zero Frost Domain; "
        "and Third Wife Bai Ling unleashes the awe-inspiring phantom power of ancient mythic beast ancestors!\n\n"
        "As ancient sects, hidden dynasties, and predatory royal scions attempt to covet his wives and suppress his lineage, "
        "Gu Chen leverages every gifted heavenly treasure into massive critical multiplier rewards—surpassing holy lords, "
        "slaying supreme realm elders, and establishing an immortal family sanctuary!\n\n"
        "Welcome to Chapters 51 to 100 of 'Investing In My Three Crippled Wives Get 10,000x Times Return' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 51: Gifting the Primordial Sword Scripture & 10,000x Return of Chaos Sword Intent\n"
        "• Ch 60: Ancient Secret Realm Incursion & Crushing Elite Holy Land Scions\n"
        "• Ch 68: Jiang Luoli's Ice Imperial Bloodline Metamorphosis & Absolute Zero Freeze\n"
        "• Ch 75: Gifting Ancient Demon Beast Core & Bai Ling's Nine-Tailed Sovereign Awakening\n"
        "• Ch 82: The Holy Land Incursion Ambush & Gu Chen's Extreme Yang Sun Domain\n"
        "• Ch 90: Black Market Celestial Auction & The Million-Year Holy Lotus Investment\n"
        "• Ch 95: Severing the Supreme Realm Elder's Soul with Combined Wives Resonance\n"
        "• Ch 100: Grand Patriarch Gu Chen Sovereign Coronation & The Three Empress Realm\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#InvestingInMyThreeCrippledWives #10000xReturn #GuChen #CultivationAudiobook #Xianxia #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts (Unified High-Contrast 3D Portrait Specification)
    "blocks": [
        {
            "index": 1, "range": (51, 55),
            "title": ["CHAOS SWORD INTENT", "YE QINGXUE'S BREAKTHROUGH"],
            "fallback_color": (25, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of an authoritative young male cultivator, refined jawline, calm piercing amber-gold eyes, "
                "wearing flowing dark-navy silk robes embroidered with silver dragon constellations. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a secluded mountain pavilion chamber, revealing First Wife Ye Qingxue standing proudly beside him, "
                "brandishing a translucent divine flying sword emitting spiraling chaotic silver-and-black sword qi in the distance. "
                "Illumination from radiant silver blade gleams and floating golden investment return runes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (56, 60),
            "title": ["SECRET REALM EXPEDITION", "HOLY SCION PURGE"],
            "fallback_color": (20, 25, 45),
            "prompt": (
                "Cinematic 3D portrait of Cultivator Gu Chen, fierce focused expression, windswept dark hair, radiant electric-azure pupils, "
                "holding a glowing jade ancient key, wearing dark battle garments with reinforced vambraces. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set at the entrance of a colossal crumbling ancient grotto canyon, revealing defeated arrogant holy land disciples "
                "staggering backward under an invisible spiritual gravity wave in the distance. Illumination from neon-cyan ancient glyphs and crackling golden sparks, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (61, 65),
            "title": ["ICE EMPRESS ASCENT", "JIANG LUOLI'S COVENANT"],
            "fallback_color": (15, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of a poised male clan sovereign, warm compassionate gaze, dark hair, glowing amber eyes, "
                "handing an ornate crystalline frost elixir bottle forward. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside a glaciated palace grotto, revealing Second Wife Jiang Luoli, regal with flowing silver-white hair, "
                "manifesting enormous shimmering azure ice phoenix wings behind her back in the distance. Illumination from blinding crystalline sapphire rays "
                "and shimmering diamond dust, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (66, 70),
            "title": ["ABSOLUTE ZERO RETURN", "NINE-YIN DOMAIN PURGE"],
            "fallback_color": (20, 35, 45),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen mastering extreme Yin-Yang equilibrium, serene expression, dual-colored golden and frost-blue pupils, "
                "wearing charcoal-and-silver Taoist robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set atop a frozen snowy mountain summit under a starry night sky, revealing concentric rings of crystalline ice "
                "freezing the surrounding raging thunderclouds in the distance. Illumination from blinding turquoise ice radiance and warm golden dantian halos, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (71, 75),
            "title": ["NINE-TAILED SOVEREIGN", "BAI LING'S METAMORPHOSIS"],
            "fallback_color": (35, 20, 35),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen, gentle protective smile, sharp handsome facial structure, luminous amber eyes, "
                "wearing dark flowing silk robes with gold filigree clasps. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in an ancient bamboo spiritual grove, revealing innocent Third Wife Bai Ling transformed into a majestic celestial maiden, "
                "flourishing nine ethereal translucent amethyst fox tails dancing with divine starlight in the distance. "
                "Illumination from soft violet divine fire and golden celestial wisps, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (76, 80),
            "title": ["MYTHIC BEAST PHANTOM", "ANCESTRAL INVESTMENT RETURN"],
            "fallback_color": (40, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of a commanding cultivator patriarch, dark hair whipped by kinetic currents, fierce glowing magenta pupils, "
                "surrounded by floating ancient beast bone runes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set against an expansive storm-torn horizon, revealing the colossal spectral phantom of a primordial divine qilin "
                "bowing loyally behind him in the distance. Illumination from crackling amethyst lightning bolts and deep golden ancestral auras, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (81, 85),
            "title": ["HOLY LAND CONFRONTATION", "EXTREME YANG SUN DOMAIN"],
            "fallback_color": (45, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen in battle readiness, razor-sharp jawline, blazing sun-gold eyes, "
                "wearing blackened dragon-scale mantle armor over crimson robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set in a shattered mountain battlefield, revealing advancing hostile holy land elders engulfed in roaring golden "
                "solar flames erupting from Gu Chen's expansive territory domain in the distance. Illumination from blinding white-yellow solar fire columns "
                "and shimmering heat ripples, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (86, 90),
            "title": ["CELESTIAL AUCTION", "MILLION-YEAR LOTUS"],
            "fallback_color": (30, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of a wealthy master patriarch, refined handsome features, calm calculating golden eyes, "
                "wearing an imperial midnight-blue formal coat with intricate gold embroidery. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an opulent multi-tiered underground auction colosseum, revealing an ethereal nine-colored spiritual lotus "
                "floating on an enchanted jade pedestal in the distance. Illumination from warm brass chandeliers and shimmering iridescent lotus luminescence, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (91, 95),
            "title": ["SOUL SEVERING STRIKE", "THREE WIVES HARMONY"],
            "fallback_color": (25, 30, 45),
            "prompt": (
                "Cinematic 3D portrait of Gu Chen commanding supreme divine energy, floating strands of black hair, radiant tri-colored irises, "
                "directing a multi-layered heavenly barrier with raised palms. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set high above the clouds, revealing Ye Qingxue, Jiang Luoli, and Bai Ling executing a synchronized elemental strike "
                "that fractures a giant enemy supreme elder's soul phantom in the distance. Illumination from silver sword light, frost blue mist, and violet beast fires, "
                "deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (96, 100),
            "title": ["GRAND PATRIARCH CORONATION", "THE THREE EMPRESSES"],
            "fallback_color": (25, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Sovereign Patriarch Gu Chen at peak dominion, majestic windswept dark hair, imperial glowing sun-gold eyes, "
                "wearing ornate imperial black-and-gold robes embroidered with celestial dragons. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set on the highest throne pavilion of a soaring mountain empire, revealing his three fully restored empress wives "
                "standing regally beside him overlooking tens of thousands of kneeling cultivators under a radiant dawn sky. "
                "Illumination from brilliant auroras of sunrise gold, pristine silver sword qi, and celestial violet mana, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
