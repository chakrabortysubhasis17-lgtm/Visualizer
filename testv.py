import os
import re
import json
import time
import random
import asyncio
import subprocess
import urllib.parse
from typing import List, Literal

import httpx
import requests
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from text_director_utils import (
    scrape_chapter_content,
    parse_chapter_via_gemini_director,
    clean_and_parse_json
)
from media_utils import synthesize_chapter_audio
from subtitle_utils import build_srt_subtitles
from visual_utils import apply_lower_third_vignette

CREDENTIALS_FILE = "api_credentials.json"
BUILD_DIR = "build_shadow_slave_dynamic"
OUTPUT_VIDEO = "Shadow_Slave_Chapter_1_Dynamic_Comic.mp4"

# =====================================================================
# ASPECT RATIO MODE TOGGLE:
# Choose "crop_1920" (Approach 1) OR "pillarbox_1024" (Approach 2)
# =====================================================================
ASPECT_MODE: Literal["crop_1920", "pillarbox_1024"] = "crop_1920"

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080


def load_credentials(file_path: str = CREDENTIALS_FILE) -> dict:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to parse '{file_path}': {e}", flush=True)
    return {}


# =====================================================================
# 1. HARDENED STORYBOARD SCHEMA & PROMPT GENERATOR
# =====================================================================

class SceneBeat(BaseModel):
    scene_id: int
    start_line: int
    end_line: int
    scene_title: str
    camera_motion: Literal["zoom_in", "zoom_out", "pan_right", "tilt_down", "slow_push"]
    visual_prompt: str = Field(
        description="A rich, sharp dark gothic fantasy matte painting prompt matching the master style guide."
    )


class StoryboardManifest(BaseModel):
    scenes: List[SceneBeat]


def generate_dynamic_storyboard_strict(client, clean_title: str, staged_segments: list, max_retries: int = 4) -> List[dict]:
    total_lines = len(staged_segments)

    script_summary = []
    for s in staged_segments:
        line_num = int(s.get("line_id", 1))
        spk = s.get("speaker", "Narrator")
        txt = s.get("text", "")[:100]
        script_summary.append(f"Line {line_num:03d} [{spk}]: {txt}")

    script_text = "\n".join(script_summary)

    system_instruction = """
You are a master digital matte painter and art director for a dark fantasy visual novel.
Divide the chapter lines into 4 to 8 sequential visual scenes. For every scene, write an ultra-sharp, vivid concept art prompt.

MANDATORY AESTHETIC STYLE RULES:
1. Architectural Style: Dark gothic architecture, towering spires, intricate stone carvings, weathered castle masonry, ornate ironwork.
2. Lighting & Color: High-contrast chiaroscuro. Deep slate-gray storm clouds illuminated by warm amber/orange lantern glow radiating from arched windows.
3. Focal Accents: Include ominous glowing crimson/blood-red spherical orbs or sigils floating in the scene to anchor the composition.
4. CRITICAL HUMAN FRAMING RULE:
   - If a scene is about a CHARACTER (e.g. Sunny or Officer), the prompt MUST specify a 'Cinematic waist-up medium portrait' or 'Dramatic chest-up close shot'. The character's face and upper body MUST fill the majority of the frame so facial features are razor-sharp. NEVER render tiny full-body miniature characters sitting in distant landscapes.
   - If a scene is about the ENVIRONMENT (e.g. city streets, station exterior, cosmic void), prompt a 'Pure architectural dark gothic matte painting' with ZERO human figures.
5. Prompt Suffix: Every prompt must end with:
   'masterpiece, dark gothic concept art, hyper-detailed architectural drafting, glowing amber windows, floating crimson orbs, sharp focus, volumetric lighting, 8k resolution.'

RULES:
- Cover all lines from line 1 to the final line continuously without gaps.
- camera_motion must strictly be one of: zoom_in, zoom_out, pan_right, tilt_down, slow_push.
"""

    prompt = f"CHAPTER TITLE: {clean_title}\nTOTAL LINES: {total_lines}\n\nLINES CHRONOLOGY:\n{script_text}"

    for attempt in range(1, max_retries + 1):
        print(f"[Storyboard Director] Generating gothic scene prompts via Gemini (Attempt {attempt}/{max_retries})...", flush=True)
        try:
            response = client.models.generate_content(
                model="gemini-flash-lite-latest",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=StoryboardManifest,
                    temperature=0.2
                )
            )

            if response and response.text:
                data = json.loads(response.text)
                scenes = data.get("scenes", [])

                if len(scenes) >= 3:
                    scenes[0]["start_line"] = 1
                    scenes[-1]["end_line"] = total_lines

                    for i in range(len(scenes) - 1):
                        scenes[i + 1]["start_line"] = scenes[i]["end_line"] + 1

                    print(f"[Storyboard Director] [✓] Successfully styled {len(scenes)} dynamic gothic scenes.", flush=True)
                    return scenes

        except Exception as e:
            print(f"[Storyboard Director] Attempt {attempt} failed: {e}", flush=True)
            if attempt < max_retries:
                time.sleep(attempt * 3.0)

    raise RuntimeError("[Fatal] Failed to generate storyboard. Stopping to prevent low-quality output.")


