import os
import tempfile
import re
import requests
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
    """פונקציה שמחלצת את מזהה הסרטון מהקישור"""
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    if match:
        return match.group(1)
    return None

@app.route('/')
def home():
    # הצגת הדף הראשי
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    raw_url = request.form.get('url')
    if not raw_url:
        return "אנא ספק קישור תקין", 400

    video_id = clean_youtube_url(raw_url)
    if not video_id:
        return "קישור לא תקין", 400

    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, f"{video_id}.mp4")

    # ניסיון להורדה דרך שרת API עוקף חסימות
    try:
        invidious_instances = [
            'https://invidious.nerdvpn.de',
            'https://inv.us.projectsegfau.lt',
            'https://invidious.flokinet.to'
        ]
        
        download_success = False
        for instance in invidious_instances:
            api_url = f"{instance}/api/v1/videos/{video_id}"
            res = requests.get(api_url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                format_url = None
                for fmt in data.get('formatStreams', []):
                    if fmt.get('container') == 'mp4':
                        format_url = fmt.get('url')
                        break
                
                if format_url:
                    video_res = requests.get(format_url, stream=True, timeout=15)
                    with open(output_path, 'wb') as f:
                        for chunk in video_res.iter_content(chunk_size=1024*1024):
                            if chunk:
                                f.write(chunk)
                    download_success = True
                    break
                    
        if download_success and os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, download_name=f"video_{video_id}.mp4")

    except Exception:
        pass  # אם ה-API לא זמין, ממשיכים ל-yt-dlp

    # גיבוי: ניסיון הורדה בעזרת yt-dlp
    ydl_opts = {
        'format': 'b[ext=mp4]/b',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['tvhtml5'],
            }
        },
    }

    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"ארעה שגיאה בזמן ההורדה: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
