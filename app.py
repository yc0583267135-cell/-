import re
import requests
from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

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

    # רשימת שרתי API ציבוריים חיצוניים להמרת קישורים בענן
    api_endpoints = [
        "https://api.cobalt.tools",
        "https://co.wuk.sh"
    ]

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    payload = {
        "url": full_yt_url,
        "videoQuality": "720"
    }

    for endpoint in api_endpoints:
        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                download_url = data.get("url") or data.get("picker", [{}])[0].get("url")
                if download_url:
                    return redirect(download_url)
        except Exception:
            continue

    return "שגיאה: השרתים החיצוניים חסומים כרגע לגישה מענן. נסה שוב מאוחר יותר.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
