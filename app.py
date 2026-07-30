import os
import tempfile
import re
import requests
from flask import Flask, request, render_template_string, send_file

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
    """חילוץ וניקוי הקישור מיוטיוב"""
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    raw_url = request.form.get('url')
    if not raw_url:
        return "אנא ספק קישור תקין", 400

    clean_url = clean_youtube_url(raw_url)
    cobalt_api = "https://api.cobalt.tools"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    payload = {
        "url": clean_url,
        "videoQuality": "720"
    }

    try:
        response = requests.post(cobalt_api, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            download_url = data.get("url")
            
            if download_url:
                file_res = requests.get(download_url, stream=True, timeout=60)
                temp_dir = tempfile.mkdtemp()
                output_path = os.path.join(temp_dir, "video.mp4")

                with open(output_path, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

                return send_file(output_path, as_attachment=True, download_name="video.mp4")
            else:
                return "לא ניתן היה לקבל קישור להורדה עבור סרטון זה.", 400
        else:
            return f"שגיאה בעבודת השרת המעבד (קוד: {response.status_code})", 500

    except requests.exceptions.RequestException as e:
        return f"שגיאת תקשורת מול שרת ההורדות: {str(e)}", 500
    except Exception as e:
        return f"ארעה שגיאה בלתי צפויה: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
