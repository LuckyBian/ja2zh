import sys
import wave
import contextlib

def process_audio_list(file_path):
    # 读取原始文件并准备写入新内容
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 处理每一行
    new_lines = []
    for line in lines:
        parts = line.strip().split('|')  # 按 '|' 分割每一行
        audio_path = parts[0]  # 音频文件的路径

        # 使用 wave 库读取音频文件的总时长
        try:
            with contextlib.closing(wave.open(audio_path, 'r')) as audio:
                frames = audio.getnframes()
                rate = audio.getframerate()
                duration = (frames / float(rate)) * 1000  # 计算时长（毫秒）
        except wave.Error as e:
            duration = 0  # 如果文件无法读取，设置时长为0

        # 将时长追加到行末
        new_line = f"{line.strip()}|{duration:.0f}\n"  # 毫秒不需要小数点
        new_lines.append(new_line)

    # 将修改后的内容写入新文件
    output_file_path = file_path.replace('.txt', '_updated.txt')
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        outfile.writelines(new_lines)
    print(f"Updated file has been saved as {output_file_path}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_list_file>")
    else:
        process_audio_list(sys.argv[1])
