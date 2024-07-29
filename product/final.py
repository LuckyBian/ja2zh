import os
import sys
import subprocess
from pydub import AudioSegment

def get_audio_file_list(folder_path):
    files = sorted(os.listdir(folder_path), key=lambda x: int(x.split('_')[1].split('.')[0]))
    return [os.path.join(folder_path, f) for f in files if f.endswith('.wav')]

def concatenate_audios(audio_files):
    combined = AudioSegment.empty()
    for file in audio_files:
        audio = AudioSegment.from_wav(file)
        combined += audio
    return combined

def overlay_audio(main_audio, bgm_audio):
    combined = main_audio.overlay(bgm_audio, loop=True)
    return combined

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <audio_folder> <bgm_file> <video_file> <output_file>")
        sys.exit(1)

    audio_folder = sys.argv[1]
    bgm_file = sys.argv[2]
    video_file = sys.argv[3]
    output_file = sys.argv[4]
    
    # Step 1: Get list of audio files and concatenate them
    audio_files = get_audio_file_list(audio_folder)
    concatenated_audio = concatenate_audios(audio_files)
    
    # Step 2: Load BGM and overlay with concatenated audio
    bgm_audio = AudioSegment.from_wav(bgm_file)
    final_audio = overlay_audio(concatenated_audio, bgm_audio)
    
    # Step 3: Export final audio to a file
    final_audio_file = "final_audio.wav"
    final_audio.export(final_audio_file, format="wav")
    
    # Step 4: Use ffmpeg to merge final audio with video
    print(f"Merging audio {final_audio_file} with video {video_file} into {output_file} using ffmpeg")
    subprocess.run([
        'ffmpeg', '-i', video_file, '-i', final_audio_file, 
        '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', output_file
    ])
    
    print(f"Final video saved as {output_file}")
