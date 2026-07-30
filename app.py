import os
import tempfile
from flask import Flask, request, render_template_string, send_file
import yt_dlp

# אתחול אפליקציית Flask
app = Flask(__name__)

# דף הבית - ממשק משתמש ב-HTML בעברית
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

@app.route('/')
def home():
    # נתיב ראשי - הצגת טופס ההורדה למשתמש
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    # קבלת הקישור שהזין המשתמש בטופס
    video_url = request.form.get('url')
    if not video_url:
        return "אנא ספק קישור תקין", 400

    # יצירת תיקייה זמנית לשמירת הקובץ בשרת לפני שליחתו
    temp_dir = tempfile.mkdtemp()
    
    # הגדרות מתקדמות עבור yt-dlp לעקיפת חסימות HTTP 403 בשרתי ענן
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        # הגדרת לקוחות Android ו-Web לעקיפת מגבלות יוטיוב
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
            }
        },
        # הגדרת User-Agent של מכשיר נייד
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        }
    }

    try:
        # ביצוע ההורדה מיוטיוב
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
        # שליחת הקובץ בחזרה לדפדפן של המשתמש
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"ארעה שגיאה בזמן ההורדה: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