# =====================================================================
# 2. POLLINATIONS FLUX ENGINE (SUPPORTING BOTH APPROACHES)
# =====================================================================

def fetch_pollinations_artwork_strict(prompt: str, out_path: str, scene_idx: int) -> str:
    """
    Fetches square artwork from Pollinations Flux and applies either:
    - Approach 1 ('crop_1920'): Request 1920x1920 and vertical center-crop to 1920x1080.
    - Approach 2 ('pillarbox_1024'): Request 1024x1024 and pillarbox with equal black bars.
    """
    if os.path.exists(out_path) and os.path.getsize(out_path) > 20000:
        return out_path

    clean_p = " ".join(prompt.split()).strip()
    encoded = urllib.parse.quote(clean_p)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    attempt = 1
    raw_temp = out_path + ".tmp.jpg"

    while True:
        seed = random.randint(100000, 9999999)

        if ASPECT_MODE == "crop_1920":
            req_w, req_h = 1920, 1920
        else:
            req_w, req_h = 1024, 1024

        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width={req_w}&height={req_h}&seed={seed}&model=flux&nologo=true"
        )
        print(f"     [Pollinations Flux] Scene {scene_idx} ({ASPECT_MODE} Mode | Attempt {attempt})...", flush=True)

        try:
            resp = requests.get(url, headers=headers, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 20000:
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)

                with Image.open(raw_temp) as test_img:
                    test_img.verify()

                base = Image.open(raw_temp).convert("RGBA")

                if ASPECT_MODE == "crop_1920":
                    # APPROACH 1: Scale to 1920 width, center-crop vertically to 1080 (zero stretching)
                    base = ImageOps.fit(
                        base,
                        (TARGET_WIDTH, TARGET_HEIGHT),
                        method=Image.Resampling.LANCZOS,
                        centering=(0.5, 0.45)
                    )
                else:
                    # APPROACH 2: Scale 1024x1024 to height 1080, pillarbox with equal black bars on sides
                    scale_factor = TARGET_HEIGHT / float(base.size[1])
                    new_w = int(base.size[0] * scale_factor)
                    base_resized = base.resize((new_w, TARGET_HEIGHT), Image.Resampling.LANCZOS)

                    canvas = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 255))
                    offset_x = (TARGET_WIDTH - new_w) // 2
                    canvas.paste(base_resized, (offset_x, 0))
                    base = canvas

                # Apply vignette for subtitle legibility
                base = apply_lower_third_vignette(base)

                # Save clean, uncompressed JPEG
                base.convert("RGB").save(out_path, "JPEG", quality=95, subsampling=0)

                try:
                    os.remove(raw_temp)
                except OSError:
                    pass

                print(f"     [Pollinations Flux] [✓] Scene {scene_idx} delivered with clean proportions!", flush=True)
                return out_path
            else:
                print(f"     [Pollinations Flux] Incomplete response (HTTP {resp.status_code}, {len(resp.content)} bytes). Retrying in 7s...", flush=True)

        except Exception as e:
            print(f"     [Pollinations Flux] Network warning: {e}. Retrying in 7s...", flush=True)

        attempt += 1
        time.sleep(7)


# =====================================================================
# 3. KEN BURNS MOTION COMPOSITOR (FFMPEG)
# =====================================================================

def render_ken_burns_segment(image_path: str, duration: float, motion_type: str, output_path: str):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return

    duration = max(2.5, duration)

    if motion_type == "zoom_in":
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z='min(zoom+0.0003,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
        )
    elif motion_type == "pan_right":
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z=1.12:x='if(lte(on,1),(iw-iw/zoom)*0.15,min((iw-iw/zoom)*0.85,x+0.35))':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
        )
    elif motion_type == "tilt_down":
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z=1.10:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min((ih-ih/zoom),y+0.25))':d=1:s=1920x1080:fps=24"
        )
    elif motion_type == "zoom_out":
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0003))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
        )
    else:  # slow_push
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z='min(zoom+0.0002,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
        )

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-t", f"{duration:.3f}",
        "-vf", f"{zoom_filter},format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "animation",
        "-r", "24", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


# =====================================================================
# 4. MASTER ORCHESTRATION PIPELINE
# =====================================================================

