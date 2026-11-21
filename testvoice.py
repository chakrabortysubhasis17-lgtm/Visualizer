import sys
import asyncio
import edge_tts

VOICE = "en-US-ChristopherNeural"
OUTPUT_FILE = "test.mp3"


async def generate_test_audio(text: str, output_file: str = OUTPUT_FILE):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        pitch="-2Hz",
        rate="+0%"
    )
    await communicate.save(output_file)
    print(f"[OK] Saved '{output_file}' using {VOICE}")


def main():
    if len(sys.argv) > 1:
        sentence = " ".join(sys.argv[1:]).strip()
    else:
        sentence = input("Enter a sentence: ").strip()

    if not sentence:
        print("No sentence provided. Exiting.")
        return

    asyncio.run(generate_test_audio(sentence))


if __name__ == "__main__":
    main()