import os
import tempfile
import re
from flask import Flask, request, render_template_string, send_file
import yt_dlp

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
        .status { margin-top: 15px; color: #555; font-size: 14px; }
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
        <div class="status">המערכת מעבדת את הקובץ ישירות</div>
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

    try:
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"{video_id}.mp4")

        ydl_opts = {
            'format': 'b[ext=mp4]/best[ext=mp4]/b',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([full_yt_url])

        if os.path.exists(output_path):
            return send_file(output_path, as_attachment=True, download_name=f"video_{video_id}.mp4")
        else:
            return "שגיאה: הקובץ לא נוצר בהצלחה.", 500

    except Exception as e:
        return f"שגיאה בהורדת הסרטון מהשרת: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