async def run_strict_dynamic_pipeline():
    creds = load_credentials()
    gemini_key = creds.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        raise ValueError("[Fatal] No valid Gemini API key found in api_credentials.json or environment.")

    client = genai.Client(api_key=gemini_key)

    os.makedirs(BUILD_DIR, exist_ok=True)
    chapter_url = "https://freewebnovel.com/novel/shadow-slave/chapter-1"
    ch_num = 1

    print("\n=======================================================", flush=True)
    print(f"  SHADOW SLAVE: GOTHIC MOTION COMIC ({ASPECT_MODE.upper()})", flush=True)
    print("=======================================================\n", flush=True)

    # 1. Scrape chapter text
    print("[1/5] Scraping Chapter Content...", flush=True)
    with httpx.Client() as session:
        clean_title, full_text, _ = scrape_chapter_content(session, chapter_url, ch_num, default_topic="Shadow Slave")
    print(f"      Scraped '{clean_title}' ({len(full_text.split())} words)", flush=True)

    # 2. Stage Script Lines
    print("\n[2/5] Parsing Script Lines via Gemini Director...", flush=True)
    stage_file = os.path.join(BUILD_DIR, "session_entities_staged.json")
    staged_segments = parse_chapter_via_gemini_director(client, clean_title, full_text, stage_file)
    total_lines = len(staged_segments)
    print(f"      Staged {total_lines} dialogue and narration lines.", flush=True)

    # 3. Dynamic Storyboard Analysis
    print("\n[3/5] Constructing Content-Driven Gothic Scene Beats...", flush=True)
    storyboard = generate_dynamic_storyboard_strict(client, clean_title, staged_segments)

    # 4. Multi-Voice Audio Generation
    print("\n[4/5] Synthesizing Multi-Voice TTS Audio & Timings...", flush=True)
    chapter_sem = asyncio.Semaphore(8)
    _, chapter_mp3, total_duration, _, rel_subtitles = await synthesize_chapter_audio(
        ch_num=ch_num,
        rows=staged_segments,
        title=clean_title,
        build_dir=BUILD_DIR,
        chapter_sem=chapter_sem
    )

    srt_path = os.path.join(BUILD_DIR, "subtitles.srt")
    build_srt_subtitles(rel_subtitles, srt_path)
    print(f"      Master Audio Duration: {total_duration:.2f}s across {len(rel_subtitles)} subtitle records.", flush=True)

    # 5. Exact Slicing & Visual Generation
    print("\n[5/5] Synthesizing Visuals and Camera Motion...", flush=True)
    rendered_video_segments = []

    for scene in storyboard:
        s_id = scene["scene_id"]
        s_title = scene["scene_title"]
        s_start = max(1, min(scene["start_line"], len(rel_subtitles)))
        s_end = max(s_start, min(scene["end_line"], len(rel_subtitles)))
        motion = scene["camera_motion"]
        prompt = scene["visual_prompt"]

        start_timestamp = rel_subtitles[s_start - 1][0]
        end_timestamp = rel_subtitles[s_end - 1][1]
        scene_dur = max(2.5, end_timestamp - start_timestamp)

        print(f"\n   -> Scene {s_id}: '{s_title}'", flush=True)
        print(f"      Lines: {s_start} to {s_end} | Duration: {scene_dur:.2f}s ({start_timestamp:.1f}s -> {end_timestamp:.1f}s)", flush=True)
        print(f"      Prompt: {prompt[:120]}...", flush=True)

        art_file = os.path.join(BUILD_DIR, f"scene_{s_id}_flux.jpg")
        video_seg_file = os.path.join(BUILD_DIR, f"v_seg_{s_id}.mp4")

        fetch_pollinations_artwork_strict(prompt, art_file, scene_idx=s_id)
        render_ken_burns_segment(art_file, scene_dur, motion, video_seg_file)
        rendered_video_segments.append(video_seg_file)

    # 6. Lossless Multiplexing
    v_manifest = os.path.join(BUILD_DIR, "v_concat_manifest.txt")
    with open(v_manifest, "w", encoding="utf-8") as f:
        for vs in rendered_video_segments:
            f.write(f"file '{os.path.abspath(vs).replace(os.sep, '/')}'\n")

    full_video_track = os.path.join(BUILD_DIR, "full_video_track.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_manifest, "-c", "copy", full_video_track],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )

    final_cmd = [
        "ffmpeg", "-y",
        "-i", full_video_track,
        "-i", chapter_mp3,
        "-i", srt_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-map", "2:s:0",
        "-c:v", "copy",
        "-c:a", "copy",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=eng",
        "-metadata:s:s:0", "title=English",
        "-shortest",
        OUTPUT_VIDEO
    ]
    subprocess.run(final_cmd, check=True)

    print(f"\n=======================================================", flush=True)
    print(f"  [SUCCESS] High-Definition Gothic Motion Comic Ready: '{OUTPUT_VIDEO}'", flush=True)
    print(f"=======================================================\n", flush=True)


if __name__ == "__main__":
    asyncio.run(run_strict_dynamic_pipeline())