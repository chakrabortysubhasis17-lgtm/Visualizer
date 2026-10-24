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
REGISTRY_FILE = "character_registry.json"
BUILD_DIR = "build_shadow_slave_dynamic"
OUTPUT_VIDEO = "Shadow_Slave_Chapter_1_Dynamic_Comic.mp4"
SERIES_ID = "shadow_slave"

TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080


def load_credentials(file_path: str = CREDENTIALS_FILE) -> dict:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Failed to parse credentials: {e}", flush=True)
    return {}


def load_registry(file_path: str = REGISTRY_FILE, series_id: str = SERIES_ID) -> dict:
    """Loads the character and environment registry for the selected series."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"[Fatal] Missing registry file '{file_path}'.")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    series_data = data.get("series", {}).get(series_id)
    if not series_data:
        raise KeyError(f"[Fatal] Series '{series_id}' not found in registry '{file_path}'.")
    return series_data


# =====================================================================
# 1. GRANULAR STORYBOARD SCHEMA WITH DIALOGUE ENSEMBLE STAGING
# =====================================================================

class SceneBeat(BaseModel):
    scene_id: int
    start_line: int
    end_line: int
    scene_title: str
    staging_type: Literal["solo", "two_shot", "group_shot", "environment_only"]
    camera_motion: Literal["zoom_slow", "zoom_punch", "pan_slow", "tilt_slumber", "shake_impact"]
    visual_prompt: str = Field(
        description="A composition prompt embedding the exact character and group visual anchors from the registry."
    )


class StoryboardManifest(BaseModel):
    scenes: List[SceneBeat]


def generate_dynamic_storyboard_strict(
    client, clean_title: str, staged_segments: list, registry: dict, max_retries: int = 4
) -> List[dict]:
    total_lines = len(staged_segments)

    # Format script lines for Gemini context
    script_summary = []
    for s in staged_segments:
        line_num = int(s.get("line_id", 1))
        spk = s.get("speaker", "Narrator")
        txt = s.get("text", "")[:110]
        script_summary.append(f"Line {line_num:03d} [{spk}]: {txt}")

    script_text = "\n".join(script_summary)

    # Serialize registry for Gemini injection
    reg_context = json.dumps({
        "characters": {k: v["visual_core"] for k, v in registry.get("characters", {}).items()},
        "groups": {k: v["visual_core"] for k, v in registry.get("groups", {}).items()},
        "environments": registry.get("environments", {}),
        "style_suffix": registry.get("art_style_suffix", "")
    }, indent=2)

    system_instruction = f"""
You are an expert anime storyboard director.
Divide this novel chapter into 18 to 26 rapid, visually engaging scene beats.
DO NOT create long, static scenes. Cut frequently (every 10 to 30 seconds of content).

MANDATORY STAGING RULES:
1. SOLO SCENES ('solo'): When one character speaks or reflects alone, generate a waist-up medium portrait of that character using their exact visual core.
2. TWO-PERSON DIALOGUE ('two_shot'): When two characters talk to each other (e.g. Sunny and Desk Officer), YOU MUST SHOW BOTH CHARACTERS IN THE SAME SCENE. Describe both characters' visual cores side-by-side or facing each other.
3. GROUP SCENES ('group_shot'): When multiple guards, riot police, or crowds are involved, render a wide group shot featuring the main character alongside the group template.
4. ENVIRONMENT SCENES ('environment_only'): For broad establishing shots or cosmic events with no characters, depict the gothic architecture with zero human figures.
5. CAMERA MOTIONS:
   - 'zoom_slow': Gradual dramatic push-in.
   - 'zoom_punch': Fast intense zoom on key dialogue or sudden shocks.
   - 'pan_slow': Horizontal pan across establishing environments.
   - 'tilt_slumber': Downward vertical drift when drowsiness or falling is mentioned.
   - 'shake_impact': Camera shake on alarms, yells, or sudden panic (e.g., Code Black).

CANONICAL REGISTRY TEMPLATES:
{reg_context}

