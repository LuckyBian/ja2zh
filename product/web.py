from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

audio_dir = '/home/weizhenbian/ja2zh/product/output'
video_path = '/home/weizhenbian/ja2zh/product/nonwav_video/nonwav.mp4'

@app.route('/')
def index():
    audio_files = sorted([f for f in os.listdir(audio_dir) if f.endswith('.wav')])
    total_audio_files = len(audio_files)
    return render_template('index.html', total_audio_files=total_audio_files, video_file=video_path)

@app.route('/audio/<filename>')
def audio(filename):
    return send_from_directory(audio_dir, filename)

@app.route('/video')
def video():
    return send_from_directory(os.path.dirname(video_path), os.path.basename(video_path))

if __name__ == '__main__':
    app.run(debug=True)
