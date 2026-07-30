import os
import tempfile
import re
import requests
from flask import Flask, request, render_template_string, send_file, redirect

app = Flask(__name__)

# ממשק משתמש
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
        input[type="text"] { width: 340px; padding: 10px; margin: 10px; border: 1px solid #ccc; border-radius: 5px; }
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

def extract_video_id(url):
    """חילוץ מזהה הסרטון (11 תווים)"""
    match = re.search(r'(?:v=|\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})', url)
    if match:
        return match.group(1)
    return None

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    raw_url = request.form.get('url', '').strip()
    video_id = extract_video_id(raw_url)

    if not video_id:
        return "קישור YouTube לא תקין. אנא בדוק את הקישור ונסה שוב.", 400

    full_yt_url = f"https://www.youtube.com/watch?v={video_id}"

    # === ניסיון 1: Cobalt API מעודכן ===
    try:
        cobalt_res = requests.post(
            "https://api.cobalt.tools",
            json={"url": full_yt_url, "videoQuality": "720"},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=8
        )
        if cobalt_res.status_code == 200:
            download_url = cobalt_res.json().get("url")
            if download_url:
                return redirect(download_url)
    except Exception:
        pass  # מעבר שקט לשיטה הבאה במקרה של כישלון

    # === ניסיון 2: Invidious Instances (רשת שרתים עוקפת חסימות) ===
    invidious_servers = [
        "https://invidious.nerdvpn.de",
        "https://inv.us.projectsegfau.lt",
        "https://invidious.flokinet.to",
        "https://invidious.privacydev.net"
    ]

    for server in invidious_servers:
        try:
            api_url = f"{server}/api/v1/videos/{video_id}"
            res = requests.get(api_url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                formats = data.get("formatStreams", [])
                for fmt in formats:
                    if fmt.get("container") == "mp4" and fmt.get("url"):
                        return redirect(fmt["url"])
        except Exception:
            continue

    # === ניסיון 3: yt-dlp מקומי עם עקיפת Android Client ===
    try:
        import yt_dlp
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{video_id}.mp4")

        ydl_opts = {
            'format': 'b[ext=mp4]/best[ext=mp4]/b',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([full_yt_url])

        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, download_name=f"video_{video_id}.mp4")

    except Exception as e:
        last_error = str(e)

    return f"לא ניתן היה לחלץ את הסרטון דרך אף אחד משרתי הגיבוי. (שגיאה: {last_error if 'last_error' in locals() else 'כל השרתים עמוסים'})", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
