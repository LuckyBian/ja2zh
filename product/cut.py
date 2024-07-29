import os
import argparse
from pydub import AudioSegment, silence

def main(input_file, output_dir):
    # 载入音频文件
    audio = AudioSegment.from_wav(input_file)

    # 将音频转换为单声道
    mono_audio = audio.set_channels(1)
    mono_audio.export(input_file, format="wav")  # 直接覆盖原文件

    # 设置静默阈值和静默最小长度
    silence_thresh = -50  # 静默的分贝阈值
    min_silence_len = 1000  # 静默的最小长度（毫秒）

    # 检测音频中的静默部分
    silences = silence.detect_silence(mono_audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    silences = [(0, 0)] + silences + [(len(mono_audio), len(mono_audio))]  # 包括音频的开始和结束

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 用于保存切割点的列表，包括音频的起始和结束点
    cut_points = [0]  # 开始添加音频的起始点

    # 计算每个静音区间的中点作为切割点
    for silence_start, silence_end in silences:
        mid_point = (silence_start + silence_end) // 2
        cut_points.append(mid_point)

    # 切割音频并导出
    segments = [mono_audio[cut_points[i]:cut_points[i + 1]] for i in range(len(cut_points) - 1)]

    # 前三段拼接
    if len(segments) >= 3:
        combined_start_segments = segments[0] + segments[1] + segments[2]
        segments = [combined_start_segments] + segments[3:]

    # 后三段拼接
    if len(segments) >= 3:
        combined_end_segments = segments[-3] + segments[-2] + segments[-1]
        segments = segments[:-3] + [combined_end_segments]

    # 导出每个segment
    for i, segment in enumerate(segments):
        segment.export(os.path.join(output_dir, f"segment_{i + 1}.wav"), format="wav")

    # 打印信息
    print(f"Total segments created: {len(segments)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert to mono and split an audio file into segments based on silences longer than 1 second, including initial and final parts.")
    parser.add_argument("input_file", type=str, help="The path to the input WAV file.")
    parser.add_argument("output_dir", type=str, help="The directory where the output files will be saved.")

    args = parser.parse_args()

    main(args.input_file, args.output_dir)
