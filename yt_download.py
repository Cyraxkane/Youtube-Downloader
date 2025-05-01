# yt_download.py
# Developed by CyraxKane – Team BitRebel
# A script to download videos or playlists as MP3 or MP4 using yt-dlp

import os
import yt_dlp

def download_content(url, format_choice):
    # Set options based on user format
    if format_choice.lower() == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'audio_format': 'mp3',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif format_choice.lower() == 'mp4':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': '%(title)s.%(ext)s'
        }
    else:
        print("Invalid format. Please enter 'mp3' or 'mp4'.")
        return

    # Download using yt_dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([url])
            print("Download complete.")
        except Exception as e:
            print(f"An error occurred: {e}")
            
def main():
    print("=== Album/Video Downloader ===")
    url = input("Enter the video or playlist URL: ").strip()
    format_choice = input("Choose format (mp3/mp4): ").strip()
    download_content(url, format_choice)

if __name__ == '__main__':
    main()
