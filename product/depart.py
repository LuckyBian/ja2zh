import os
import sys
import subprocess

def convert_video(folder_path, video_output_path, audio_output_path):
    # 检测文件夹中的视频文件
    video_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    if not video_files:
        print("No video files found in the specified directory.")
        return

    # 假设文件夹中只有一个视频文件
    video_file = os.path.join(folder_path, video_files[0])

    # 定义转换为mp4的路径
    temp_video_path = os.path.join(folder_path, "temp_video.mp4")

    # 转换视频为mp4格式
    subprocess.run(['ffmpeg', '-i', video_file, '-vcodec', 'copy', '-acodec', 'copy', temp_video_path])

    # 分离无声视频
    subprocess.run(['ffmpeg', '-i', temp_video_path, '-an', '-vcodec', 'copy', video_output_path])

    # 提取音频并转换为WAV格式
    subprocess.run(['ffmpeg', '-i', temp_video_path, '-vn', '-acodec', 'pcm_s16le', audio_output_path])

    # 删除临时文件
    os.remove(temp_video_path)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <folder_path> <video_output_path> <audio_output_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    video_output_path = sys.argv[2]
    audio_output_path = sys.argv[3]

    convert_video(folder_path, video_output_path, audio_output_path)
