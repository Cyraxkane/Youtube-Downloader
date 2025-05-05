import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import json
from datetime import datetime
import logging

from config import DOWNLOAD_DIR, SECRET_KEY, DETAILED_LOG
from utils.voucher import get_voucher, save_voucher, update_voucher_status, save_to_detailed_log, delete_voucher, remove_voucher_record, generate_unique_code
from utils.cleanup import cleanup_old_files
from utils.downloader import download_video

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

# Set up scheduler for cleanup task
scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_files, 'interval', hours=24)  # Run once a day
scheduler.start()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()  # This will log to console as well
    ]
)
logger = logging.getLogger('youtube-downloader')

def get_client_ip():
    """Get the client's IP address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR']
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ['HTTP_X_REAL_IP']
    else:
        return request.remote_addr
    
@app.before_request
def log_request_info():
    logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')
    if request.method == 'POST':
        logger.info(f'POST data: {request.form}')

@app.after_request
def log_response_info(response):
    logger.info(f'Response: {response.status_code}')
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_voucher():
    return render_template('new_voucher.html')

@app.route('/create_voucher', methods=['POST'])
def create_voucher():
    youtube_url = request.form.get('youtube_url')
    format_type = request.form.get('format_type')
    
    if not youtube_url or not format_type:
        flash('Please provide all required information.')
        return redirect(url_for('new_voucher'))
    
    # Get quality based on format type
    if format_type == 'mp4':
        quality = request.form.get('mp4_quality', '720p')
    else:  # mp3
        quality = request.form.get('mp3_quality', '192k')
    
    # Get client IP address
    ip_address = get_client_ip()
    
    # Generate voucher code
    voucher_code = generate_unique_code()
    voucher = get_voucher(voucher_code)
    if voucher:
        save_voucher(voucher, ip_address=request.remote_addr)
    else:
    # Create a new voucher
        voucher = {
        'code': voucher_code,
        'status': 'processing',
        'created_at': datetime.now().isoformat()
    }
    save_voucher(voucher, ip_address=request.remote_addr)
    
    # Save voucher information with IP address
    voucher = {
    'code': voucher_code,
    'youtube_url': youtube_url,
    'format_type': format_type,
    'quality': quality,
    'status': 'processing',
    'created_at': datetime.now().isoformat()
    }
    save_voucher(voucher, ip_address=request.remote_addr)
    
    # Log detailed information about the request
    save_to_detailed_log(
        voucher_code=voucher_code,
        ip_address=ip_address,
        youtube_url=youtube_url,
        format_type=format_type,
        quality=quality
    )
    
    # Start download in background
    download_video(voucher_code, youtube_url, format_type, quality, ip_address)
    
    return render_template('new_voucher.html', voucher_code=voucher_code)

@app.route('/voucher/<code>/status')
def voucher_status_json(code):
    """Return voucher status as JSON for API clients"""
    voucher = get_voucher(code)
    if not voucher:
        return jsonify({'error': 'Voucher not found'}), 404
        
    return jsonify({
        'code': voucher.get('code'),
        'status': voucher.get('status'),
        'youtube_url': voucher.get('youtube_url'),
        'format_type': voucher.get('format_type'),
        'quality': voucher.get('quality'),
        'file_size': voucher.get('file_size'),
        'created_at': voucher.get('created_at'),
        'error_message': voucher.get('error_message', '')
    })


@app.route('/debug/create_voucher', methods=['POST'])
@app.route('/debug/create_voucher/<code>', methods=['POST'])
def debug_create_voucher(code=None):
    """Debug endpoint for QA testing, optionally with a specific code"""
    youtube_url = request.form.get('youtube_url')
    format_type = request.form.get('format_type')
    
    if format_type == 'mp3':
        quality = request.form.get('mp3_quality')
    else:
        quality = request.form.get('mp4_quality')
    
    # Log the received data
    logger.info(f"Debug create voucher: URL={youtube_url}, Format={format_type}, Quality={quality}")
    
    # Generate a unique voucher code if not provided
    if not code:
        code = generate_unique_code()
    
    # Create voucher record
    voucher = {
        'code': code,
        'youtube_url': youtube_url,
        'format_type': format_type,
        'quality': quality,
        'status': 'processing',
        'created_at': datetime.now().isoformat()
    }
    
    # Save the voucher
    save_voucher(voucher)
    
    # Start the download process
    download_video(code, youtube_url, format_type, quality)
    
    # Return a simple JSON response
    return jsonify({
        'success': True,
        'voucher_code': code
    })

@app.route('/find_voucher', methods=['POST'])
def find_voucher():
    voucher_code = request.form.get('voucher_code')
    if not voucher_code:
        flash('Please enter a voucher code.')
        return redirect(url_for('index'))
    
    return redirect(url_for('voucher_status', code=voucher_code))

@app.route('/voucher/<code>')
def voucher_status(code):
    voucher = get_voucher(code)
    if not voucher:
        flash('Voucher not found.')
        return redirect(url_for('index'))
    
    return render_template('voucher.html', voucher=voucher)

@app.route('/voucher/<code>/progress')
def voucher_progress(code):
    """API endpoint to get progress for a specific voucher"""
    voucher = get_voucher(code)
    if not voucher:
        return jsonify({'error': 'Voucher not found'}), 404
    
    return jsonify({
        'status': voucher.get('status'),
        'progress': voucher.get('progress', 0),
        'error_message': voucher.get('error_message', '')
    })

@app.route('/download/<code>')
def download_file(code):
    voucher = get_voucher(code)
    if not voucher or voucher['status'] != 'complete' or not voucher.get('file_path'):
        flash('File not available for download.')
        return redirect(url_for('index'))
    
    if not os.path.exists(voucher['file_path']):
        flash('File not found on server.')
        return redirect(url_for('voucher_status', code=code))
    
    # Get filename from path
    filename = os.path.basename(voucher['file_path'])
    
    # Log the download activity
    ip_address = get_client_ip()
    save_to_detailed_log(voucher=voucher)
    # Send file to user
    return send_file(voucher['file_path'], as_attachment=True, download_name=filename)

@app.route('/delete_file/<code>')
def delete_file(code):
    """Delete a downloaded file"""
    voucher = get_voucher(code)
    if not voucher:
        flash('Voucher not found', 'error')
        return redirect(url_for('index'))
    
    # Delete the file if it exists
    file_path = voucher.get('file_path')
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            flash(f'Error deleting file: {str(e)}', 'error')
    
    # Mark voucher as deleted
    delete_voucher(code)
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('voucher_status', code=code))

@app.route('/delete_voucher_record/<code>')
def delete_voucher_record(code):
    """Permanently delete a voucher record"""
    # Delete the voucher record
    if remove_voucher_record(code):
        flash('Voucher record deleted successfully', 'success')
        return redirect(url_for('index'))
    else:
        flash('Error deleting voucher record', 'error')
        return redirect(url_for('voucher_status', code=code))

@app.route('/admin')
def admin():
    # Admin authentication
    admin_password = request.args.get('key')
    if admin_password != 'admin123':  # Change this to a secure password
        return render_template('admin_login.html')
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    format_filter = request.args.get('format', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    ip_filter = request.args.get('ip', '')
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    
    # Load detailed logs
    if os.path.exists(DETAILED_LOG):
        with open(DETAILED_LOG, 'r') as f:
            try:
                all_logs = json.load(f)
            except json.JSONDecodeError:
                all_logs = []
    else:
        all_logs = []
    
    # Apply filters
    filtered_logs = all_logs
    
    if status_filter:
        filtered_logs = [log for log in filtered_logs if log.get('status') == status_filter]
    
    if format_filter:
        filtered_logs = [log for log in filtered_logs if log.get('format_type') == format_filter]
    
    if date_from:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        filtered_logs = [log for log in filtered_logs if datetime.strptime(log.get('timestamp', '').split('T')[0], '%Y-%m-%d') >= from_date]
    
    if date_to:
        to_date = datetime.strptime(date_to, '%Y-%m-%d')
        filtered_logs = [log for log in filtered_logs if datetime.strptime(log.get('timestamp', '').split('T')[0], '%Y-%m-%d') <= to_date]
    
    if ip_filter:
        filtered_logs = [log for log in filtered_logs if ip_filter in log.get('ip_address', '')]
    
    # Sort by timestamp (newest first)
    filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Calculate pagination
    total_entries = len(filtered_logs)
    total_pages = (total_entries + per_page - 1) // per_page
    
    # Get logs for current page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    logs = filtered_logs[start_idx:end_idx]
    
    # Calculate statistics
    stats = {
        'total_downloads': len(all_logs),
        'mp4_downloads': len([log for log in all_logs if log.get('format_type') == 'mp4']),
        'mp3_downloads': len([log for log in all_logs if log.get('format_type') == 'mp3']),
        'total_storage': sum(log.get('file_size', 0) for log in all_logs if log.get('file_size'))
    }
    
    # Make sure each log has a progress field
    for log in logs:
        if 'progress' not in log and log.get('status') == 'processing':
            log['progress'] = 0
        elif 'progress' not in log and log.get('status') == 'complete':
            log['progress'] = 100
    
    return render_template('admin.html', 
                          logs=logs, 
                          page=page, 
                          total_pages=total_pages, 
                          total_entries=total_entries,
                          stats=stats)


@app.route('/admin/progress_update')
def admin_progress_update():
    """AJAX endpoint to get progress updates for processing vouchers"""
    # Simple admin authentication
    admin_password = request.args.get('key')
    if admin_password != 'admin123':  # Change this to a secure password
        abort(403)  # Forbidden
    
    # Load detailed logs
    if os.path.exists(DETAILED_LOG):
        with open(DETAILED_LOG, 'r') as f:
            try:
                all_logs = json.load(f)
            except json.JSONDecodeError:
                all_logs = []
    else:
        all_logs = []
    
    # Filter only processing vouchers
    processing_logs = [
        {
            'voucher_code': log.get('voucher_code'),
            'progress': log.get('progress', 0),
            'status': log.get('status')
        }
        for log in all_logs if log.get('status') == 'processing'
    ]
    
    return jsonify(processing_logs)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

if __name__ == '__main__':
    # Make sure directories exist
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Start the Flask app
    app.run(host='0.0.0.0',debug=True)
