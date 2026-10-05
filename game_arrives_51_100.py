import os
import re
import sys
import json
import time
import random
import shutil
import asyncio
import subprocess
import urllib.parse
import requests
from bs4 import BeautifulSoup
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from pydantic import BaseModel, Field

# Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

from entity_manager import EntityManager

# ==================== ARCHITECTURAL & API CONFIG ====================
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
    "AQ.Ab8RN6IAz25x6_DTjjrmdSenfUJJJq-oFLMndRdjtl_BNuPo-A"
)

START_CHAPTER = 51
END_CHAPTER = 100
BATCH_SIZE = 5
PARALLEL_CHAPTERS = 2
GLOBAL_MAX_CONCURRENT_TTS = 3
MAX_NARRATION_MERGE_WORDS = 210
TARGET_DIALOGUE_CHUNK_WORDS = 65

CINZEL_URL = "https://github.com/google/fonts/raw/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
CINZEL_LOCAL_PATH = "CinzelDecorative-Bold.ttf"

REQUEST_TIMEOUT = 25

NOVEL_SLUG = "game-arrives-i-can-evolve-my-talents-infinitely"
START_URL = "https://mtl-novel.com/novel/game-arrives-i-can-evolve-my-talents-infinitely/chapter-51-feast/"
BUILD_DIR = "build_game_arrives_51_100"
FINAL_AUDIO = "output_game_arrives_51_100.mp3"
FINAL_VIDEO = "final_game_arrives_51_100.mp4"
COVER_IMAGE = "cover_game_arrives_51_100.jpg"
TIMESTAMPS_FILE = "youtube_timestamps_game_arrives_51_100.txt"
SUBTITLES_FILE = "subtitles_game_arrives_51_100.srt"
PAYLOAD_FILE = "youtube_upload_payload_game_arrives_51_100.json"

VIDEO_TITLE = "GAME ARRIVES: I Awoke An F-Rank Trash Skill That Evolves Infinitely! [Ch 51-100] | LitRPG Audiobook"
TAGS = [
    "LitRPG Audiobook", "Progression Fantasy", "Game Arrives I Can Evolve My Talents Infinitely",
    "Zhou Han", "Xia Ming", "Infinite Evolution", "System Apocalypse", "Solo Leveling",
    "Full Audiobook", "Audiobook Marathon", "Being A Bong"
]

DESC_HEADER = (
    "Following his legendary solo kill of the Abyssal Dragon and awakening the S-Rank hidden class 'Lord of the Stars', "
    "the protagonist shatters all expectations of the base commanders!\n\n"
    "Granted entry into the human race's top-secret 'Spark Project', his supposedly useless F-rank talents continue to mutate. "
    "While rival factions, blood-cult infiltrators, and foreign guild champions conspire in the shadows, his basic spells evolve "
    "into cosmic true-damage cataclysms with infinite attack speed and instant battlefield teleportation!\n\n"
    "Welcome to Chapters 51 to 100 of 'Game Arrives: I Can Evolve My Talents Infinitely' "
    "(网游降临：我的天赋能无限进化) in unabridged multi-voice dramatization!\n\n"
    "🎧 AUDIO MASTER: Mobile-Optimized Broadcast Standard (-14 LUFS, Punchy Dynamic Dialogue).\n"
    "📖 CLOSED CAPTIONS: Soft Subtitles (CC Enabled for dialogue, skill sheets, and server announcements).\n"
    "🎨 VISUAL ENGINE: 10 High-Contrast 4K Manhwa Visuals + 15s End-Card Outro.\n\n"
    "══════════════════════════════════════════════\nTIMESTAMPS:\n"
)

DESC_FOOTER = (
    "\n══════════════════════════════════════════════\n\n"
    "🌟 KEY ARC HIGHLIGHTS:\n"
    "• 00:00:00 - Chapter 51: The Victory Feast & Star Embryo Hatching\n"
    "• Chapter 58: Inducted into the Human Race Spark Project\n"
    "• Chapter 64: Annihilating Blood God Cult Infiltrators\n"
    "• Chapter 73: Second Job Advancement: Stellar Astral Sovereign\n"
    "• Chapter 80: Inter-Server Arena: Face-Slapping Foreign Guild Masters\n"
    "• Chapter 88: Forging the SSS-Tier Divine Cosmic Core\n"
    "• Chapter 100: World First Blood! Tier-3 Godhood Domain Unleashed\n\n"
    "══════════════════════════════════════════════\n"
    "DISCLAIMER:\nThis audiobook is an edited dramatized adaptation produced for entertainment and literature commentary. "
    "All original novel concepts belong to the author. Subscribe for more!\n\n"
    "#LitRPG #ProgressionFantasy #ZhouHan #InfiniteEvolution #FullAudiobook #AudiobookMarathon #SystemApocalypse"
)

GRADIENT_PALETTES = [
    ((255, 235, 120), (255, 120, 40)),
    ((160, 230, 255), (60, 140, 255)),
    ((220, 160, 255), (140, 60, 240)),
]

# ==================== GEMINI HIGH-TEXTURE DEDUCTION SCHEMA ====================
class CharacterProfile(BaseModel):
    name: str = Field(description="Character name or clear narrative role")
    role_or_identity: str = Field(description="Narrative identity: e.g. Solo Leveler Zhou Han / Xia Ming, Captain Xiang Yinsha, Commander Li, Ice Mage Han Xue")
    visual_attire: str = Field(description="Specific attire materials: leather tunic, steel armor with gold runes, silk cheongsam, lace, heavy cloaks")

class BlockClimaxScene(BaseModel):
    deduced_environment: str = Field(description="Specific fantasy/sci-fi location matching the chapters (e.g. ruined city with blue crystals, cosmic starfall altar, grand baroque command hall)")
    characters_present: list[CharacterProfile] = Field(description="Profiles of characters participating in this climax beat")
    camera_framing: str = Field(description="Strict camera angle: 'low angle shot', 'dramatic dutch angle', 'wide action shot', 'over-the-shoulder shot', or 'medium action shot'")
    lighting_and_atmosphere: str = Field(description="Color palette: e.g. sapphire cyan frost and starlight gold, fiery amber dusk, crimson velvet")
    climax_action: str = Field(description="Core dramatic moment occurring in the scene")
    image_prompt: str = Field(
        description=(
            "Ultra-sharp, hyper-detailed 2D anime manhwa prompt (under 140 chars). "
            "Format: [camera framing], [characters with fabric/armor textures], [action], [setting with lighting], sharp ink contours, 8k webtoon masterpiece. "
            "DO NOT use 'cel shaded' or 'flat colors'. Strictly no quotes, brackets, or violent trigger words. Only letters, numbers, commas, and spaces."
        )
    )

class MasterCoverDeduction(BaseModel):
    hero_composition: str = Field(description="Hero commanding pose, golden aura, divine sword, and glowing pupils")
    heroine_companion: str = Field(description="Heroine companion standing beside him with celestial magic frost")
    background_power_elements: str = Field(description="Grand magic arrays, celestial glowing summon circles, or cosmic dimensional rift")
    color_contrast: str = Field(description="Vibrant contrast: incandescent solar gold and starlight vs deep sapphire mana blue")
    image_prompt: str = Field(
        description=(
            "High-impact 2D anime manhwa master thumbnail prompt (under 135 chars). "
            "Must feature hero front and center with glowing golden blade, heroine companion beside him, "
            "intricate glowing magic summon circles in backdrop. Letters, numbers, commas, spaces only."
        )
    )

