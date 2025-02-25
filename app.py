from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import re
import uuid

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
app.config['UPLOAD_FOLDER'] = 'downloads'

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        
        if not url.startswith(('https://www.youtube.com/', 'https://youtu.be/')):
            return render_template('index.html', error="Invalid YouTube link!")

        
        unique_id = str(uuid.uuid4())[:8]
        output_template = os.path.join(app.config['UPLOAD_FOLDER'], f'%(title)s_{unique_id}.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'quiet': True
        }

        try:
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                temp_filename = ydl.prepare_filename(info)
                base, ext = os.path.splitext(temp_filename)
                final_filename = f"{base}.mp3"
                safe_filename = sanitize_filename(os.path.basename(final_filename))

           
            if not os.path.exists(final_filename):
                raise FileNotFoundError("The created MP3 file could not be found!")

            response = send_file(
                final_filename,
                as_attachment=True,
                download_name=safe_filename,
                mimetype='audio/mpeg'
            )

           
            @response.call_on_close
            def remove_file():
                try:
                    os.remove(final_filename)
                except:
                    pass

            return response

        except Exception as e:
            return render_template('index.html', error=f"Error: {str(e)}")
    
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    app.run(host='0.0.0.0', port=5000, debug=False)
