from pydub import AudioSegment

def get_audio_duration_ms(audio_path):
    # 加载音频文件
    audio_segment = AudioSegment.from_file(audio_path)
    
    # 获取音频时长（毫秒）
    duration_ms = len(audio_segment)
    
    return duration_ms

# 示例使用
audio_path = '/home/weizhenbian/ja2zh/product/output/segment_110.wav'  # 更改为你的音频文件路径
duration = get_audio_duration_ms(audio_path)
print(f"音频时长为：{duration} 毫秒")
