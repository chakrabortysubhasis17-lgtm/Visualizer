import os
import re
from bs4 import BeautifulSoup

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def clean_title(title: str, ch_num: int) -> str:
    # Fix WebNovel typos (e.g. "Chaper 2:") and duplicate prefixes
    cleaned = re.sub(r'^(?:chapter|chaper)\s*\d+[\s:\-–—]+(?:chapter|chaper)\s*\d+[\s:\-–—]*', '', title, flags=re.I)
    cleaned = re.sub(r'^(?:chapter|chaper)\s*\d+[\s:\-–—]*', '', cleaned, flags=re.I).strip()
    return f"Chapter {ch_num:02d} - {cleaned}" if cleaned else f"Chapter {ch_num:02d}"

def extract_chapters(output_dir: str = "extracted_chapters"):
    # Detect the file automatically
    candidates = [
        "New Text Document (6)_2.txt",
        "New Text Document (6).txt",
        "story.html",
        "story.txt"
    ]
    input_file = next((f for f in candidates if os.path.exists(f)), None)

    if not input_file:
        # Check for any .txt or .html file in the current directory containing WebNovel content
        for f in os.listdir("."):
            if f.endswith((".txt", ".html")) and os.path.isfile(f):
                input_file = f
                break

    if not input_file:
        print("Error: Could not locate your input text/html file in this directory.")
        return

    print(f"Reading input file: '{input_file}'...")
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")
    os.makedirs(output_dir, exist_ok=True)

    # Locate all chapter containers specifically without decomposing parent divs
    chapter_containers = soup.find_all(
        "div", class_=lambda c: c and "chapter_content" in c.split()
    )

    if not chapter_containers:
        # Fallback query for alternative WebNovel wrappers
        chapter_containers = soup.find_all("div", attrs={"data-cid": True})

    print(f"Found {len(chapter_containers)} chapter(s).\n")

    for idx, ch in enumerate(chapter_containers, 1):
        # 1. Extract Title (Prefer clean data-chaptername attribute)
        raw_title = ch.get("data-chaptername")
        if not raw_title:
            h1 = ch.find(["h1", "h2"])
            raw_title = h1.get_text(strip=True) if h1 else f"Chapter {idx}"

        formatted_title = clean_title(raw_title, idx)

        # 2. Extract Paragraphs specifically from story text containers
        paragraphs = []
        words_div = ch.find("div", class_=re.compile(r"cha-words"))
        search_root = words_div if words_div else ch

        for p in search_root.find_all("p"):
            # Skip comments, buttons, and UI text
            if p.find_parent(class_=re.compile(r"(operate-bar|user-links-wrap|cha-info)")):
                continue
            
            txt = p.get_text(strip=True)
            if txt and txt.lower() not in ["comment", "vote"]:
                paragraphs.append(txt)

        # 3. Save to file
        safe_filename = sanitize_filename(formatted_title) + ".txt"
        file_path = os.path.join(output_dir, safe_filename)

        with open(file_path, "w", encoding="utf-8") as out:
            out.write(f"{formatted_title}\n")
            out.write("=" * len(formatted_title) + "\n\n")
            out.write("\n\n".join(paragraphs))

        word_count = len(" ".join(paragraphs).split())
        print(f"[✓ Saved] {safe_filename} ({len(paragraphs)} paragraphs, {word_count} words)")

    print(f"\nCompleted. All chapters saved to: '{os.path.abspath(output_dir)}'")

if __name__ == "__main__":
    extract_chapters()
