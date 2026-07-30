import os
import tempfile
from flask import Flask, request, render_template_string, send_file
import yt_dlp

app = Flask(__name__)

# דף הבית - ממשק בעברית להזנת קישור
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
        input[type="text"] { width: 300px; padding: 10px; margin: 10px; border: 1px solid #ccc; border-radius: 5px; }
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
    # הצגת ממשק המשתמש
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    # קבלת הקישור שהזין המשתמש
    video_url = request.form.get('url')
    if not video_url:
        return "אנא ספק קישור תקין", 400

    # יצירת תיקייה זמנית לשמירת הקובץ בשרת
    temp_dir = tempfile.mkdtemp()
    
    # הגדרות עבור yt-dlp להורדת הסרטון
    ydl_opts = {
        'format': 'best',  # הורדת האיכות הטובה ביותר הזמינה
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
        # שליחת הקובץ בחזרה אל המשתמש
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"ארעה שגיאה בזמן ההורדה: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
