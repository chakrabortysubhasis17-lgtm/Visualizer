import os
import re
import urllib.request
import urllib.error

# List of target YouTube URLs
urls = [
    "https://www.youtube.com/watch?v=63J8hOgI2HM",
    "https://www.youtube.com/watch?v=bliNKLyjEIk",
    "https://www.youtube.com/watch?v=KvtiaiMITio",
    "https://www.youtube.com/watch?v=EEa6vLaf27Q",
    "https://www.youtube.com/watch?v=ycevz2yzksM",
    "https://www.youtube.com/watch?v=FzoCbeOge4I",
    "https://www.youtube.com/watch?v=gJwVqx5YPvc",
    "https://www.youtube.com/watch?v=UZyY9KNHrag",
    "https://www.youtube.com/watch?v=V6tUfu6t1a4",
    "https://www.youtube.com/watch?v=yq4i0huCKGs",
    "https://www.youtube.com/watch?v=XfVQVn90s4I",
    "https://www.youtube.com/watch?v=irE7fW4qyYM",
    "https://www.youtube.com/watch?v=dEeo7yZQDk0",
    "https://www.youtube.com/watch?v=UU-gpl6YOzE",
    "https://www.youtube.com/watch?v=vWuUGtN0gFs",
    "https://www.youtube.com/watch?v=JrBjVLRqbVs",
    "https://www.youtube.com/watch?v=j8WSJd7vyyI",
    "https://www.youtube.com/watch?v=xswVVVfApvg",
    "https://www.youtube.com/watch?v=xpZb-2FQ_ns",
    "https://www.youtube.com/watch?v=i_im2u7iDZs",
    "https://www.youtube.com/watch?v=hCv46Tijaqk",
    "https://www.youtube.com/watch?v=ubV1-f4aVHE",
    "https://www.youtube.com/watch?v=g137xXEH96M",
    "https://www.youtube.com/watch?v=ADV-gnBIkmE",
    "https://www.youtube.com/watch?v=EnP-GmOT7kM",
    "https://www.youtube.com/watch?v=bbjaSLXjhyg",
    "https://www.youtube.com/watch?v=sjICaGn-qWY",
    "https://www.youtube.com/watch?v=It4L1JmjGtQ",
    "https://www.youtube.com/watch?v=uFPc30p0PT0",
    "https://www.youtube.com/watch?v=DPauQgkvCb0",
    "https://www.youtube.com/watch?v=gyCcdnw2cDM",
    "https://www.youtube.com/watch?v=b1eJN9rSAQA",
    "https://www.youtube.com/watch?v=afoDPBopKvw",
    "https://www.youtube.com/watch?v=bA1yghvmfhk",
    "https://www.youtube.com/watch?v=fdBdE9udj3Q",
    "https://www.youtube.com/watch?v=hgqeVq0tRUI",
    "https://www.youtube.com/watch?v=j3PYcG-Sj9M",
    "https://www.youtube.com/watch?v=P1duYnISqpI",
    "https://www.youtube.com/watch?v=COUN0oKLzXY",
    "https://www.youtube.com/watch?v=MwmGwdfhbXE",
    "https://www.youtube.com/watch?v=AZQm-uZgyfU",
    "https://www.youtube.com/watch?v=3C_q59aBFfY",
    "https://www.youtube.com/watch?v=zFKWvOofpx8",
    "https://www.youtube.com/watch?v=OMcQzSYx02U",
    "https://www.youtube.com/watch?v=o02FT0iGuv4",
    "https://www.youtube.com/watch?v=mWP15X7B8KU",
    "https://www.youtube.com/watch?v=byKyvNgb7Lg",
    "https://www.youtube.com/watch?v=XjiRmH5-vf8",
    "https://www.youtube.com/watch?v=bbS0TLuaje8",
    "https://www.youtube.com/watch?v=IvjuaTi_AV4",
    "https://www.youtube.com/watch?v=nka7_LrANEA",
    "https://www.youtube.com/watch?v=tRuH5vpD3_Y",
    "https://www.youtube.com/watch?v=ahIFDX2SUDw",
    "https://www.youtube.com/watch?v=qmGnrDHAf1Q",
    "https://www.youtube.com/watch?v=zyS20ThcbE0",
    "https://www.youtube.com/watch?v=EvBUbGmhYT8",
    "https://www.youtube.com/watch?v=mtleXaBER0Q",
    "https://www.youtube.com/watch?v=7yjlZq9efD0",
    "https://www.youtube.com/watch?v=S6I_H71wp18",
    "https://www.youtube.com/watch?v=vRTYtUQZJSY",
    "https://www.youtube.com/watch?v=NaWKTDxScKI",
    "https://www.youtube.com/watch?v=dYGeIW4tgk0",
    "https://www.youtube.com/watch?v=vVnIZNqLJug",
    "https://www.youtube.com/watch?v=lwoNqXDPAnY",
    "https://www.youtube.com/watch?v=oLiWo1NIVBM",
    "https://www.youtube.com/watch?v=2AeCSugL400",
    "https://www.youtube.com/watch?v=a_flNhOlnqM",
    "https://www.youtube.com/watch?v=XdAZoIqre3Y",
    "https://www.youtube.com/watch?v=oVoDqnBXvnI",
    "https://www.youtube.com/watch?v=NAOcMLcqIOY",
    "https://www.youtube.com/watch?v=T9AeEaqUALY",
    "https://youtu.be/xJeGt2s-jQk",
    "https://youtu.be/ObyLOHbWZ2A",
    "https://youtu.be/PTCsZI-dO_U",
    "https://youtu.be/pWGGs9mAu_s",
    "https://youtu.be/ZTfZ96bw5kM",
    "https://youtu.be/T6n4bExSoUU",
    "https://youtu.be/l4Mkh5wmmt4",
    "https://youtu.be/qG0_9rEDvmg",
    "https://youtu.be/zCYUM3TcxI8",
    "https://youtu.be/J9MbCT1V8ZU",
    "https://youtu.be/6r5C-bHyH9I",
    "https://youtu.be/7xkzI24NwyI",
    "https://youtu.be/kEyV89c2Jf4",
    "https://youtu.be/zorHyTZO80M",
    "https://youtu.be/ifvbQ7ZgPZE",
    "https://youtu.be/gbihew_COl0",
    "https://youtu.be/gAXN8Sya80Y",
    "https://youtu.be/l00Ggg25wB8",
    "https://youtu.be/XbeUkvcDF88",
    "https://youtu.be/OOCRcEYSIAQ",
    "https://youtu.be/Zs_G-ziocEk",
    "https://youtu.be/sTL2K4_ZJho",
    "https://youtu.be/M-Jb3sCrcfI",
    "https://youtu.be/Oqjsav1RziY",
    "https://youtu.be/lm5JAcc0zs4",
    "https://youtu.be/dgV774-2cwQ",
    "https://youtu.be/2O3yGakD0jw",
    "https://youtu.be/_OxQmqLkN_0",
    "https://youtu.be/4gzbW2UgV9o",
    "https://youtu.be/nAq6LwzgYdM",
    "https://youtu.be/X_MJWwbiLXg",
    "https://youtu.be/09Xzw5YKrd0",
    "https://youtu.be/hYezCSRJOP8",
    "https://youtu.be/t1bESWQ6XOU",
    "https://youtu.be/s6p-1ovcuMM",
    "https://youtu.be/C36j-7Gp7l8",
    "https://youtu.be/1eBLjaykzBs",
    "https://youtu.be/LosyS92biU8",
    "https://youtu.be/Z_lhTQcxcbA",
    "https://youtu.be/Tecf457t5QA",
    "https://youtu.be/oevgvUTIx_A",
    "https://youtu.be/rGsbUiT8wEc",
    "https://youtu.be/n2eRNOQYc-w",
    "https://youtu.be/teX8mXnkwW8",
    "https://youtu.be/ZBQ-txXibsI",
    "https://youtu.be/xXZhjWOiwrY",
    "https://youtu.be/ZbDa6jnnnVc",
    "https://youtu.be/-TQt8BHFdlE",
    "https://youtu.be/ZM_hCaCX4OA",
    "https://youtu.be/tmuTQId7n5w",
    "https://youtu.be/fvBEtzX3GSg",
    "https://youtu.be/CIKRikWqIFQ",
    "https://youtu.be/nowm_nK0quI",
    "https://youtu.be/ETL-LtpzeA4",
    "https://youtu.be/4Ie8v5q-gR4",
    "https://youtu.be/uNLV65uampE",
]

