import os
import re
import sys
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter

def extract_video_id(url: str) -> str:
    """Extracts the 11-character video ID from common YouTube URL formats."""
    parsed = urlparse(url.strip())
    
    if parsed.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed.path.lstrip('/')
    
    if parsed.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
        if parsed.path == '/watch':
            queries = parse_qs(parsed.query)
            return queries.get('v', [None])[0]
        if parsed.path.startswith(('/embed/', '/v/')):
            return parsed.path.split('/')[2]
            
    match = re.search(r'([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(1)
        
    raise ValueError(f"Could not extract a valid YouTube video ID from: {url}")

def download_en_us_srt(youtube_url: str, output_path: str = None):
    video_id = extract_video_id(youtube_url)
    print(f"Target Video ID: {video_id}")
    
    ytt_api = YouTubeTranscriptApi()
    formatter = SRTFormatter()
    
    print("Fetching available transcript list...")
    transcript_list = ytt_api.list(video_id)
    
    # Priority order: en-US explicitly first, then standard en fallback
    try:
        transcript = transcript_list.find_transcript(['en-US', 'en'])
    except Exception as e:
        print(f"Direct English/en-US transcript not found ({e}). Checking translatable options...")
        try:
            # If native en-US isn't available, check if we can translate the existing track to en-US
            base_transcript = next(iter(transcript_list))
            if base_transcript.is_translatable:
                print(f"Translating {base_transcript.language_code} track to en-US...")
                transcript = base_transcript.translate('en-US')
            else:
                transcript = base_transcript
        except Exception:
            raise RuntimeError("No suitable transcript found on this video.")

    print(f"Found track: {transcript.language} ({transcript.language_code}) [Generated: {transcript.is_generated}]")
    fetched_transcript = transcript.fetch()

    srt_formatted = formatter.format_transcript(fetched_transcript)

    if not output_path:
        output_path = f"{video_id}_{transcript.language_code}.srt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_formatted)

    print(f"Successfully saved SRT to: {output_path}")

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://youtu.be/gJIlNusofW0"
    download_en_us_srt(url)
