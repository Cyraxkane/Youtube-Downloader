🎬 YouTube Downloader Web Application 🚀

A full-featured web app for downloading YouTube videos as MP4 🎥 or extracting audio as MP3 🎧 — with real-time progress tracking and a voucher system for asynchronous downloads!

👨‍💻 Developed by: CyraxKane
👥 Developer Team: BitRebel
✨ Features

✅ Easy-to-use web interface – No technical knowledge needed
📹 Multiple format options – Download as MP4 (video) or MP3 (audio)
📐 Quality selection – Choose video (480p/720p/1080p) or audio (128k/192k/256k)
🎟️ Voucher system – Unique code to check download status later
⏱️ Real-time progress tracking – Live updates on your downloads
📱 Mobile-responsive design – Works on desktop, tablet, and mobile
🛠️ Admin dashboard – Monitor and manage downloads with stats
🔁 Robust error handling – Automatic retries for failed downloads
🧰 Installation
📋 Prerequisites

    🐍 Python 3.8+

    📦 pip (Python package installer)

    📹 yt-dlp

    🎵 ffmpeg (for audio conversion)

📦 Setup

git clone https://github.com/yourusername/youtube-downloader.git
cd youtube-downloader

Create a virtual environment:

python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Install ffmpeg:

    Ubuntu/Debian: sudo apt-get install ffmpeg

    macOS: brew install ffmpeg

    Windows: Download from ffmpeg.org and add to PATH

Configure the app:

cp config.example.py config.py

Edit config.py to set your download directory and other settings.

Create required directories:

mkdir downloads logs

▶️ Usage
🔌 Start the Server

Activate the virtual environment:

source env/bin/activate  # Windows: env\Scripts\activate

Run the app:

python app.py

Visit in browser: http://localhost:5000
📥 Downloading a Video

    Paste a YouTube URL 🔗

    Choose format: MP4 🎞️ or MP3 🎧

    Pick the quality you want 📐

    Click Download ⬇️

    Save your voucher code 🎟️ for later!

🕵️ Check Download Status

    Enter your voucher code on the home page

    Click Check Status

    View download progress or download the finished file 📂

🛡️ Admin Dashboard

    Go to: http://localhost:5000/admin?key=admin123

    Change the key in config.py for security 🔐

    View and filter downloads, check stats 📊

⚙️ Configuration Options

Edit config.py to customize:
Setting	Description
DOWNLOAD_DIR	Where downloaded files are stored
VOUCHER_LOG	Path to voucher logs
DETAILED_LOG	Path for admin-level logging
MAX_DOWNLOADS_PER_IP	Anti-abuse limit
ADMIN_PASSWORD	Protects admin dashboard
🚀 Deployment
Using Gunicorn (Production)

Install:

pip install gunicorn

Run:

gunicorn -w 4 -b 0.0.0.0:8000 app:app

Using Nginx as Reverse Proxy

Install Nginx:

sudo apt-get install nginx

Example config:

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

Enable and restart:

sudo ln -s /etc/nginx/sites-available/youtube-downloader /etc/nginx/sites-enabled/
sudo systemctl restart nginx

🛠️ Troubleshooting
Common Issues

    ❌ Download fails: Update yt-dlp

pip install --upgrade yt-dlp

    ❌ Audio conversion fails: Check ffmpeg install

ffmpeg -version

    ❌ Permission errors: Ensure app can write to downloads/ and logs/

    ❌ App won’t start: Check for port conflicts or missing packages

Logs

    App logs: app.log

    Download errors: download_errors.log

🤝 Contributing

    Fork the repo

    Create a feature branch:

git checkout -b feature-name

    Commit your changes:

git commit -m "Add some feature"

    Push and open a pull request

🪪 License

MIT License – see LICENSE for details.
🙌 Acknowledgements

    🛠️ yt-dlp – for powerful downloading

    🌐 Flask – for backend magic

    🎨 Bootstrap – for responsive UI

⚠️ Disclaimer

This app is intended for downloading videos you have the right to download.
Please respect copyright laws and YouTube’s Terms of Service.
The developers are not responsible for misuse of this tool.