BLOCKS = [
    {
        "index": 1, "range": (51, 55),
        "title": ["VICTORY FEAST", "STAR EMBRYO HATCHING", "Chapters 51 – 55"],
        "fallback_color": (25, 20, 35),
        "prompt": "medium shot, hero in dark leather coat inspecting glowing pulsing cosmic star embryo in luxury base banquet hall with azure neon holographic UI"
    },
    {
        "index": 2, "range": (56, 60),
        "title": ["PIONEER CORPS ASCENSION", "SPARK PROJECT UNLOCKED", "Chapters 56 – 60"],
        "fallback_color": (30, 40, 25),
        "prompt": "low angle shot, commander Li Yueming awarding gold star sovereign insignia to protagonist amidst saluting military officers, cybernetic base hall"
    },
    {
        "index": 3, "range": (61, 65),
        "title": ["ABYSSAL RIFT RECON", "VOID STALKER HUNT", "Chapters 61 – 65"],
        "fallback_color": (15, 30, 50),
        "prompt": "dynamic mid-air shot, hero slashing dual radiant golden flame arcs through shadowy void stalkers in crystalline ruined alien canyon"
    },
    {
        "index": 4, "range": (66, 70),
        "title": ["BLOOD GOD PURGE", "SECT ENCLAVE CRUSHED", "Chapters 66 – 70"],
        "fallback_color": (45, 20, 25),
        "prompt": "dramatic Dutch angle, hero unleashing swirling celestial starstorm eradicating red-robed blood god cult elders in underground cathedral"
    },
    {
        "index": 5, "range": (71, 75),
        "title": ["SECOND JOB ADVANCEMENT", "STELLAR ASTRAL SOVEREIGN", "Chapters 71 – 75"],
        "fallback_color": (35, 30, 45),
        "prompt": "mystical cosmic shot, protagonist levitating as brilliant galaxy constellations and golden stat glyphs lock onto his celestial armor plates"
    },
    {
        "index": 6, "range": (76, 80),
        "title": ["INTER-SERVER SHOWDOWN", "FOREIGN GUILD FACE-SLAP", "Chapters 76 – 80"],
        "fallback_color": (50, 25, 15),
        "prompt": "wide action shot, calm protagonist parrying giant frost hammer from foreign guild champion with one finger, glowing barrier sparks"
    },
    {
        "index": 7, "range": (81, 85),
        "title": ["COSMIC TITAN FORGE", "SSS-TIER DIVINE WEAPON", "Chapters 81 – 85"],
        "fallback_color": (20, 35, 30),
        "prompt": "high contrast forge shot, hero plunging glowing solar blade into celestial titan core, radiating blinding gold lightning arcs"
    },
    {
        "index": 8, "range": (86, 90),
        "title": ["STARFALL EXTINCTION", "BEAST TIDE ANNIHILATION", "Chapters 86 – 90"],
        "fallback_color": (45, 35, 15),
        "prompt": "panoramic wide shot, protagonist atop obsidian fortress wall commanding thousands of orbital starlight beams raining into endless demon hordes"
    },
    {
        "index": 9, "range": (91, 95),
        "title": ["WARLORD CONFRONTATION", "CAPTAIN XIANG RESCUED", "Chapters 91 – 95"],
        "fallback_color": (25, 30, 45),
        "prompt": "medium action shot, hero projecting hexagonal solar aegis shielding injured female captain Xiang Yinsha from descending colossal dragon claw"
    },
    {
        "index": 10, "range": (96, 100),
        "title": ["WORLD FIRST ASCENSION", "TIER-3 GODHOOD DOMAIN", "Chapters 96 – 100"],
        "fallback_color": (35, 20, 45),
        "prompt": "epic cosmic wide shot, sovereign hero in divine starlight robes standing above planet Earth, golden server announcement banners illuminating sky"
    }
]