For every scene prompt, you MUST combine the staging characters/environments and append the exact style_suffix.
"""

    prompt = f"CHAPTER: {clean_title}\nTOTAL LINES: {total_lines}\n\nLINES CHRONOLOGY:\n{script_text}"

    for attempt in range(1, max_retries + 1):
        print(f"[Storyboard Director] Generating granular scene beats (Attempt {attempt}/{max_retries})...", flush=True)
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

                if len(scenes) >= 12:
                    scenes[0]["start_line"] = 1
                    scenes[-1]["end_line"] = total_lines

                    for i in range(len(scenes) - 1):
                        scenes[i + 1]["start_line"] = scenes[i]["end_line"] + 1

                    print(f"[Storyboard Director] [✓] Successfully mapped {len(scenes)} dynamic scene beats.", flush=True)
                    return scenes

        except Exception as e:
            print(f"[Storyboard Director] Attempt {attempt} failed: {e}", flush=True)
            if attempt < max_retries:
                time.sleep(attempt * 3.0)

    raise RuntimeError("[Fatal] Failed to generate granular storyboard. Aborting to avoid low-quality output.")


# =====================================================================
# 2. POLLINATIONS 1920x1920 NATIVE + VERTICAL 16:9 CENTER CROP
# =====================================================================

def fetch_pollinations_artwork_strict(prompt: str, out_path: str, scene_idx: int) -> str:
    """
    Requests a 1920x1920 square canvas from Pollinations Flux to prevent horizontal squishing,
    then center-crops vertically to 1920x1080 to maintain true anatomical proportions.
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
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1920&height=1920&seed={seed}&model=flux&nologo=true"
        )
        print(f"     [Pollinations Flux] Scene {scene_idx} (Attempt {attempt})...", flush=True)

        try:
            resp = requests.get(url, headers=headers, timeout=60)
            if resp.status_code == 200 and len(resp.content) > 20000:
                with open(raw_temp, "wb") as f:
                    f.write(resp.content)

                with Image.open(raw_temp) as test_img:
                    test_img.verify()

                base = Image.open(raw_temp).convert("RGBA")

                # Center-crop 1920x1920 vertically to 1920x1080 (zero horizontal stretch)
                base = ImageOps.fit(
                    base,
                    (TARGET_WIDTH, TARGET_HEIGHT),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.45)
                )

                base = apply_lower_third_vignette(base)
                base.convert("RGB").save(out_path, "JPEG", quality=95, subsampling=0)

                try:
                    os.remove(raw_temp)
                except OSError:
                    pass

                print(f"     [Pollinations Flux] [✓] Scene {scene_idx} delivered with clean proportions!", flush=True)
                return out_path
            else:
                print(f"     [Pollinations Flux] Returned HTTP {resp.status_code}. Retrying in 7s...", flush=True)

        except Exception as e:
            print(f"     [Pollinations Flux] Request failed: {e}. Retrying in 7s...", flush=True)

        attempt += 1
        time.sleep(7)


# =====================================================================
# 3. ENHANCED MOTION ENGINE (ZOOM, TILT, PAN, SHAKE)
# =====================================================================

def render_ken_burns_segment(image_path: str, duration: float, motion_type: str, output_path: str):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return

    duration = max(2.0, duration)

    if motion_type == "zoom_punch":
        # Fast punch-in for sudden dramatic beats
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z='min(zoom+0.0012,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
        )
    elif motion_type == "shake_impact":
        # Rapid micro-shakes on impact/alarms (10% overscan prevents edge tearing)
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z=1.12:"
            "x='iw/2-(iw/zoom/2)+sin(on*4)*7':"
            "y='ih/2-(ih/zoom/2)+cos(on*5)*7':"
            "d=1:s=1920x1080:fps=24"
        )
    elif motion_type == "tilt_slumber":
        # Slow downward drift mimicking heavy eyelids / falling asleep
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z=1.12:x='iw/2-(iw/zoom/2)':y='if(lte(on,1),0,min((ih-ih/zoom),y+0.45))':d=1:s=1920x1080:fps=24"
        )
    elif motion_type == "pan_slow":
        # Wide horizontal sweep
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z=1.14:x='if(lte(on,1),(iw-iw/zoom)*0.15,min((iw-iw/zoom)*0.85,x+0.45))':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
        )
    else:  # zoom_slow fallback
        zoom_filter = (
            "scale=2560:1440,"
            "zoompan=z='min(zoom+0.0004,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=24"
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
    registry = load_registry(REGISTRY_FILE, series_id=SERIES_ID)

    os.makedirs(BUILD_DIR, exist_ok=True)
    chapter_url = "https://freewebnovel.com/novel/shadow-slave/chapter-1"
    ch_num = 1

    print("\n=======================================================", flush=True)
    print(f"  {registry['title'].upper()}: HIGH-TEMPO MOTION COMIC", flush=True)
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

    # 3. Dynamic Storyboard with Character Registry Injection
    print("\n[3/5] Constructing Storyboard with Dialogue Staging (Solo, Two-Shot, Group)...", flush=True)
    storyboard = generate_dynamic_storyboard_strict(client, clean_title, staged_segments, registry)

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

    # 5. Exact Timestamp Slicing & Visual Generation
    print(f"\n[5/5] Synthesizing {len(storyboard)} Visual Scenes with Camera Motions...", flush=True)
    rendered_video_segments = []

    for scene in storyboard:
        s_id = scene["scene_id"]
        s_title = scene["scene_title"]
        staging = scene["staging_type"]
        motion = scene["camera_motion"]
        prompt = scene["visual_prompt"]

        s_start = max(1, min(scene["start_line"], len(rel_subtitles)))
        s_end = max(s_start, min(scene["end_line"], len(rel_subtitles)))

        start_timestamp = rel_subtitles[s_start - 1][0]
        end_timestamp = rel_subtitles[s_end - 1][1]
        scene_dur = max(2.5, end_timestamp - start_timestamp)

        print(f"\n   -> Scene {s_id:02d}: '{s_title}' [{staging.upper()}]", flush=True)
        print(f"      Lines: {s_start} to {s_end} | Duration: {scene_dur:.2f}s | Motion: {motion}", flush=True)
        print(f"      Prompt: {prompt[:130]}...", flush=True)

        art_file = os.path.join(BUILD_DIR, f"scene_{s_id:02d}_flux.jpg")
        video_seg_file = os.path.join(BUILD_DIR, f"v_seg_{s_id:02d}.mp4")

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
    print(f"  [SUCCESS] High-Tempo Dynamic Motion Comic Ready: '{OUTPUT_VIDEO}'", flush=True)
    print(f"=======================================================\n", flush=True)


if __name__ == "__main__":
    asyncio.run(run_strict_dynamic_pipeline())