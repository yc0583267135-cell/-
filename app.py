import os
import tempfile
import re
from flask import Flask, request, render_template_string, send_file
import yt_dlp

app = Flask(__name__)

# ממשק משתמש ב-HTML בעברית
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>מוריד הסרטונים מ-YouTube</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; }
        .container { background: white; padding: 30px; border-radius: 10px; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        input[type="text"] { width: 320px; padding: 10px; margin: 10px; border: 1px solid #ccc; border-radius: 5px; }
        button { padding: 10px 20px; background-color: #ff0000; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #cc0000; }
    </style>
</head>
<body>
    <div class="container">
        <h2>מוריד סרטוני YouTube</h2>
        <form action="/download" method="post">
            <input type="text" name="url" placeholder="הדבק קישור ליוטיוב כאן..." required>
            <br>
            <button type="submit">הורד סרטון</button>
        </form>
    </div>
</body>
</html>
'''

def clean_youtube_url(url):
    """פונקציה שמנקה פרמטרים מיותרים מקישור יוטיוב"""
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/watch?v={video_id}'
    return url

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    raw_url = request.form.get('url')
    if not raw_url:
        return "אנא ספק קישור תקין", 400

    video_url = clean_youtube_url(raw_url)
    temp_dir = tempfile.mkdtemp()
    
    # הגדרות לעקיפת מנגנון עקוף בוטים (Sign in to confirm you're not a bot)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'noplaylist': True,
        # שימוש בלקוחות המדמים טלוויזיות/VR לעקיפת אימות הבוטים
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr', 'tv_embedded', 'ios'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"ארעה שגיאה בזמן ההורדה: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
