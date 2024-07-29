import sys
from pydub import AudioSegment
from pydub.silence import split_on_silence

def convert_to_mono_trim_silence_and_clip(wav_path, duration_minutes):
    # 加载音频文件
    sound = AudioSegment.from_wav(wav_path)
    
    # 转换为单声道
    sound_mono = sound.set_channels(1)
    
    # 分割音频，移除长时间的静音部分并保持部分静音
    chunks = split_on_silence(
        sound_mono,
        # 考虑静音的最小长度（毫秒）
        min_silence_len=500,
        # 静音阈值（dBFS）
        silence_thresh=sound_mono.dBFS-16,
        # 保留静音时间不超过0.5秒
        keep_silence=500
    )

    # 连接处理后的音频块
    processed_sound = sum(chunks)

    # 裁剪音频至指定长度，如果音频长度小于指定长度，则保留整个音频
    duration_ms = duration_minutes * 60 * 1000  # 将分钟转换为毫秒
    if len(processed_sound) > duration_ms:
        processed_sound = processed_sound[:duration_ms]

    # 导出处理后的音频文件，直接覆盖原文件
    processed_sound.export(wav_path, format="wav")
    
    return wav_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <path_to_wav> <duration_in_minutes>")
        sys.exit(1)
    
    input_wav_path = sys.argv[1]
    duration_minutes = float(sys.argv[2])
    convert_to_mono_trim_silence_and_clip(input_wav_path, duration_minutes)
    print(f"音频已处理并保存至: {input_wav_path}")
