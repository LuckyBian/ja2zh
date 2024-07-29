import subprocess
import os
from pydub import AudioSegment
import numpy as np

def remove_silence_from_ends(audio_segment, silence_thresh=-40, min_silence_len=0.5):
    """
    只去除音频开头和结尾的静音，不考虑静音的长度。
    """
    start_trim = detect_leading_silence(audio_segment, silence_thresh, min_silence_len)
    end_trim = detect_leading_silence(audio_segment.reverse(), silence_thresh, min_silence_len)
    trimmed_audio = audio_segment[start_trim:len(audio_segment)-end_trim]
    return trimmed_audio

def detect_leading_silence(sound, silence_threshold=-40.0, chunk_size=10):
    """
    测量音频开头的静音长度，即使是极短的静音也算。
    """
    trim_ms = 0
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size
    return trim_ms

def remove_middle_silence(audio_segment, silence_thresh=-40, min_silence_len=700):
    """
    去除音频中间的部分静音。
    """
    non_silent_chunks = [chunk for chunk in audio_segment if chunk.dBFS > silence_thresh]
    silent_durations = [len(chunk) for chunk in audio_segment if chunk.dBFS <= silence_thresh]

    total_silence_duration = sum(silent_durations)
    reduced_silence_duration = total_silence_duration // 3  # 保留 1/3 的静音
    reduced_audio = AudioSegment.empty()

    current_silence = 0
    for chunk in audio_segment:
        if chunk.dBFS > silence_thresh:
            reduced_audio += chunk
        else:
            if current_silence < reduced_silence_duration:
                reduced_audio += chunk
                current_silence += len(chunk)

    return reduced_audio

def add_silence(audio_segment, start_ms, total_duration_ms):
    """
    给音频前后添加适量的静音，确保音频从start_ms开始，总时长为total_duration_ms。
    """
    silence_before = AudioSegment.silent(duration=start_ms)
    silence_after = AudioSegment.silent(duration=total_duration_ms - len(audio_segment) - start_ms)
    return silence_before + audio_segment + silence_after

# 读取cut.list文件以获取参考wav路径和提示文本
ref_wav_path = ""
prompt_text = ""
list_file2 = 'product/text/cut.list'
with open(list_file2, 'r') as file:
    for line in file:
        parts = line.strip().split('|')
        ref_wav_path = parts[0]
        prompt_text = parts[1]
        break  # 假设只需要读取第一行

# 读取cut3.list文件以获取音频处理参数
list_file = 'product/text/cut3.list'
with open(list_file, 'r') as file:
    lines = file.readlines()

# 遍历每行数据进行音频处理
for line in lines:
    parts = line.strip().split('|')
    audio_path = parts[0]
    text = parts[1]
    start_ms = int(parts[2])
    ideal_end_ms = int(parts[3])
    max_end_ms = int(parts[4])
    output_path = f"product/output/{os.path.basename(audio_path)}"

    attempts = 0
    while attempts < 5:
        # 运行推理脚本生成音频
        command = [
            'python', 'inf/inf.py',
            '--output_path', output_path,
            '--prompt_text', prompt_text,
            '--ref_wav_path', ref_wav_path,
            '--text', text
        ]
        subprocess.run(command)

        # 去除开头和结尾的静音
        audio = AudioSegment.from_file(output_path)
        processed_audio = remove_silence_from_ends(audio)

        # 检查音频时长是否符合要求
        min_duration = (ideal_end_ms - start_ms) / 2
        max_duration = max_end_ms - start_ms
        actual_duration = len(processed_audio)

        if not (min_duration <= actual_duration <= max_duration):
            print(f"音频 {output_path} 第 {attempts+1} 次不合格，重新生成...")
            attempts += 1
            if attempts < 5:
                # 去除中间部分静音
                processed_audio = remove_middle_silence(audio)
                actual_duration = len(processed_audio)

                if min_duration <= actual_duration <= max_duration:
                    break

            if attempts == 5:
                # 达到最大尝试次数，使用最后一次的结果
                print(f"音频 {output_path} 重试已达最大次数，将使用最后一次生成的音频。")
        else:
            break

    # 给音频前后添加静音
    final_audio = add_silence(processed_audio, start_ms, max_end_ms)
    final_audio.export(output_path, format="wav")

print("所有音频处理完成。")