output_dir = "downloaded_thumbnails"
os.makedirs(output_dir, exist_ok=True)

# Regex pattern to extract 11-character video IDs from standard and short URLs
pattern = r"(?:v=|\.be/)([a-zA-Z0-9_-]{11})"

# Extract and deduplicate video IDs while preserving order
extracted_ids = []
for url in urls:
    match = re.search(pattern, url)
    if match:
        video_id = match.group(1)
        if video_id not in extracted_ids:
            extracted_ids.append(video_id)

print(f"Found {len(extracted_ids)} unique video IDs to download.")

# Resolution fallback chain
qualities = ["maxresdefault.jpg", "sddefault.jpg", "hqdefault.jpg"]

for idx, vid in enumerate(extracted_ids, start=1):
    save_path = os.path.join(output_dir, f"{vid}.jpg")
    success = False

    for quality in qualities:
        img_url = f"https://img.youtube.com/vi/{vid}/{quality}"
        request = urllib.request.Request(
            img_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )

        try:
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    with open(save_path, "wb") as f:
                        f.write(response.read())
                    print(f"[{idx}/{len(extracted_ids)}] Downloaded: {vid}.jpg ({quality})")
                    success = True
                    break
        except urllib.error.HTTPError:
            continue
        except Exception as err:
            print(f"[{idx}/{len(extracted_ids)}] Error on {vid}: {err}")
            break

    if not success:
        print(f"[{idx}/{len(extracted_ids)}] Failed to download thumbnail for ID: {vid}")

print(f"\nAll downloads finished. Files are saved in: {os.path.abspath(output_dir)}")