BASE_CHARACTERS = {
    "narrator": {"display_name": "Narrator", "gender": "Female", "line_type": "Narration", "voice": "en-US-JennyNeural", "pitch": "+1Hz", "rate": "+4%"},
    "mc": {"display_name": "Zhou Han", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-GuyNeural", "pitch": "+0Hz", "rate": "+6%"},
    "game_system": {"display_name": "Game System", "gender": "Synthetic", "line_type": "System", "voice": "en-US-SteffanNeural", "pitch": "-18Hz", "rate": "-6%"},
    "xiang_yinsha": {"display_name": "Xiang Yinsha", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-AriaNeural", "pitch": "+1Hz", "rate": "+5%"},
    "li_yueming": {"display_name": "Commander Li", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-RogerNeural", "pitch": "-6Hz", "rate": "+2%"},
    "jiang_ning": {"display_name": "Jiang Ning", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-EmmaNeural", "pitch": "+3Hz", "rate": "+6%"},
    "leina": {"display_name": "Lena", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-JennyNeural", "pitch": "+1Hz", "rate": "+4%"},
    "han_xue": {"display_name": "Han Xue", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-JennyNeural", "pitch": "+2Hz", "rate": "+6%"},
    "sister_ya": {"display_name": "Sister Ya", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-AriaNeural", "pitch": "+1Hz", "rate": "+5%"},
    "ou_shengnan": {"display_name": "Captain Ou", "gender": "Female", "line_type": "Dialogue", "voice": "en-US-EmmaNeural", "pitch": "-1Hz", "rate": "+5%"},
    "fatty_wang": {"display_name": "Fatty Wang", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-ChristopherNeural", "pitch": "+2Hz", "rate": "+6%"},
    "young_master_zhang": {"display_name": "Young Master Zhang", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-EricNeural", "pitch": "+6Hz", "rate": "+10%"},
    "guild_leader": {"display_name": "Guild Leader", "gender": "Male", "line_type": "Dialogue", "voice": "en-US-RogerNeural", "pitch": "-6Hz", "rate": "+2%"},
    "dungeon_boss": {"display_name": "Dungeon Boss", "gender": "Synthetic", "line_type": "Dialogue", "voice": "en-US-SteffanNeural", "pitch": "-15Hz", "rate": "+4%"}
}

RE_SYSTEM = re.compile(r"(?:\[|【|〔|『|〖|［)(Ding!|System|Notice|Warning|Announcement|World Announcement|Server Notice|Prompt|Talent Evolution).*?(?:\]|】|〕|』|〗|］)", re.I)
RE_SCENE_DIVIDER = re.compile(r"^(\s*[*~=_#-]\s*){3,}$", re.MULTILINE)
WATERMARK_PATTERNS = [
    re.compile(r"\(End of this chapter\)", re.I),
    re.compile(r"Please visit mtl-novel\.com.*", re.I),
    re.compile(r"Check out our latest novel.*", re.I),
    re.compile(r"\[TL Note:.*?\]", re.I),
    re.compile(r"https?://\S+", re.I),
    re.compile(r"【?\s*Brain Storage\s*】?", re.I),
    re.compile(r"【?\s*Please come in, dear readers\.?\s*】?", re.I)
]
FULLWIDTH_TO_ASCII = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '「': '"', '」': '"',
    '，': ', ', '。': '. ', '！': '! ', '？': '? ',
    '：': ': ', '；': '; ', '（': '(', '）': ')'
})
RE_ALPHANUM = re.compile(r'[a-zA-Z0-9]')
RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


# ==================== COOLDOWN & TIMER HELPER ====================
def execute_cooldown_timer(wait_seconds: int, reason: str = "Backoff pause"):
    for remaining in range(wait_seconds, 0, -1):
        print(f"\r     [{reason}] Retrying in {remaining:2d}s...", end="", flush=True)
        time.sleep(1)
    print(f"\r     [{reason}] {wait_seconds}s pause elapsed. Firing request...             ", flush=True)


# ==================== GEMINI INTELLIGENT SCENE DEDUCTION ====================
def deduce_block_scene_via_gemini(client, block_idx: int, ch_start: int, ch_end: int, chapter_titles: list, excerpt: str) -> str:
    if not client or not GENAI_AVAILABLE:
        return BLOCKS[block_idx - 1]["prompt"]

    print(f"\n     [Gemini Director] Deducing visual scene for Block {block_idx} (Ch {ch_start}–{ch_end})...", flush=True)

    system_instruction = """
You are the creative director and storyboard lead for an elite 2D manhwa webtoon adaptation studio.
Your mandate is to deduce a visually stunning, highly textured climax scene panel for this 5-chapter batch of a LitRPG progression novel.

CRITICAL DIRECTIVES FOR HIGH TEXTURE & RAZOR SHARPNESS:
1. LORE & CHARACTER INTEGRATION:
   - Identify core power systems, character roles, and situation from the text (Protagonist Zhou Han / Xia Ming with Infinite Evolution and Lord of the Stars, Captain Xiang Yinsha, Commander Li Yueming, Han Xue, Blood God Cultists).
   - Character identities must match their specific role and attire (e.g. Zhou Han in dark leather/steel armor with golden circuit runes, Xiang Yinsha in thunder robes, Commander Li in high-ranking officer cape).
   - NEVER render generic modern school uniforms or blank backgrounds.
2. STRICT VISUAL DIVERSITY:
   - Use dynamic, non-repetitive camera angles: low-angle looking up, dramatic Dutch angle for clashes, wide panoramic shot for armies/blade storms, or over-the-shoulder action.
3. HIGH TEXTURE PROMPT SPECIFICATIONS:
   - Format: "[camera framing], [characters with fabric/armor textures], [action], [setting with lighting], sharp ink contours, highly detailed, 8k webtoon masterpiece"
   - Keep the image_prompt strictly UNDER 140 characters.
   - AVOID words like 'cel shaded' or 'flat colors'.
   - ONLY letters, numbers, commas, and spaces. No quotes or brackets.
"""

    prompt_content = (
        f"PROTAGONIST: Zhou Han (Xia Ming - Lord of the Stars with Infinite Talent Evolution)\n"
        f"NOVEL: Game Arrives: I Can Evolve My Talents Infinitely\n"
        f"BATCH: Block {block_idx} (Chapters {ch_start} to {ch_end})\n"
        f"CHAPTER TITLES: {', '.join(chapter_titles)}\n\n"
        f"STORY EXCERPT & BATTLE SCENES:\n{excerpt[:2000]}\n\n"
        f"Deduce the specific environment, active characters, their attire, and the climax manhwa scene prompt."
    )

    model_candidates = [
        "gemini-flash-lite-latest",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]

    for model_name in model_candidates:
        try:
            print(f"     [Gemini] Submitting context to '{model_name}'...", flush=True)
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=BlockClimaxScene,
                    temperature=0.2
                )
            )
            if resp and resp.text:
                parsed = json.loads(resp.text)
                raw_p = parsed.get("image_prompt", "")
                clean_p = re.sub(r'[^a-zA-Z0-9\s,]', '', raw_p).strip()
                if len(clean_p) > 130:
                    clean_p = clean_p[:130].rsplit(' ', 1)[0]

                print(f"     [Gemini Director] Deduced Setting: {parsed.get('deduced_environment')}")
                print(f"     [Gemini Director] Framing: {parsed.get('camera_framing')} | Action: {parsed.get('climax_action')}")
                for ch in parsed.get("characters_present", []):
                    print(f"        • {ch.get('name')} ({ch.get('role_or_identity')}): {ch.get('visual_attire')}")
                print(f"     [Gemini Prompt]: \"{clean_p}\"", flush=True)
                if len(clean_p) > 20:
                    return clean_p
        except Exception as e:
            print(f"     [Gemini Note] Model '{model_name}' fallback: {e}. Trying next model...", flush=True)
            time.sleep(1)

    return BLOCKS[block_idx - 1]["prompt"]


def deduce_master_cover_via_gemini(client, novel_slug: str, char_map: dict) -> str:
    fallback_prompt = (
        "anime manhwa cover art, hero Zhou Han front center glowing golden aura holding celestial sword, "
        "beside ice mage Han Xue, glowing magic summon circles, 8k uhd"
    )
    if not client or not GENAI_AVAILABLE:
        return fallback_prompt

    print(f"\n[{novel_slug}] [Gemini Director] Designing Multi-Character Master Thumbnail...", flush=True)

    system_instruction = """
You are the lead thumbnail artist and creative director for top-performing YouTube progression fantasy and LitRPG audiobooks.
Your task is to design an ultra-high CTR, epic, colorful master cover artwork featuring the main hero front-and-center, accompanied by his companion.

VISUAL INSPIRATION & GUIDELINES:
1. HERO DOMINANCE:
   - The male protagonist (Zhou Han / Xia Ming) must be front and center, commanding and powerful.
   - Radiant golden armor, celestial star crown, and a blade radiating incandescent golden lightning and star power.
2. HEROINE COMPANION:
   - Beside or slightly behind him stands the beautiful female lead with crystalline frost and mana starlight.
3. BACKGROUND MAGIC & PARTICLES:
   - Behind them are massive glowing cosmic magic circles, glowing status glyphs, intricate summoning arrays, and radiant mana motes.
4. CONTRAST & SATURATION:
   - High color contrast: radiant warm gold and amber lightning clashing with deep sapphire ice blue and cosmic violet.
5. PROMPT FORMAT:
   - Under 135 characters, strictly letters, numbers, commas, and spaces. No quotes or brackets.
"""

    prompt_content = (
        f"NOVEL: Game Arrives: I Can Evolve My Talents Infinitely\n"
        f"MAIN CHARACTER: Zhou Han (Xia Ming - Lord of the Stars, SSS-Tier Infinite Evolution)\n"
        f"COMPANION: Xiang Yinsha / Han Xue\n"
        f"THEME: System Apocalypse, Cosmic MMORPG Arrival, Divine Class Ascension, High-CTR Manhwa Cover\n\n"
        f"Synthesize the master thumbnail prompt."
    )

    model_candidates = [
        "gemini-flash-lite-latest",
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash"
    ]

    for model_name in model_candidates:
        try:
            print(f"     [Gemini Cover] Requesting thumbnail composition from '{model_name}'...", flush=True)
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=MasterCoverDeduction,
                    temperature=0.3
                )
            )
            if resp and resp.text:
                parsed = json.loads(resp.text)
                raw_p = parsed.get("image_prompt", "")
                clean_p = re.sub(r'[^a-zA-Z0-9\s,]', '', raw_p).strip()
                if len(clean_p) > 130:
                    clean_p = clean_p[:130].rsplit(' ', 1)[0]

                print(f"     [Gemini Cover] Hero Focus: {parsed.get('hero_composition')}")
                print(f"     [Gemini Cover] Companion: {parsed.get('heroine_companion')}")
                print(f"     [Gemini Cover] Palette: {parsed.get('color_contrast')}")
                print(f"     [Gemini Master Prompt]: \"{clean_p}\"", flush=True)
                if len(clean_p) > 20:
                    return clean_p
        except Exception as e:
            print(f"     [Gemini Cover Note] Model '{model_name}' fallback: {e}. Trying next model...", flush=True)
            time.sleep(1)

    return fallback_prompt


# ==================== TEXT PROCESSING & REGISTRY ====================
def load_characters_and_vocatives(slug: str, base_defaults: dict) -> tuple:
    char_map = dict(base_defaults)
    voc_map = {}
    candidate_files = ["novel_entities_registry.json", "novel_entities_registry_4.json", "novel_entities_registry_3.json"]
    reg_file = next((f for f in candidate_files if os.path.exists(f)), None)

    if reg_file:
        try:
            with open(reg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if slug in data:
                reg_chars = data[slug].get("characters", {})
                voc_map = data[slug].get("vocatives", {})
                print(f"[{slug}] Linked {reg_file}: {len(reg_chars)} characters, {len(voc_map)} vocatives indexed.", flush=True)
                for name, cinfo in reg_chars.items():
                    entry = {
                        "display_name": name.title(),
                        "gender": cinfo.get("gender", "Male"),
                        "line_type": "Dialogue" if cinfo.get("role") != "system" else "System",
                        "voice": cinfo.get("voice", "en-US-GuyNeural"),
                        "pitch": cinfo.get("pitch", "+0Hz"),
                        "rate": cinfo.get("rate", "+6%"),
                        "aliases": cinfo.get("aliases", [])
                    }
                    char_map[name.lower()] = entry
                    char_map[cinfo.get("role", name)] = entry
                    for alias in entry["aliases"]:
                        char_map[alias.lower()] = entry
        except Exception as e:
            print(f"[{slug}] Warning: Registry sync failed: {e}", flush=True)
    return char_map, voc_map


def clean_and_normalize_text(text: str) -> str:
    cleaned = text.translate(FULLWIDTH_TO_ASCII)
    cleaned = RE_SCENE_DIVIDER.sub("", cleaned)
    for pat in WATERMARK_PATTERNS:
        cleaned = pat.sub("", cleaned)
    cleaned = re.sub(r'~+', '', cleaned)
    cleaned = re.sub(r'\*{2,}', '', cleaned)
    cleaned = re.sub(r'\.{4,}', '...', cleaned)
    return re.sub(r"[ \t]+", " ", cleaned).strip()


def balance_paragraph_quotes(paragraph: str) -> str:
    if paragraph.count('"') % 2 != 0:
        if re.search(r'\b(said|replied|whispered|murmured|asked|smiled|sneered)\b', paragraph, re.I):
            paragraph = paragraph + '"'
        else:
            paragraph = '"' + paragraph
    return paragraph


def scrape_chapter_content(session: requests.Session, url: str, ch_num: int):
    print(f"[{NOVEL_SLUG}] Connecting to Ch.{ch_num:03d}: {url}", flush=True)
    resp = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else f"Chapter {ch_num}"

    container = soup.find("article") or \
                soup.find("div", class_=re.compile(r"(chapter-content|entry-content|epcontent|post-content|reading-content)", re.I)) or \
                soup.find("div", id=re.compile(r"(chapter-content|content|article)", re.I)) or \
                soup.find("body")

    paragraphs = [clean_and_normalize_text(p.get_text(strip=True)) for p in container.find_all("p")]
    paragraphs = [p for p in paragraphs if p and RE_ALPHANUM.search(p)]

    if not paragraphs:
        paragraphs = [f"Chapter {ch_num}. The cosmic system deepens and evolution proceeds."]

    full_text = f"{title}.\n\n" + "\n\n".join(paragraphs)

    next_url = None
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        rel = a.get("rel", "")
        if isinstance(rel, list): rel = " ".join(rel)
        t = a.get_text(strip=True).lower()
        if ("next" in rel.lower() or "next" in t or "»" in t or "next chapter" in t) and href not in ["#", ""]:
            full_next = urllib.parse.urljoin(url, href)
            if full_next != url:
                next_url = full_next
                break

    if not next_url:
        target_pattern = re.compile(rf"/chapter-{ch_num + 1}(?:[/-]|$)", re.I)
        for a in soup.find_all("a", href=True):
            if target_pattern.search(a["href"]):
                next_url = urllib.parse.urljoin(url, a["href"])
                break

    if not next_url:
        pattern_curr = re.compile(rf"(chapter-){ch_num}([/-])", re.I)
        if pattern_curr.search(url):
            next_url = pattern_curr.sub(rf"\g<1>{ch_num + 1}\g<2>", url)

    return title, full_text, next_url


def classify_game_arrives_dialogue(chunk: str, prev_narr: str, next_narr: str) -> str:
    chunk_lower = chunk.lower()
    prev_lower = prev_narr.lower()
    next_lower = next_narr.lower()

    if any(k in chunk_lower or k in prev_lower for k in [
        "ding!", "system prompt", "world announcement", "server notice",
        "evolution completed", "talent upgraded", "congratulations player",
        "100% true damage", "first blood", "attribute points allocated"
    ]):
        return "game_system"

    if re.search(r"\b(xiang\s+yinsha|yin\s+sha|yinsha)\s+(?:said|replied|asked|whispered|blushed|sighed)\b", prev_lower):
        return "xiang_yinsha"
    if re.search(r"\b(li\s+yueming|commander\s+li)\s+(?:said|ordered|asked|commanded)\b", prev_lower):
        return "li_yueming"
    if re.search(r"\b(jiang\s+ning|ning'er)\s+(?:said|cheered|laughed|asked)\b", prev_lower):
        return "jiang_ning"
    if re.search(r"\b(leina|lena|reina)\s+(?:said|whispered|murmured)\b", prev_lower):
        return "leina"
    if re.search(r"\b(han\s+xue|xue'er|miss\s+han|ice\s+mage)\s+(?:said|replied|asked|whispered)\b", prev_lower):
        return "han_xue"
    if re.search(r"\b(sister\s+ya|ya\s+fei|madam\s+ya|auctioneer)\s+(?:smiled|chuckled|gasped)\b", prev_lower):
        return "sister_ya"
    if re.search(r"\b(ou\s+shengnan|captain\s+ou|female\s+captain)\s+(?:ordered|barked|saluted)\b", prev_lower):
        return "ou_shengnan"

    if re.search(r"\b(?:said|whispered|asked)\s+(xiang\s+yinsha|yinsha|jiang\s+ning|leina)\b", next_lower):
        for f_name, role_k in [("yinsha", "xiang_yinsha"), ("jiang", "jiang_ning"), ("leina", "leina")]:
            if f_name in next_lower:
                return role_k

    if re.search(r"\b(fatty|fatty\s+wang|wang\s+bao)\s+(?:shouted|cried|laughed|screamed)\b", prev_lower):
        return "fatty_wang"
    if re.search(r"\b(young\s+master|zhang\s+tiancheng|arrogant\s+player|scion)\s+(?:sneered|mocked|roared|cursed)\b", prev_lower):
        return "young_master_zhang"
    if re.search(r"\b(guild\s+leader|commander|iron\s+blood)\s+(?:ordered|demanded)\b", prev_lower):
        return "guild_leader"
    if re.search(r"\b(dungeon\s+boss|beast\s+king|abyssal\s+lord|boss)\s+(?:roared|growled|bellowed)\b", prev_lower):
        return "dungeon_boss"

    if re.search(r"\b(brother\s+han|xia\s+ming|big\s+brother\s+han)\b", chunk_lower):
        return "xiang_yinsha"
    if re.search(r"\b(boss\s+zhou|god\s+zhou)\b", chunk_lower):
        return "fatty_wang"
    if re.search(r"\b(sister\s+ya)\b", chunk_lower):
        return "mc"
    if re.search(r"\b(courting\s+death|you\s+dare|know\s+who\s+my\s+father\s+is)\b", chunk_lower):
        return "young_master_zhang"

    if re.search(r"\b(zhou\s+han\s+smiled|xia\s+ming\s+smiled|he\s+said|he\s+thought)\b", next_lower):
        return "mc"

    return "mc"


def parse_chapter_to_staged_json(text: str, entity_mgr: EntityManager, char_map: dict, voc_map: dict) -> list:
    paragraphs = text.split("\n\n")
    raw_tokens = []

    for p in paragraphs:
        p_clean = balance_paragraph_quotes(p.strip())
        if not p_clean or not RE_ALPHANUM.search(p_clean):
            continue
        parts = p_clean.split('"')
        for i, raw_chunk in enumerate(parts):
            chunk = raw_chunk.strip()
            if not chunk or not RE_ALPHANUM.search(chunk):
                continue
            if i % 2 == 0:
                raw_tokens.append({"is_quote": False, "text": chunk})
            else:
                raw_tokens.append({"is_quote": True, "text": chunk})

    staged_segments = []
    for idx, token in enumerate(raw_tokens):
        if not token["is_quote"]:
            line_type = "System" if RE_SYSTEM.search(token["text"]) else "Narration"
            role_key = "game_system" if line_type == "System" else "narrator"
            staged_segments.append({"role_key": role_key, "line_type": line_type, "text": token["text"]})
        else:
            prev_narr = ""
            for back_idx in range(idx - 1, -1, -1):
                if not raw_tokens[back_idx]["is_quote"]:
                    prev_narr = raw_tokens[back_idx]["text"][-85:]
                    break

            next_narr = ""
            for fwd_idx in range(idx + 1, len(raw_tokens)):
                if not raw_tokens[fwd_idx]["is_quote"]:
                    next_narr = raw_tokens[fwd_idx]["text"][:85]
                    break

            role_key = classify_game_arrives_dialogue(token["text"], prev_narr, next_narr)
            line_t = "System" if role_key == "game_system" else ("Narration" if role_key == "narrator" else "Dialogue")
            staged_segments.append({"role_key": role_key, "line_type": line_t, "text": token["text"]})

    consolidated = []
    for seg in staged_segments:
        if consolidated and consolidated[-1]["role_key"] == "narrator" and seg["role_key"] == "narrator":
            if len(consolidated[-1]["text"].split()) + len(seg["text"].split()) <= MAX_NARRATION_MERGE_WORDS:
                consolidated[-1]["text"] += " " + seg["text"]
                continue
        consolidated.append(seg)

    staged_records = []
    line_seq = 1
    for seg in consolidated:
        rk = seg["role_key"]
        role_meta = char_map.get(rk, char_map.get(rk.replace(" ", "_"), char_map.get("mc", char_map["narrator"])))
        words = seg["text"].split()
        sub_chunks = []
        chunk_ceiling = MAX_NARRATION_MERGE_WORDS if seg["line_type"] == "Narration" else TARGET_DIALOGUE_CHUNK_WORDS
        if len(words) <= chunk_ceiling:
            sub_chunks.append(seg["text"])
        else:
            sentences = RE_SENTENCE_SPLIT.split(seg["text"])
            curr_words = []
            for s in sentences:
                s_words = s.split()
                if len(curr_words) + len(s_words) > chunk_ceiling and curr_words:
                    sub_chunks.append(" ".join(curr_words))
                    curr_words = s_words
                else:
                    curr_words.extend(s_words)
            if curr_words:
                sub_chunks.append(" ".join(curr_words))

        for text_piece in sub_chunks:
            tp = text_piece.strip()
            if not re.search(r'[.!?…]$', tp):
                tp = tp + "."
            staged_records.append({
                "line_id": f"{line_seq:04d}",
                "speaker": role_meta["display_name"],
                "gender": role_meta["gender"],
                "line_type": seg["line_type"],
                "text": tp,
                "voice": role_meta["voice"],
                "pitch": role_meta["pitch"],
                "rate": role_meta["rate"]
            })
            line_seq += 1

    return staged_records


# ==================== ADVANCED VISUAL ENGINE (1080P LANDSCAPE) ====================
def ensure_cinzel_font() -> str:
    if os.path.exists(CINZEL_LOCAL_PATH) and os.path.getsize(CINZEL_LOCAL_PATH) > 10000:
        return CINZEL_LOCAL_PATH
    try:
        resp = requests.get(CINZEL_URL, timeout=12)
        if resp.status_code == 200 and len(resp.content) > 10000:
            with open(CINZEL_LOCAL_PATH, "wb") as f:
                f.write(resp.content)
            return CINZEL_LOCAL_PATH
    except Exception:
        pass
    for fp in ["C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/timesbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]:
        if os.path.exists(fp):
            return fp
    return "arialbd.ttf"


def fit_crop_and_sharpen_1080p(img: Image.Image) -> Image.Image:
    target_w, target_h = 1920, 1080
    target_ratio = target_w / target_h
    img_w, img_h = img.size
    img_ratio = img_w / img_h

    if img_ratio > target_ratio:
        new_w = int(img_h * target_ratio)
        left = (img_w - new_w) // 2
        img = img.crop((left, 0, left + new_w, img_h))
    else:
        new_h = int(img_w / target_ratio)
        top = (img_h - new_h) // 2
        img = img.crop((0, top, img_w, top + new_h))

    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    img = img.filter(ImageFilter.DETAIL)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=160, threshold=0))
    img = img.filter(ImageFilter.UnsharpMask(radius=2.8, percent=110, threshold=1))
    img = ImageEnhance.Sharpness(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    img = ImageEnhance.Color(img).enhance(1.10)
    return img


def fetch_comic_artwork_landscape(prompt: str, out_path: str, block_index: int) -> bool:
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return True

    clean_p = re.sub(r'[^a-zA-Z0-9\s,]', '', prompt).strip()
    if len(clean_p) > 130:
        clean_p = clean_p[:130].rsplit(' ', 1)[0]

    full_prompt = (
        f"{clean_p}, sharp detailed anime eyes, clear pupil, "
        f"intricate outfit texture, crisp ink linework, "
        f"subsurface lighting, masterpiece 2D anime manhwa, 8k uhd"
    )
    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(10000, 9999999)

    clusters = [
        (f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=576&seed={seed}&nologo=true", "Free 1024p Cluster", 0 if block_index == 1 else 15),
        (f"https://image.pollinations.ai/prompt/{encoded}?width=896&height=512&seed={seed+1}&nologo=true", "Free 512p Cluster", 10),
        (f"https://image.pollinations.ai/prompt/{encoded}?width=960&height=540&seed={seed+2}&nologo=true", "Free 540p Cluster", 10)
    ]

    for attempt, (url, label, delay_sec) in enumerate(clusters, 1):
        if delay_sec > 0:
            execute_cooldown_timer(delay_sec, reason=f"Cooldown Block {block_index} ({label})")

        try:
            print(f"     [Image Engine] Polling {label} (Attempt {attempt}/{len(clusters)})...", flush=True)
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200 and len(resp.content) > 10000:
                raw_temp = out_path + ".tmp.jpg"
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)
                base = Image.open(raw_temp).convert("RGBA")
                bw, bh = base.size
                base = base.crop((0, 0, bw, bh - int(bh * 0.055)))
                base = fit_crop_and_sharpen_1080p(base)
                base.convert("RGB").save(out_path, "JPEG", quality=98)
                try: os.remove(raw_temp)
                except OSError: pass
                print(f"     [Image Engine] Succeeded via {label}! Rendered to 1920x1080 HD ({len(resp.content)} bytes).", flush=True)
                return True
            else:
                print(f"     [Image Engine] {label} returned HTTP {resp.status_code}.", flush=True)
        except requests.exceptions.Timeout:
            print(f"     [Image Engine] {label} timed out after {REQUEST_TIMEOUT}s.", flush=True)
        except Exception as e:
            print(f"     [Image Engine] {label} error: {e}", flush=True)

    print(f"     [Image Engine] All model clusters exhausted for Block {block_index}. Fallback applied.", flush=True)
    return False


def apply_lower_third_vignette(base: Image.Image) -> Image.Image:
    width, height = base.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(overlay)
    vig_start = int(height * 0.82)
    for y in range(vig_start, height):
        alpha = int(85 * (((y - vig_start) / (height - vig_start)) ** 1.3))
        v_draw.line([(0, y), (width, y)], fill=(12, 18, 24, alpha))
    return Image.alpha_composite(base.convert("RGBA"), overlay)


def stamp_channel_watermark(base: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(base)
    wx, wy = 55, 45
    crest_r = 22
    draw.ellipse([(wx - crest_r, wy - crest_r), (wx + crest_r, wy + crest_r)], fill=(225, 150, 40, 255), outline=(255, 245, 220, 255), width=2)
    star_font = None
    for fp in ["C:/Windows/Fonts/seguisym.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(fp):
            try:
                star_font = ImageFont.truetype(fp, 24)
                break
            except Exception:
                pass
    if not star_font:
        star_font = ImageFont.load_default()
    bbox_star = draw.textbbox((0, 0), "✦", font=star_font)
    sw = bbox_star[2] - bbox_star[0]
    sh = bbox_star[3] - bbox_star[1]
    draw.text((wx - (sw // 2), wy - (sh // 2) - 2), "✦", fill=(255, 255, 255, 255), font=star_font)
    name_fp = "C:/Windows/Fonts/arialbd.ttf"
    if not os.path.exists(name_fp):
        name_fp = ensure_cinzel_font()
    name_font = ImageFont.truetype(name_fp, 36)
    handle_font = ImageFont.truetype(name_fp, 22)
    tx = wx + 36
    draw.text((tx + 2, wy - 18 + 2), "Being a Bong", fill=(20, 15, 10, 255), font=name_font)
    draw.text((tx, wy - 18), "Being a Bong", fill=(255, 255, 255, 255), font=name_font)
    draw.text((tx + 1, wy + 20 + 1), "@beingabong", fill=(20, 15, 10, 220), font=handle_font)
    draw.text((tx, wy + 20), "@beingabong", fill=(255, 215, 100, 255), font=handle_font)
    return base


def create_vertical_gradient_text_mask(width: int, height: int, line: str, font: ImageFont.FreeTypeFont, top_col: tuple, bot_col: tuple) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.text((0, 0), line, fill=255, font=font)
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for y in range(height):
        factor = y / max(1, height - 1)
        r = int(top_col[0] + (bot_col[0] - top_col[0]) * factor)
        g = int(top_col[1] + (bot_col[1] - top_col[1]) * factor)
        b = int(top_col[2] + (bot_col[2] - top_col[2]) * factor)
        g_draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    gradient.putalpha(mask)
    return gradient


def stamp_3d_metallic_flame_typography(base: Image.Image, lines: list) -> Image.Image:
    width, height = base.size
    font_path = ensure_cinzel_font()
    title_font = ImageFont.truetype(font_path, 60)
    sub_font = ImageFont.truetype(font_path, 46)
    line_spacing = 76
    total_text_h = (len(lines) - 1) * line_spacing + 60
    start_y = int(height * 0.81) - (total_text_h // 2)
    draw = ImageDraw.Draw(base)

    for i, line in enumerate(lines):
        active_font = sub_font if i == len(lines) - 1 else title_font
        bbox = draw.textbbox((0, 0), line, font=active_font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (width - text_w) // 2
        y = start_y + (i * line_spacing)
        draw.text((x + 3, y + 4), line, font=active_font, fill=(15, 20, 30, 255), stroke_width=5, stroke_fill=(15, 20, 30, 255))
        draw.text((x, y), line, font=active_font, fill=(30, 45, 60, 255), stroke_width=3, stroke_fill=(30, 45, 60, 255))
        palette = GRADIENT_PALETTES[min(i, len(GRADIENT_PALETTES) - 1)]
        grad_layer = create_vertical_gradient_text_mask(text_w + 20, text_h + 20, line, active_font, palette[0], palette[1])
        base.paste(grad_layer, (x, y), grad_layer)
    return base


def ensure_block_cover_jit(cfg: dict, build_dir: str, gemini_client=None, batch_titles: list = None, batch_excerpt: str = ""):
    out_file = cfg["cover_file"]
    b_idx = cfg["index"]

    if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
        print(f"[{NOVEL_SLUG}] [Cached Image] Block {b_idx} Cover ready: '{out_file}'", flush=True)
        return

    if gemini_client and batch_titles:
        ch_s, ch_e = cfg["range"]
        active_prompt = deduce_block_scene_via_gemini(gemini_client, b_idx, ch_s, ch_e, batch_titles, batch_excerpt)
    else:
        active_prompt = cfg["prompt"]

    raw_art = os.path.join(build_dir, f"raw_block_{b_idx}.jpg")
    success = fetch_comic_artwork_landscape(active_prompt, raw_art, block_index=b_idx)

    if success and os.path.exists(raw_art):
        raw_img = Image.open(raw_art).convert("RGBA")
        base = raw_img
    else:
        print(f"[{NOVEL_SLUG}] [Image Engine] Generation fallback applied for Block {b_idx}.", flush=True)
        base = Image.new("RGBA", (1920, 1080), (*cfg["fallback_color"], 255))

    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base)
    base = stamp_3d_metallic_flame_typography(base, cfg["title"])
    base.convert("RGB").save(out_file, "JPEG", quality=98)
    print(f"[{NOVEL_SLUG}] [Saved Image] Block {b_idx} Cover: '{out_file}'", flush=True)


def create_dynamic_outro_slate(out_path: str):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        return
    base = Image.new("RGB", (1920, 1080), (18, 22, 32))
    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base)
    draw = ImageDraw.Draw(base)
    font_path = ensure_cinzel_font()
    head_font = ImageFont.truetype(font_path, 54)
    cta_font = ImageFont.truetype(font_path, 42)
    line1 = "CHAPTER 101 COMING SOON"
    line2 = "SUBSCRIBE FOR THE NEXT MARATHON"
    for i, txt in enumerate([line1, line2]):
        font = head_font if i == 0 else cta_font
        bbox = draw.textbbox((0, 0), txt, font=font)
        tw = bbox[2] - bbox[0]
        x = (1920 - tw) // 2
        y = 480 + (i * 80)
        draw.text((x + 3, y + 4), txt, font=font, fill=(10, 12, 18, 255))
        draw.text((x, y), txt, font=font, fill=(255, 215, 100, 255) if i == 0 else (255, 255, 255, 255))
    base.convert("RGB").save(out_path, "JPEG", quality=95)
    print(f"[{NOVEL_SLUG}] [Outro Slate] Generated 15s outro card: '{out_path}'", flush=True)


def generate_50ch_ensemble_cover(slug: str, build_dir: str, master_cover_path: str, gemini_client=None, char_map=None):
    print(f"\n[{slug}] [Phase 5] Synthesizing Multi-Character Master Cover...", flush=True)
    master_prompt = deduce_master_cover_via_gemini(gemini_client, slug, char_map)
    raw_ensemble = os.path.join(build_dir, "raw_master_cover_ensemble.jpg")
    fetch_comic_artwork_landscape(master_prompt, raw_ensemble, block_index=99)

    if os.path.exists(raw_ensemble) and os.path.getsize(raw_ensemble) > 10000:
        raw_img = Image.open(raw_ensemble).convert("RGBA")
        base = raw_img
    else:
        base = Image.new("RGBA", (1920, 1080), (30, 25, 40, 255))

    base = apply_lower_third_vignette(base)
    base = stamp_channel_watermark(base)

    master_title_lines = [
        "GAME ARRIVES",
        "INFINITE TALENT EVOLUTION",
        "Complete Marathon • Ch. 51–100"
    ]
    base = stamp_3d_metallic_flame_typography(base, master_title_lines)
    base.convert("RGB").save(master_cover_path, "JPEG", quality=98)
    print(f"[{slug}] [Master Thumbnail Complete] Saved to '{master_cover_path}'", flush=True)


# ==================== AUDIO SYNTHESIS & ASSEMBLY ====================
async def synthesize_line_record(row: dict, out_file: str, sem: asyncio.Semaphore, max_retries: int = 5):
    voice, pitch, rate, text = row["voice"], row["pitch"], row["rate"], row["text"]
    chunk_timeout = max(35.0, 25.0 + (len(text.split()) * 0.40))
    async with sem:
        for attempt in range(1, max_retries + 1):
            try:
                active_voice = voice
                if attempt >= 4:
                    active_voice = "en-US-GuyNeural" if row.get("gender") == "Male" else "en-US-JennyNeural"
                comm = edge_tts.Communicate(text, active_voice, pitch=pitch, rate=rate)
                await asyncio.wait_for(comm.save(out_file), timeout=chunk_timeout)
                if os.path.exists(out_file) and os.path.getsize(out_file) > 100:
                    return
            except Exception:
                pass
            if attempt == max_retries:
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
                    "-t", "0.5", "-q:a", "9", "-acodec", "libmp3lame", out_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            await asyncio.sleep((attempt * 1.5) + random.uniform(0.5, 1.5))


def get_audio_duration(file_path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 0.5


def format_timestamp(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_srt_time(seconds: float) -> str:
    h, m, s = int(seconds // 3600), int((seconds % 3600) // 60), int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


async def synthesize_chapter_task(ch_num: int, rows: list, title: str, build_dir: str, global_sem: asyncio.Semaphore):
    chapter_mp3 = os.path.join(build_dir, f"ch_{ch_num:03d}.mp3")
    chapter_meta = os.path.join(build_dir, f"ch_{ch_num:03d}_meta.json")
    if os.path.exists(chapter_mp3) and os.path.exists(chapter_meta):
        try:
            with open(chapter_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("duration", 0) > 60:
                print(f"[{NOVEL_SLUG}] [Cached Audio] Ch.{ch_num:03d} ({format_timestamp(meta['duration'])})", flush=True)
                return ch_num, chapter_mp3, meta["duration"], meta["title"], meta["relative_subtitles"]
        except Exception:
            pass

    temp_dir = os.path.join(build_dir, f"temp_ch_{ch_num:03d}")
    os.makedirs(temp_dir, exist_ok=True)
    chunk_files, tasks = [], []
    for row in rows:
        c_path = os.path.join(temp_dir, f"seg_{row['line_id']}.mp3")
        chunk_files.append(c_path)
        tasks.append(synthesize_line_record(row, c_path, global_sem))

    await asyncio.gather(*tasks)
    manifest_path = os.path.join(temp_dir, "manifest.txt")
    valid_chunks = [cf for cf in chunk_files if os.path.exists(cf) and os.path.getsize(cf) > 100]

    if not valid_chunks:
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
            "-t", "3.0", "-q:a", "9", "-acodec", "libmp3lame", chapter_mp3
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        with open(manifest_path, "w", encoding="utf-8") as f:
            for cf in valid_chunks:
                f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

        res = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-c", "copy", chapter_mp3],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        if res.returncode != 0 or not os.path.exists(chapter_mp3) or os.path.getsize(chapter_mp3) < 100:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest_path, "-acodec", "libmp3lame", "-ar", "24000", "-ac", "1", chapter_mp3],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

    rel_subtitles, rel_time = [], 0.0
    for cf, row in zip(valid_chunks, rows):
        dur = get_audio_duration(cf)
        sub_text = f"[{row['speaker']}]: {row['text']}" if row['line_type'] == "Dialogue" else row['text']
        rel_subtitles.append((rel_time, rel_time + dur, sub_text))
        rel_time += dur

    final_dur = get_audio_duration(chapter_mp3)
    with open(chapter_meta, "w", encoding="utf-8") as f:
        json.dump({"title": title, "duration": final_dur, "relative_subtitles": rel_subtitles}, f)

    for cf in chunk_files:
        try: os.remove(cf)
        except OSError: pass
    try: os.remove(manifest_path)
    except OSError: pass
    try: os.rmdir(temp_dir)
    except OSError: pass

    print(f"[{NOVEL_SLUG}] [Synthesized Audio] Ch.{ch_num:03d}: '{title}' ({format_timestamp(final_dur)})", flush=True)
    return ch_num, chapter_mp3, final_dur, title, rel_subtitles


def assemble_multi_image_video(block_durations: dict, final_audio_path: str, output_video_path: str):
    print(f"\n[{NOVEL_SLUG}] [Phase 4] Assembling Visual Transitions + 15s Dynamic Outro...", flush=True)
    video_segments = []
    for cfg in BLOCKS:
        b_idx = cfg["index"]
        dur = block_durations.get(b_idx, 0.0)
        if dur <= 0.1:
            dur = 60.0
        cfg["cover_file"] = os.path.join(BUILD_DIR, f"cover_block_{cfg['range'][0]}_{cfg['range'][1]}.jpg")
        ensure_block_cover_jit(cfg, BUILD_DIR)
        segment_video = os.path.join(BUILD_DIR, f"v_seg_block_{b_idx}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", f"{dur:.3f}",
            "-i", cfg["cover_file"], "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", segment_video
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        video_segments.append(segment_video)

    outro_slate = os.path.join(BUILD_DIR, "outro_slate_card.jpg")
    create_dynamic_outro_slate(outro_slate)
    outro_seg = os.path.join(BUILD_DIR, "v_seg_outro.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-t", "15.000",
        "-i", outro_slate, "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", outro_seg
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    video_segments.append(outro_seg)

    v_manifest = os.path.join(BUILD_DIR, "v_segments_list.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(BUILD_DIR, "full_video_track.mp4")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_manifest, "-c", "copy", full_video_track], check=True)
    subprocess.run(["ffmpeg", "-y", "-i", full_video_track, "-i", final_audio_path, "-c", "copy", "-movflags", "+faststart", "-shortest", output_video_path], check=True)

    for vs in video_segments:
        try: os.remove(vs)
        except OSError: pass
    try: os.remove(v_manifest)
    except OSError: pass
    try: os.remove(full_video_track)
    except OSError: pass


# ==================== MAIN ORCHESTRATION PIPELINE ====================
async def main():
    os.makedirs(BUILD_DIR, exist_ok=True)
    print(f"=== Starting Global Game Infinite Evolution Pipeline: Ch.{START_CHAPTER}–{END_CHAPTER} ===", flush=True)

    gemini_client = None
    if GENAI_AVAILABLE and GEMINI_API_KEY:
        try:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            print("[Gemini Engine] GenAI client initialized successfully.", flush=True)
        except Exception as e:
            print(f"[Gemini Note] Initialization skipped: {e}", flush=True)

    char_map, voc_map = load_characters_and_vocatives(NOVEL_SLUG, BASE_CHARACTERS)
    entity_mgr = EntityManager(novel_slug=NOVEL_SLUG, build_dir=BUILD_DIR)

    print(f"\n[{NOVEL_SLUG}] [Phase 1/4] Checking and Staging Chapters {START_CHAPTER} to {END_CHAPTER}...", flush=True)
    staged_chapters = []
    with requests.Session() as session:
        curr_url = START_URL
        for ch_num in range(START_CHAPTER, END_CHAPTER + 1):
            if not curr_url:
                print(f"[{NOVEL_SLUG}] Pagination exhausted early at Ch.{ch_num}.", flush=True)
                break
            ch_json = os.path.join(BUILD_DIR, f"ch_{ch_num:03d}_staged.json")

            if os.path.exists(ch_json):
                with open(ch_json, "r", encoding="utf-8") as f:
                    rows = json.load(f)
                title, _, next_url = scrape_chapter_content(session, curr_url, ch_num)
                print(f"[{NOVEL_SLUG}] [Cached Ch.{ch_num:03d}] {title} ({len(rows)} lines)", flush=True)
            else:
                title, text, next_url = scrape_chapter_content(session, curr_url, ch_num)
                entity_mgr.scan_chapter_for_entities(text, default_female_role="xiang_yinsha", default_male_role="mc")
                rows = parse_chapter_to_staged_json(text, entity_mgr, char_map, voc_map)
                with open(ch_json, "w", encoding="utf-8") as f:
                    json.dump(rows, f, indent=2, ensure_ascii=False)
                print(f"[{NOVEL_SLUG}] [Staged Ch.{ch_num:03d}] {title} ({len(rows)} blocks)", flush=True)

            staged_chapters.append((ch_num, rows, title))
            curr_url = next_url

    create_dynamic_outro_slate(os.path.join(BUILD_DIR, "outro_slate_card.jpg"))

    print(f"\n[{NOVEL_SLUG}] [Phase 2/4] Synthesizing Audio (Batches of {BATCH_SIZE})...", flush=True)
    global_sem = asyncio.Semaphore(GLOBAL_MAX_CONCURRENT_TTS)
    chapter_semaphore = asyncio.Semaphore(PARALLEL_CHAPTERS)

    async def run_chapter_bounded(cn, rw, tt):
        async with chapter_semaphore:
            return await synthesize_chapter_task(cn, rw, tt, BUILD_DIR, global_sem)

    all_results = []
    for b_idx in range(0, len(staged_chapters), BATCH_SIZE):
        batch = staged_chapters[b_idx:b_idx + BATCH_SIZE]
        batch_start_ch = batch[0][0]
        batch_end_ch = batch[-1][0]
        block_num = (b_idx // BATCH_SIZE) + 1

        print(f"\n{'='*25} STARTING BATCH {block_num}: Chapters {batch_start_ch} to {batch_end_ch} {'='*25}", flush=True)

        if block_num <= len(BLOCKS):
            b_cfg = BLOCKS[block_num - 1]
            b_cfg["cover_file"] = os.path.join(BUILD_DIR, f"cover_block_{b_cfg['range'][0]}_{b_cfg['range'][1]}.jpg")
            
            batch_titles = [c[2] for c in batch]
            sample_paragraphs = []
            for ch in batch:
                dialogues = [r["text"] for r in ch[1] if r["line_type"] == "Dialogue"]
                narrations = [r["text"] for r in ch[1] if r["line_type"] == "Narration"]
                if narrations:
                    sample_paragraphs.append(narrations[0])
                if dialogues:
                    sample_paragraphs.append(" ".join(dialogues[:3]))
                if len(narrations) > 1:
                    sample_paragraphs.append(narrations[-1])
            batch_sample = " \n".join(sample_paragraphs)[:2000]

            ensure_block_cover_jit(b_cfg, BUILD_DIR, gemini_client, batch_titles, batch_sample)

        batch_results = await asyncio.gather(*[run_chapter_bounded(cn, rw, tt) for cn, rw, tt in batch])
        all_results.extend(batch_results)
        print(f"{'='*25} BATCH {block_num} COMPLETE: Chapters {batch_start_ch} to {batch_end_ch} {'='*25}\n", flush=True)

    all_results.sort(key=lambda x: x[0])
    chapter_files, chapter_durations, timestamps, all_subtitles = [], {}, [], []
    global_offset = 0.0

    for ch_num, mp3_path, dur, title, rel_subs in all_results:
        chapter_files.append(mp3_path)
        chapter_durations[ch_num] = dur
        timestamps.append(f"{format_timestamp(global_offset)} - {title}")
        for s_rel, e_rel, text in rel_subs:
            all_subtitles.append((format_srt_time(global_offset + s_rel), format_srt_time(global_offset + e_rel), text))
        global_offset += dur

    block_durations = {cfg["index"]: sum(chapter_durations.get(c, 0.0) for c in range(cfg["range"][0], cfg["range"][1] + 1)) for cfg in BLOCKS}

    with open(TIMESTAMPS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(timestamps))
    with open(SUBTITLES_FILE, "w", encoding="utf-8") as f:
        for idx, (s_time, e_time, text) in enumerate(all_subtitles, 1):
            f.write(f"{idx}\n{s_time} --> {e_time}\n{text}\n\n")

    print(f"\n[{NOVEL_SLUG}] [Phase 3/4] Audio Mastering (-14 LUFS) & 15s Outro Pad...", flush=True)
    raw_master_audio = os.path.join(BUILD_DIR, "raw_master.mp3")
    master_manifest = os.path.join(BUILD_DIR, "master_list.txt")
    with open(master_manifest, "w", encoding="utf-8") as f:
        for cf in chapter_files:
            f.write(f"file '{os.path.abspath(cf).replace(os.sep, '/')}'\n")

    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", master_manifest, "-c", "copy", raw_master_audio], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", raw_master_audio,
        "-af", "highpass=f=85,equalizer=f=3200:t=q:w=1.5:g=2.5,acompressor=threshold=-16dB:ratio=3:attack=5:release=50,loudnorm=I=-14:TP=-1.5:LRA=7,apad=pad_dur=15",
        "-c:a", "libmp3lame", "-b:a", "192k", FINAL_AUDIO
    ], check=True)
    if os.path.exists(raw_master_audio):
        os.remove(raw_master_audio)

    assemble_multi_image_video(block_durations, FINAL_AUDIO, FINAL_VIDEO)
    entity_mgr.finalize_and_merge()

    generate_50ch_ensemble_cover(NOVEL_SLUG, BUILD_DIR, COVER_IMAGE, gemini_client, char_map)

    payload = {
        "snippet": {
            "title": VIDEO_TITLE,
            "description": f"{DESC_HEADER}{chr(10).join(timestamps)}{DESC_FOOTER}",
            "tags": TAGS,
            "categoryId": "24",
            "defaultLanguage": "en-US"
        },
        "status": {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False},
        "assets": {
            "video_file": os.path.abspath(FINAL_VIDEO),
            "thumbnail_file": os.path.abspath(COVER_IMAGE),
            "subtitles_file": os.path.abspath(SUBTITLES_FILE),
            "timestamps_file": os.path.abspath(TIMESTAMPS_FILE)
        }
    }
    with open(PAYLOAD_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[{NOVEL_SLUG}] Execution Complete! Output: {FINAL_VIDEO}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
