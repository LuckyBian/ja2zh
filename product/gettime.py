import os
from pydub import AudioSegment, silence

def process_audio_files(list_file, output_list_file):
    # 打开输出文件，准备写入
    with open(output_list_file, 'w', encoding='utf-8') as outfile:
        # 读取原始list文件
        with open(list_file, 'r', encoding='utf-8') as infile:
            for line in infile:
                parts = line.strip().split('|')
                if len(parts) < 2:
                    continue  # 如果行不正确就跳过

                audio_path, text = parts
                if not os.path.exists(audio_path):
                    print(f"File not found: {audio_path}")
                    continue

                # 载入音频文件
                audio = AudioSegment.from_wav(audio_path)

                # 使用低阈值检测声音
                nonsilences = silence.detect_nonsilent(audio, min_silence_len=1, silence_thresh=-60)

                if nonsilences:
                    # 获取有效音频的起始和结束时间
                    start_ms = nonsilences[0][0]  # 第一个非静音部分的开始时间
                    end_ms = nonsilences[-1][1]   # 最后一个非静音部分的结束时间
                    # 写入新的list文件，包括开始和结束时间
                    outfile.write(f"{audio_path}|{text}|{start_ms}|{end_ms}\n")
                else:
                    # 如果没有检测到有效的非静音部分，写入-1作为标记
                    outfile.write(f"{audio_path}|{text}|-1|-1\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Process .list file to append start and end times of audio segments.")
    parser.add_argument("list_file", type=str, help="The path to the input .list file containing audio paths and text.")
    parser.add_argument("output_list_file", type=str, help="The path to the output .list file where results will be saved.")

    args = parser.parse_args()

    process_audio_files(args.list_file, args.output_list_file)
