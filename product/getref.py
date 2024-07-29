import os
import sys
import librosa

def filter_audio(file_path):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 遍历每一行，检查音频时长
    new_lines = []
    for line in lines:
        parts = line.strip().split('|')
        audio_path = parts[0]
        japanese_text = parts[3]

        # 检测音频时长
        duration = librosa.get_duration(filename=audio_path)
        
        # 时长在6到10秒之间，修改行格式并添加到新列表
        if 6 < duration < 10:
            new_lines.append(f"{audio_path}|{japanese_text}\n")
            break
    
    # 重写文件，只保留满足条件的行
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_lines)

if __name__ == "__main__":
    # 从命令行参数获取文件路径
    if len(sys.argv) < 2:
        print("Usage: python script.py path_to_your_file.list")
        sys.exit(1)

    file_path = sys.argv[1]
    filter_audio(file_path)
