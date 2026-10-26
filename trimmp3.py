import os
from pydub import AudioSegment


def trim_mp3_files(source_folder, max_duration_sec=5):
    # 1. Setup the output folder path with the same name + '_trimmed' suffix
    # to avoid overwriting the original directory structure
    folder_name = os.path.basename(os.path.normpath(source_folder))
    parent_dir = os.path.dirname(os.path.normpath(source_folder))
    output_folder = os.path.join(parent_dir, f"{folder_name}_trimmed")

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Convert maximum duration to milliseconds (pydub operates in ms)
    max_duration_ms = max_duration_sec * 1000

    # 2. Iterate through all files in the source folder
    for file_name in os.listdir(source_folder):
        if file_name.lower().endswith(".mp3"):
            source_file_path = os.path.join(source_folder, file_name)
            output_file_path = os.path.join(output_folder, file_name)

            try:
                # Load the audio file
                audio = AudioSegment.from_mp3(source_file_path)

                # Check if the file is longer than the target duration
                if len(audio) > max_duration_ms:
                    # Slice the audio to the first 5 seconds
                    trimmed_audio = audio[:max_duration_ms]
                    # Export the modified file to the new folder
                    trimmed_audio.export(output_file_path, format="mp3")
                    print(f"Trimmed: {file_name}")
                else:
                    # If it's less than 5 seconds, leave it as is and copy/save it
                    audio.export(output_file_path, format="mp3")
                    print(f"Left as is (under 5s): {file_name}")

            except Exception as e:
                print(f"Error processing {file_name}: {e}")


# Example usage:
# Replace 'path/to/your/folder' with your actual target folder path
source_directory = "assets/sfx"
trim_mp3_files(source_directory)
