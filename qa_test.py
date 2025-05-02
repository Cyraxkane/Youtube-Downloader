import os
import time
import random
import requests
import threading
import subprocess
from urllib.parse import urlparse, parse_qs

# Configuration
BASE_URL = "http://localhost:5000"  # Change to your server URL
TEST_VIDEOS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (first YouTube video)
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",  # Despacito
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # Gangnam Style
]
FORMATS = ["mp3", "mp4"]
MP3_QUALITIES = ["128k", "192k", "320k"]
MP4_QUALITIES = ["480p", "720p", "1080p"]

# Test cases
def test_basic_download():
    """Test basic download functionality"""
    print("\n=== Testing Basic Download ===")
    
    for video_url in TEST_VIDEOS[:2]:  # Use first two videos
        for format_type in FORMATS:
            if format_type == "mp3":
                quality = random.choice(MP3_QUALITIES)
            else:
                quality = random.choice(MP4_QUALITIES)
            
            print(f"Testing {format_type} download with {quality} quality for {video_url}")
            
            # Create voucher
            voucher_code = create_voucher(video_url, format_type, quality)
            if not voucher_code:
                print("❌ Failed to create voucher")
                continue
                
            print(f"✅ Created voucher: {voucher_code}")
            
            # Wait for download to complete
            status = wait_for_download(voucher_code, timeout=300)  # 5 minutes timeout
            
            if status == "complete":
                print(f"✅ Download completed successfully for {voucher_code}")
            else:
                print(f"❌ Download failed or timed out for {voucher_code}: {status}")

def test_network_interruption():
    """Test download resilience with network interruptions"""
    print("\n=== Testing Network Interruption Resilience ===")
    
    # Start a download
    video_url = random.choice(TEST_VIDEOS)
    format_type = random.choice(FORMATS)
    quality = random.choice(MP4_QUALITIES if format_type == "mp4" else MP3_QUALITIES)
    
    print(f"Testing network interruption with {format_type} download for {video_url}")
    
    # Create voucher
    voucher_code = create_voucher(video_url, format_type, quality)
    if not voucher_code:
        print("❌ Failed to create voucher")
        return
        
    print(f"✅ Created voucher: {voucher_code}")
    
    # Wait for download to start
    time.sleep(5)
    
    # Simulate network interruption
    print("Simulating network interruption...")
    
    # Option 1: Use iptables to block outgoing connections (requires root)
    # subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", "DROP"])
    
    # Option 2: Disconnect from network (less reliable, depends on OS)
    # On Linux: subprocess.run(["nmcli", "networking", "off"])
    # On Windows: subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "admin=disable"])
    
    # For testing purposes, we'll just print instructions
    print("⚠️ Manual step required: Please disconnect your network for 10 seconds, then reconnect")
    input("Press Enter after you've reconnected...")
    
    # Wait for download to complete or fail
    status = wait_for_download(voucher_code, timeout=300)  # 5 minutes timeout
    
    if status == "complete":
        print(f"✅ Download recovered and completed successfully for {voucher_code}")
    else:
        print(f"❌ Download failed to recover for {voucher_code}: {status}")

def test_concurrent_downloads():
    """Test multiple concurrent downloads"""
    print("\n=== Testing Concurrent Downloads ===")
    
    num_concurrent = 3
    voucher_codes = []
    
    # Start multiple downloads
    for i in range(num_concurrent):
        video_url = random.choice(TEST_VIDEOS)
        format_type = random.choice(FORMATS)
        quality = random.choice(MP4_QUALITIES if format_type == "mp4" else MP3_QUALITIES)
        
        print(f"Starting download {i+1}/{num_concurrent}: {format_type} {quality} for {video_url}")
        
        voucher_code = create_voucher(video_url, format_type, quality)
        if voucher_code:
            voucher_codes.append(voucher_code)
            print(f"✅ Created voucher: {voucher_code}")
        else:
            print(f"❌ Failed to create voucher for download {i+1}")
    
    # Wait for all downloads to complete
    for voucher_code in voucher_codes:
        status = wait_for_download(voucher_code, timeout=600)  # 10 minutes timeout
        
        if status == "complete":
            print(f"✅ Download completed successfully for {voucher_code}")
        else:
            print(f"❌ Download failed or timed out for {voucher_code}: {status}")

# Helper functions
def create_voucher(youtube_url, format_type, quality):
    """Create a new voucher and return the voucher code"""
    try:
        data = {
            "youtube_url": youtube_url,
            "format_type": format_type
        }
        
        if format_type == "mp3":
            data["mp3_quality"] = quality
        else:
            data["mp4_quality"] = quality
        
        # Use the debug endpoint which returns JSON
        response = requests.post(f"{BASE_URL}/debug/create_voucher", data=data)
        
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('success') and result.get('voucher_code'):
                    return result['voucher_code']
                else:
                    print(f"API returned success=False or missing voucher_code: {result}")
            except ValueError:
                print(f"Could not parse JSON response: {response.text[:200]}")
        else:
            print(f"API returned status code {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"Error creating voucher: {str(e)}")
    
    return None


def wait_for_download(voucher_code, timeout=300, check_interval=5):
    """Wait for download to complete, with timeout"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Try to use a JSON endpoint if available
            response = requests.get(f"{BASE_URL}/voucher/{voucher_code}/status")
            
            try:
                # Try to parse as JSON first
                result = response.json()
                status = result.get('status')
                if status == "complete":
                    return "complete"
                elif status == "failed":
                    return "failed"
                else:
                    print(f"Current status: {status}")
            except ValueError:
                # Fall back to HTML parsing
                response = requests.get(f"{BASE_URL}/voucher/{voucher_code}")
                content = response.text
                
                if "Status:</strong> Complete" in content or "status-complete" in content:
                    return "complete"
                elif "Status:</strong> Failed" in content or "status-failed" in content:
                    return "failed"
                else:
                    print(f"Current status: Processing")
                
        except Exception as e:
            print(f"Error checking status: {str(e)}")
        
        time.sleep(check_interval)
    
    return "timeout"


if __name__ == "__main__":
    print("YouTube Downloader QA Test Suite")
    print("================================")
    
    # Run tests
    test_basic_download()
    test_concurrent_downloads()
    test_network_interruption()
    
    print("\nAll tests completed!")
