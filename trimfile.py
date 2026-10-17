import os
import subprocess
import sys

INPUT_VIDEO = r"D:\Projects\visualer\final_road_to_mastery_001_050.mp4"
OUTPUT_VIDEO = r"D:\Projects\visualer\final_road_to_mastery_001_050_trimmed.mp4"
TARGET_DURATION = "11:59:59"  # 11 hours, 59 minutes, 59 seconds


def trim_video(input_path: str, output_path: str, duration_limit: str):
    if not os.path.exists(input_path):
        print(f"[Error] File not found: {input_path}")
        sys.exit(1)

    print(f"[Trimmer] Trimming '{input_path}' to {duration_limit}...")

    cmd = [
        "ffmpeg",
        "-y",
        "-ss", "00:00:00",
        "-i", input_path,
        "-t", duration_limit,
        "-c", "copy",
        "-avoid_negative_ts", "make_zero",
        output_path,
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\n[Success] Trimmed video saved to:\n{output_path}")
    except subprocess.CalledProcessError as e:
        print(f"\n[Error] FFmpeg failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("\n[Error] 'ffmpeg' is not found in PATH. Make sure FFmpeg is installed and accessible.")
        sys.exit(1)


if __name__ == "__main__":
    trim_video(INPUT_VIDEO, OUTPUT_VIDEO, TARGET_DURATION)
