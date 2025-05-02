import os
import time
import threading
import subprocess
import json
import logging
import re
from datetime import datetime

from config import DOWNLOAD_DIR, VOUCHER_LOG
from utils.voucher import update_voucher_status, get_voucher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='download_errors.log'
)
logger = logging.getLogger('downloader')

def get_file_size_mb(file_path):
    """Get file size in MB"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path) / (1024 * 1024)  # Convert bytes to MB
    return 0

def download_video(voucher_code, youtube_url, format_type, quality, ip_address=None):
    """Download video in a separate thread with retry logic"""
    thread = threading.Thread(
        target=_download_with_retry,
        args=(voucher_code, youtube_url, format_type, quality, ip_address)
    )
    thread.daemon = True
    thread.start()
    return thread

def _download_with_retry(voucher_code, youtube_url, format_type, quality, ip_address=None, max_retries=5, retry_delay=10):
    """Download video with retry logic"""
    retries = 0
    success = False
    
    while retries < max_retries and not success:
        try:
            if retries > 0:
                logger.info(f"Retry attempt {retries} for voucher {voucher_code}")
                # Check if voucher still exists before retrying
                voucher = get_voucher(voucher_code)
                if not voucher or voucher.get('status') == 'deleted':
                    logger.info(f"Voucher {voucher_code} was deleted, cancelling download")
                    return
                
                # Update status to show we're retrying
                update_voucher_status(
                    voucher_code, 
                    'processing', 
                    error_message=f"Retrying download (attempt {retries}/{max_retries})...",
                    progress=0
                )
                
                # Wait before retrying
                time.sleep(retry_delay)
            
            # Perform the download
            success = _perform_download(voucher_code, youtube_url, format_type, quality, ip_address)
            
        except Exception as e:
            logger.error(f"Error downloading {youtube_url} for voucher {voucher_code}: {str(e)}")
            retries += 1
            
            if retries >= max_retries:
                # Update voucher status to failed after max retries
                update_voucher_status(
                    voucher_code, 
                    'failed', 
                    error_message=f"Failed after {max_retries} attempts: {str(e)}"
                )
                logger.error(f"Max retries reached for voucher {voucher_code}")

def _perform_download(voucher_code, youtube_url, format_type, quality, ip_address=None):
    """Perform the actual download with yt-dlp"""
    try:
        # Create output filename based on voucher code
        output_template = os.path.join(DOWNLOAD_DIR, f"{voucher_code}.%(ext)s")
        
        # Prepare yt-dlp command based on format type
        if format_type == 'mp3':
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', quality,
                '-o', output_template,
                '--no-playlist',
                '--progress',  # Add progress output
                youtube_url
            ]
            expected_ext = 'mp3'
        else:  # mp4
            # For mp4, we need to select the appropriate video quality
            if quality == '1080p':
                format_code = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            elif quality == '720p':
                format_code = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == '480p':
                format_code = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            else:
                format_code = 'bestvideo+bestaudio/best'
            
            cmd = [
                'yt-dlp',
                '-f', format_code,
                '--merge-output-format', 'mp4',
                '-o', output_template,
                '--no-playlist',
                '--socket-timeout', '30',  # Add timeout to prevent hanging
                '--retries', '3',          # yt-dlp's internal retry mechanism
                '--progress',              # Add progress output
                youtube_url
            ]
            expected_ext = 'mp4'
        
        # Update voucher status to processing
        update_voucher_status(voucher_code, 'processing', progress=0)
        
        # Execute the command
        logger.info(f"Starting download for voucher {voucher_code}: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout to capture all output
            universal_newlines=True,
            bufsize=1  # Line buffered
        )
        
        # Process output line by line to extract progress
        for line in iter(process.stdout.readline, ''):
            # Parse progress information
            progress = parse_progress(line)
            if progress is not None:
                # Update voucher with progress
                update_voucher_status(voucher_code, 'processing', progress=progress)
            
            # Log the output
            logger.debug(line.strip())
        
        # Wait for process to complete
        process.wait()
        
        # Check if the process was successful
        if process.returncode != 0:
            logger.error(f"yt-dlp error for voucher {voucher_code}, return code: {process.returncode}")
            update_voucher_status(
                voucher_code, 
                'failed', 
                error_message=f"Download failed with return code {process.returncode}"
            )
            return False
        
        # Check if the file exists
        expected_file = os.path.join(DOWNLOAD_DIR, f"{voucher_code}.{expected_ext}")
        if not os.path.exists(expected_file):
            logger.error(f"File not found after download: {expected_file}")
            update_voucher_status(
                voucher_code, 
                'failed', 
                error_message="File not found after download"
            )
            return False
        
        # Get file size
        file_size = get_file_size_mb(expected_file)
        
        # Update voucher status to complete
        update_voucher_status(
            voucher_code, 
            'complete', 
            file_path=expected_file,
            file_size=file_size,
            progress=100  # Set progress to 100% when complete
        )
        
        logger.info(f"Download completed successfully for voucher {voucher_code}")
        return True
        
    except Exception as e:
        logger.error(f"Exception in _perform_download for voucher {voucher_code}: {str(e)}")
        update_voucher_status(
            voucher_code, 
            'failed', 
            error_message=f"Download error: {str(e)}"
        )
        return False

def parse_progress(line):
    """Parse progress information from yt-dlp output"""
    # Look for download progress percentage
    progress_match = re.search(r'(\d+\.\d+)%', line)
    if progress_match:
        try:
            return float(progress_match.group(1))
        except (ValueError, IndexError):
            pass
    
    # Look for other progress indicators
    if 'Downloading' in line and 'ETA' in line:
        # Try to extract progress from more complex output
        parts = line.split()
        for i, part in enumerate(parts):
            if part.endswith('%'):
                try:
                    return float(part.rstrip('%'))
                except ValueError:
                    pass
    
    return None
