import os
import re
import shutil
from typing import Dict, List, Tuple, Union, Optional, Any

# Ensure D: drive environment variables are locked
os.environ.setdefault("ARGOS_PACKAGES_DIR", r"D:\argos_translate\packages")
os.environ.setdefault("ARGOS_DATA_DIR", r"D:\argos_translate\data")

try:
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False

try:
    import pysrt
    PYSRT_AVAILABLE = True
except ImportError:
    PYSRT_AVAILABLE = False

LANGUAGE_REGISTRY: Dict[str, Dict[str, str]] = {
    "en": {"iso639_2": "eng", "name": "English"}
 #   "de": {"iso639_2": "deu", "name": "German"},
 #   "es": {"iso639_2": "spa", "name": "Spanish"},
 #   "pt": {"iso639_2": "por", "name": "Portuguese"},
 #   "ru": {"iso639_2": "rus", "name": "Russian"},
 #   "hi": {"iso639_2": "hin", "name": "Hindi"},
 #   "bn": {"iso639_2": "ben", "name": "Bengali"},
 #   "ms": {"iso639_2": "msa", "name": "Malay"},
 #   "tl": {"iso639_2": "tgl", "name": "Tagalog"},
 #   "fr": {"iso639_2": "fra", "name": "French"},
 #   "fi": {"iso639_2": "fin", "name": "Finnish"},
 #   "ja": {"iso639_2": "jpn", "name": "Japanese"},
 #   "pl": {"iso639_2": "pol", "name": "Polish"},
 #   "ur": {"iso639_2": "urd", "name": "Urdu"},
 #   "ar": {"iso639_2": "ara", "name": "Arabic"},
 #   "vi": {"iso639_2": "vie", "name": "Vietnamese"}
}

RE_BRACKETED_TAG = re.compile(r'(\[[^\]]+\])')
_TRANSLATION_ENGINES: Dict[str, Any] = {}


def format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = min(int(round((seconds - int(seconds)) * 1000)), 999)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt_file(subtitles: List[Tuple[float, float, str]], output_path: str) -> bool:
    if not subtitles:
        return False

    if PYSRT_AVAILABLE:
        try:
            srt_file = pysrt.SubRipFile()
            for idx, (s_sec, e_sec, txt) in enumerate(subtitles, 1):
                start_h, start_m, start_s = int(s_sec // 3600), int((s_sec % 3600) // 60), int(s_sec % 60)
                start_ms = min(int(round((s_sec - int(s_sec)) * 1000)), 999)
                end_h, end_m, end_s = int(e_sec // 3600), int((e_sec % 3600) // 60), int(e_sec % 60)
                end_ms = min(int(round((e_sec - int(e_sec)) * 1000)), 999)

                sub_item = pysrt.SubRipItem(
                    index=idx,
                    start=pysrt.SubRipTime(hours=start_h, minutes=start_m, seconds=start_s, milliseconds=start_ms),
                    end=pysrt.SubRipTime(hours=end_h, minutes=end_m, seconds=end_s, milliseconds=end_ms),
                    text=txt
                )
                srt_file.append(sub_item)

            srt_file.save(output_path, encoding="utf-8")
            return os.path.exists(output_path) and os.path.getsize(output_path) > 50
        except Exception:
            pass

    lines = []
    for idx, (s_sec, e_sec, txt) in enumerate(subtitles, 1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(s_sec)} --> {format_srt_time(e_sec)}")
        lines.append(txt)
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return os.path.exists(output_path) and os.path.getsize(output_path) > 50


def build_srt_subtitles(subtitles: list, output_path: str) -> bool:
    """Writes the master English SRT file."""
    parsed = []
    for item in subtitles:
        if isinstance(item, (tuple, list)):
            parsed.append((float(item[0]), float(item[1]), str(item[2]).strip()))
        elif isinstance(item, dict):
            s = float(item.get("start", 0.0))
            e = float(item.get("end", s + 1.0))
            parsed.append((s, e, str(item.get("text", "")).strip()))
    return write_srt_file(parsed, output_path)


def _defang_and_isolate_text(text: str) -> Tuple[str, List[str]]:
    tags = []

    def _repl(match):
        tags.append(match.group(0))
        return f"__SYS_TAG_{len(tags)-1}__"

    isolated = RE_BRACKETED_TAG.sub(_repl, text)
    return isolated, tags


def _refang_text(translated_text: str, tags: List[str]) -> str:
    restored = translated_text
    for idx, tag in enumerate(tags):
        placeholder = f"__SYS_TAG_{idx}__"
        restored = restored.replace(placeholder, tag)
        restored = re.sub(rf"__\s*SYS_TAG_{idx}\s*__", tag, restored, flags=re.I)
    return restored


def _get_installed_engine(target_lang: str):
    if target_lang in _TRANSLATION_ENGINES:
        return _TRANSLATION_ENGINES[target_lang]

    installed = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed if l.code == "en"), None)
    to_lang = next((l for l in installed if l.code == target_lang), None)

    if from_lang and to_lang:
        translation = from_lang.get_translation(to_lang)
        if translation:
            _TRANSLATION_ENGINES[target_lang] = translation
            return translation
    return None


