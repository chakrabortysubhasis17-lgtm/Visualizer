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
    "novel_slug": "entry-cultivation-i-can-copy-entries",
    "start_url": "https://mtl-novel.com/novel/entry-cultivation-i-can-copy-entries/chapter-251-asking-an-exorbitant-price-bargaining-on-the-spot-eight-turn-golden-core-and-nuwas-astonishment/",
    "start_chapter": 251,
    "end_chapter": 300,
    "default_topic": "Entry Cultivation",

    # Concurrency Throttles
    "batch_size": 10,
    "parallel_chapters": 3,
    "global_max_tts": 3,
    "max_narration_merge": 210,

    # Filepaths & Outputs
    "build_dir": "build_entry_cultivation_251_300",
    "final_audio": "output_entry_cultivation_251_300.mp3",
    "final_video": "final_entry_cultivation_251_300.mp4",
    "cover_image": "cover_entry_cultivation_251_300.jpg",
    "timestamps_file": "youtube_timestamps_entry_cultivation_251_300.txt",
    "subtitles_file": "subtitles_entry_cultivation_251_300.srt",
    "payload_file": "youtube_upload_payload_entry_cultivation_251_300.json",

    # Branding Overlay Assets
    "branding_assets": {
        "logo": "logo.png",
        "subscribe": "subscribe.png",
        "like": "like.png",
        "voice": "voice.png"
    },

    # YouTube Metadata
    "video_title": "EIGHT-TURN GOLDEN CORE & NUWA'S ASTONISHMENT! EXORBITANT PRICE BARGAINING [Ch 251-300] | Xianxia Audiobook Marathon",
    "tags": [
        "Entry Cultivation", "I Can Copy Entries", "Lu Yuan", "Eight-Turn Golden Core",
        "Nuwa Astonishment", "Xianxia Audiobook", "Progression Fantasy", "Full Audiobook Marathon", "Being A Bong"
    ],
    "desc_header": (
        "Mastering the art of exorbitant price bargaining and pill refinement, Lu Yuan unveils the legendary Eight-Turn Golden Core, "
        "leaving even mythical figures like Nuwa in profound astonishment!\n\n"
        "While elite merchant guilds and ancient holy lands attempt to monopolize scarce alchemical ingredients, Lu Yuan effortlessly "
        "turns the market upside down—copying rare supreme entries including [Divine Alchemical Mastery], [Mythic Bargaining Aura], "
        "and [ primordial Creation Insight]. Every traded pill and replicated entry pushes his foundation further beyond mortal limits.\n\n"
        "From out-smarting arrogant continental auctioneers to refining divine elixirs that defy the heavens, watch Lu Yuan "
        "consolidate absolute financial and alchemical supremacy while maintaining his signature low-profile demeanor!\n\n"
        "Welcome to Chapters 251 to 300 of 'Entry Cultivation: I Can Copy Entries' in full multi-voice dramatization!\n\n"
        "🎧 AUDIO MASTER: Broadcast Standard (-14 LUFS, flat dynamic curve, bedtime-ready vocal clarity).\n"
        "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, system alerts, and stats).\n"
        "🎨 VISUAL ENGINE: 10 High-Contrast 4K 3D Visuals + 15s End-Card Outro with official branding.\n\n"
        "══════════════════════════════════════════════\nTIMESTAMPS:\n"
    ),
    "desc_footer": (
        "\n══════════════════════════════════════════════\n\n"
        "🌟 KEY ARC HIGHLIGHTS:\n"
        "• Ch 251: Exorbitant Price Bargaining at the Continental Pill Exchange & The Eight-Turn Golden Core Reveal\n"
        "• Ch 257: Nuwa's Astonishment: Replicating Mythic Creation Entries from Ancient Divine Echoes\n"
        "• Ch 264: Merchant Guild Infiltration: Cornering the Rare Alchemical Herb Market in Secret\n"
        "• Ch 271: Refining Divine Nine-Turn Elixirs: Triggering Heavenly Pill Tribulation Clouds\n"
        "• Ch 278: Eliminating Corrupt Treasure Pavilion Overseers with Silent Spatial Sword Intent\n"
        "• Ch 285: Secret Dao Grotto Exploration: Extracting Lost Primordial Alchemical Formulas\n"
        "• Ch 292: Core Elder Assembly Shock: Displaying Flawless Eight-Turn Core Purity\n"
        "• Ch 300: Alchemical Overlord Hegemony: The Unrivaled Master of Copied Divine Entries\n\n"
        "══════════════════════════════════════════════\n"
        "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
        "All original novel concepts belong to the author. Subscribe for more!\n\n"
        "#EntryCultivation #ICanCopyEntries #XianxiaAudiobook #ProgressionFantasy #CultivationAudiobook #AudiobookMarathon #FullAudiobook #BeingABong"
    ),

    # 10 Story Visual Prompts
    "blocks": [
        {
            "index": 1, "range": (251, 255),
            "title": ["EXORBITANT BARGAINING", "EIGHT-TURN GOLDEN CORE"],
            "fallback_color": (35, 25, 15),
            "prompt": (
                "Cinematic 3D portrait of cultivator Lu Yuan sitting calmly across a carved rosewood trading table, calm confident smirk, "
                "holding a radiant eight-turn golden pill emitting dragon roars, wearing refined dark-blue elder robes. Flawless facial features, crisp detailed skin textures, "
                "medium close-up shot. Set inside an opulent continental merchant guild pavilion, revealing stunned guild masters staring in disbelief at the exorbitant spirit stone price tags in the distance. "
                "Illumination from warm golden lantern light and brilliant pill haloes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 2, "range": (256, 260),
            "title": ["NUWA'S ASTONISHMENT", "CREATION ENTRY COPY"],
            "fallback_color": (30, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan looking upward with quiet awe, observant dark eyes reflecting magnificent golden status matrices, "
                "surrounded by ethereal celestial mist. Flawless facial features, crisp detailed skin textures, medium close-up shot. Set within an ancient mythical shrine grotto, "
                "revealing the divine projection of Goddess Nuwa gazing down in utter astonishment at his unprecedented copied entry traits in the distance. "
                "Illumination from radiant amber divine starlight and shimmering gold entry script, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 3, "range": (261, 265),
            "title": ["MERCHANT MARKET", "CORNERING RARE HERBS"],
            "fallback_color": (25, 30, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan inspecting a rare crimson spirit herb, sharp calculating gaze, neat black hair tied with a dark wood hairpin. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a sprawling subterranean underground apothecary bazaar, "
                "revealing rows of sealed crystal boxes containing monopoly-grade alchemical ingredients in the distance. "
                "Illumination from soft emerald botanical glow and warm hanging brass lanterns, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 4, "range": (266, 270),
            "title": ["PILL TRIBULATION", "NINE-TURN ELIXIR REFINEMENT"],
            "fallback_color": (40, 20, 15),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan directing multi-colored spiritual alchemy flames into a massive bronze cauldron, intense artistic focus, "
                "palms releasing intricate alchemical hand seals. Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a sealed alchemical sanctum, "
                "revealing roaring crimson furnace fires and swirling golden pill cloud tribulation lightning swirling overhead in the distance. "
                "Illumination from bright white pill lightning flashes and fiery furnace glows, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 5, "range": (271, 275),
            "title": ["CORRUPT OVERSEER", "SILENT SPATIAL PURGE"],
            "fallback_color": (25, 15, 30),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan executing a silent sword strike, resolute cold expression, sleeves fluttering under kinetic wind pressure. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set along an ornate pill pavilion balcony under moonlight, "
                "revealing a corrupt pavilion overseer disintegrating into harmless gray spiritual motes without leaving a trace of blood or karma in the distance. "
                "Illumination from pale silver moonlight and razor-thin blade glints, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 6, "range": (276, 280),
            "title": ["SECRET DAO GROTTO", "PRIMORDIAL FORMULA EXTRACTION"],
            "fallback_color": (20, 25, 40),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan touching an ancient weathered stone stele, serene academic focus, fingers tracing glowing archaic runic formulas. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside an unexplored primordial dao grotto, "
                "revealing translucent golden entry characters dissolving from the stone walls straight into his palms in the distance. "
                "Illumination from soft cyan moss and warm golden inscription glow, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 7, "range": (281, 285),
            "title": ["ELDER ASSEMBLY SHOCK", "EIGHT-TURN PURITY REVEAL"],
            "fallback_color": (30, 25, 20),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan standing calmly before a tiered assembly of grand elders, subtle composed smile, "
                "holding a pristine white jade bottle. Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside the grandiose supreme council hall, "
                "revealing powerful continental sect elders gasping in sheer shock as the eight-turn pill purity is displayed in the distance. "
                "Illumination from warm morning sunbeams through high latticework and glowing jade tables, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 8, "range": (286, 290),
            "title": ["PRIVATE SPIRIT DOMAIN", "EXPANDING THE SANCTUARY"],
            "fallback_color": (25, 20, 45),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan expanding a private dimensional domain, commanding authoritative stance, extended palm revealing shimmering spatial cracks. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set inside a concealed dimensional fold filled with floating crystal islands and spiritual herb gardens, "
                "revealing ethereal ward barriers protecting the sanctuary from outside detection in the distance. "
                "Illumination from radiant violet spatial currents and soft cyan starlight, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 9, "range": (291, 295),
            "title": ["SUPREME ALCHEMICAL CLASH", "DEFEATING RIVAL MASTERS"],
            "fallback_color": (35, 15, 35),
            "prompt": (
                "Cinematic 3D portrait of Lu Yuan commanding dual alchemy flames with effortless ease, cool amused smirk, piercing dark eyes. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set in the center of the continental pill competition square, "
                "revealing arrogant rival grandmaster alchemists collapsing in utter defeat as their cauldrons crack under pressure in the distance. "
                "Illumination from vibrant violet magical flames and brilliant gold pill haloes, deep depth of field with high contrast details throughout."
            )
        },
        {
            "index": 10, "range": (296, 300),
            "title": ["ALCHEMICAL OVERLORD", "PEAK ENTRY HEGEMONY"],
            "fallback_color": (20, 20, 50),
            "prompt": (
                "Cinematic 3D portrait of Alchemical Overlord Lu Yuan standing at the pinnacle of continental mountain peaks at sunset, "
                "serene invincible presence, irises glowing with nine-colored creation matrices, wearing refined dark-blue elder robes billowing gracefully in the wind. "
                "Flawless facial features, crisp detailed skin textures, medium close-up shot. Set overlooking an endless sea of clouds dotted with soaring cranes and distant floating immortal sanctuaries in the distance. "
                "Illumination from rich golden sunset rays, vibrant twilight nebulae, and shimmering golden entry runes, deep depth of field with high contrast details throughout."
            )
        }
    ]
}

if __name__ == "__main__":
    asyncio.run(run_audiobook_pipeline(CONFIG))