def _translate_batch_offline(texts: List[str], target_lang: str) -> List[str]:
    engine = _get_installed_engine(target_lang)
    if not engine:
        print(f"[Subtitle Engine] [Notice] Offline model for {target_lang} not installed. Retaining English lines.", flush=True)
        return texts

    translated_all = []
    for item in texts:
        if not item.strip():
            translated_all.append("")
            continue

        clean_item, tags = _defang_and_isolate_text(item)
        try:
            raw_out = engine.translate(clean_item)
            translated_all.append(_refang_text(raw_out, tags))
        except Exception:
            translated_all.append(item)

    return translated_all


def generate_subtitles_bundle(
    base_subtitles: List[Union[Tuple[float, float, str], Dict]],
    build_dir: str,
    target_languages: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    POST-RENDER ENTRYPOINT:
    1. Creates build/subtitles/
    2. Copies root subtitles.srt to build/subtitles/subtitles_eng.srt & subtitles_en-US.srt
    3. Translates offline using D: models into build/subtitles/subtitles_<iso3>.srt
    """
    if not base_subtitles:
        return {}

    subs_dir = os.path.join(build_dir, "subtitles")
    os.makedirs(subs_dir, exist_ok=True)
    generated_srt_files: Dict[str, str] = {}

    parsed_subs: List[Tuple[float, float, str]] = []
    for item in base_subtitles:
        if isinstance(item, (tuple, list)):
            s_sec, e_sec, txt = float(item[0]), float(item[1]), str(item[2]).strip()
        elif isinstance(item, dict):
            s_sec = float(item.get("start", 0.0))
            e_sec = float(item.get("end", s_sec + 1.0))
            txt = str(item.get("text", "")).strip()
        else:
            continue
        parsed_subs.append((s_sec, e_sec, txt))

    if not parsed_subs:
        return {}

    # Copy the master English files to build/subtitles/
    en_srt_path = os.path.join(subs_dir, "subtitles_eng.srt")
    en_us_srt_path = os.path.join(subs_dir, "subtitles_en-US.srt")
    root_subtitles = os.path.join(build_dir, "subtitles.srt")

    if os.path.exists(root_subtitles):
        shutil.copy2(root_subtitles, en_srt_path)
        shutil.copy2(root_subtitles, en_us_srt_path)
    else:
        write_srt_file(parsed_subs, en_srt_path)
        shutil.copy2(en_srt_path, en_us_srt_path)

    generated_srt_files["eng"] = en_srt_path
    print("[Subtitle Engine] [OK] English & English-US subtitles mirrored into build/subtitles/.", flush=True)

    if not target_languages or not ARGOS_AVAILABLE:
        return generated_srt_files

    raw_dialogues = [s[2] for s in parsed_subs]

    # Offline translation loop directly from D: drive models
    for lang in target_languages:
        lang_clean = lang.lower().strip()
        if lang_clean not in LANGUAGE_REGISTRY or lang_clean == "en":
            continue

        meta = LANGUAGE_REGISTRY[lang_clean]
        iso_code_3 = meta["iso639_2"]
        out_srt_path = os.path.join(subs_dir, f"subtitles_{iso_code_3}.srt")

        print(f"[Subtitle Engine] Translating into {meta['name']} ({iso_code_3}) locally on D: drive...", flush=True)
        translated_lines = _translate_batch_offline(raw_dialogues, lang_clean)
        lang_subs = [(parsed_subs[i][0], parsed_subs[i][1], translated_lines[i]) for i in range(len(parsed_subs))]

        if write_srt_file(lang_subs, out_srt_path):
            generated_srt_files[iso_code_3] = out_srt_path
            print(f"[Subtitle Engine] [OK] Written {meta['name']} ({iso_code_3}) subtitles.", flush=True)

    return generated_srt_files