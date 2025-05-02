import os
import json
import string
import random
from datetime import datetime

from config import VOUCHER_LOG, DETAILED_LOG

def generate_unique_code(length=8):
    """Generate a unique voucher code"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if not get_voucher(code):
            return code

def get_voucher(code):
    """Get voucher details by code"""
    if os.path.exists(VOUCHER_LOG):
        with open(VOUCHER_LOG, 'r') as f:
            try:
                vouchers = json.load(f)
                
                # Handle case where vouchers is a list
                if isinstance(vouchers, list):
                    for voucher in vouchers:
                        if voucher.get('code') == code:
                            return voucher
                    return None
                
                # Handle case where vouchers is a dictionary
                elif isinstance(vouchers, dict):
                    return vouchers.get(code)
                
                return None
            except json.JSONDecodeError:
                return None
    return None


def save_voucher(voucher):
    """Save voucher to the log file"""
    if os.path.exists(VOUCHER_LOG):
        with open(VOUCHER_LOG, 'r') as f:
            try:
                vouchers = json.load(f)
            except json.JSONDecodeError:
                vouchers = {}
    else:
        vouchers = {}
    
    # Convert list to dictionary if needed
    if isinstance(vouchers, list):
        vouchers_dict = {}
        for v in vouchers:
            if 'code' in v:
                vouchers_dict[v['code']] = v
        vouchers = vouchers_dict
    
    # Update or add the voucher
    vouchers[voucher['code']] = voucher
    
    with open(VOUCHER_LOG, 'w') as f:
        json.dump(vouchers, f, indent=4)
    
    # Also save to detailed log for admin view
    save_to_detailed_log(voucher)


def update_voucher_status(code, status, file_path=None, file_size=None, error_message=None, progress=None):
    """Update voucher status"""
    voucher = get_voucher(code)
    if voucher:
        voucher['status'] = status
        
        if file_path:
            voucher['file_path'] = file_path
        
        if file_size is not None:
            voucher['file_size'] = file_size
        
        if error_message:
            voucher['error_message'] = error_message
            
        if progress is not None:
            voucher['progress'] = progress
        
        if status == 'deleted':
            voucher['deleted_at'] = datetime.now().isoformat()
        
        save_voucher(voucher)
        return True
    return False


def save_to_detailed_log(voucher=None, **kwargs):
    """Save voucher to detailed log for admin view
    
    Can be called with either a voucher object or individual fields as keyword arguments
    """
    logs = []
    if os.path.exists(DETAILED_LOG):
        with open(DETAILED_LOG, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    
    # If a voucher object is provided, use it
    if voucher:
        voucher_code = voucher['code']
        log_entry = {
            'timestamp': voucher.get('created_at', datetime.now().isoformat()),
            'voucher_code': voucher_code,
            'youtube_url': voucher.get('youtube_url'),
            'format_type': voucher.get('format_type'),
            'quality': voucher.get('quality'),
            'status': voucher.get('status'),
            'file_size': voucher.get('file_size'),
            'ip_address': voucher.get('ip_address'),
            'progress': voucher.get('progress', 0)
        }
    # Otherwise use the provided keyword arguments
    else:
        voucher_code = kwargs.get('voucher_code')
        log_entry = {
            'timestamp': kwargs.get('timestamp', datetime.now().isoformat()),
            'voucher_code': voucher_code,
            'youtube_url': kwargs.get('youtube_url'),
            'format_type': kwargs.get('format_type'),
            'quality': kwargs.get('quality'),
            'status': kwargs.get('status'),
            'file_size': kwargs.get('file_size'),
            'ip_address': kwargs.get('ip_address'),
            'progress': kwargs.get('progress', 100 if kwargs.get('status') == 'complete' else 0)
        }
    
    # Check if this voucher is already in the log
    for i, log in enumerate(logs):
        if log.get('voucher_code') == voucher_code:
            # Update existing log entry
            logs[i] = log_entry
            break
    else:
        # Add new log entry
        logs.append(log_entry)
    
    with open(DETAILED_LOG, 'w') as f:
        json.dump(logs, f, indent=4)


def convert_voucher_log_to_dict():
    """Convert voucher log from list to dictionary format"""
    if os.path.exists(VOUCHER_LOG):
        with open(VOUCHER_LOG, 'r') as f:
            try:
                vouchers = json.load(f)
                
                # Only convert if it's a list
                if isinstance(vouchers, list):
                    vouchers_dict = {}
                    for voucher in vouchers:
                        if 'code' in voucher:
                            vouchers_dict[voucher['code']] = voucher
                    
                    # Save back as dictionary
                    with open(VOUCHER_LOG, 'w') as f:
                        json.dump(vouchers_dict, f, indent=4)
                    
                    print(f"Converted {len(vouchers)} vouchers from list to dictionary format")
                else:
                    print("Voucher log is already in dictionary format")
            except json.JSONDecodeError:
                print("Error reading voucher log file")
    else:
        print("Voucher log file does not exist")

def delete_voucher(code):
    """Delete a voucher from the voucher log"""
    if os.path.exists(VOUCHER_LOG):
        with open(VOUCHER_LOG, 'r') as f:
            try:
                vouchers = json.load(f)
                
                # Handle case where vouchers is a list
                if isinstance(vouchers, list):
                    for i, voucher in enumerate(vouchers):
                        if voucher.get('code') == code:
                            # Mark as deleted instead of removing
                            vouchers[i]['status'] = 'deleted'
                            vouchers[i]['deleted_at'] = datetime.now().isoformat()
                            
                            with open(VOUCHER_LOG, 'w') as f:
                                json.dump(vouchers, f, indent=4)
                            
                            # Update detailed log
                            save_to_detailed_log(voucher=vouchers[i])
                            return True
                
                # Handle case where vouchers is a dictionary
                elif isinstance(vouchers, dict) and code in vouchers:
                    # Mark as deleted instead of removing
                    vouchers[code]['status'] = 'deleted'
                    vouchers[code]['deleted_at'] = datetime.now().isoformat()
                    
                    with open(VOUCHER_LOG, 'w') as f:
                        json.dump(vouchers, f, indent=4)
                    
                    # Update detailed log
                    save_to_detailed_log(voucher=vouchers[code])
                    return True
                
            except json.JSONDecodeError:
                pass
    
    return False

def remove_voucher_record(code):  # Changed from delete_voucher_record to remove_voucher_record
    """Completely remove a voucher record from the voucher log"""
    if os.path.exists(VOUCHER_LOG):
        with open(VOUCHER_LOG, 'r') as f:
            try:
                vouchers = json.load(f)
                
                # Handle case where vouchers is a list
                if isinstance(vouchers, list):
                    for i, voucher in enumerate(vouchers):
                        if voucher.get('code') == code:
                            # Remove the voucher
                            deleted_voucher = vouchers.pop(i)
                            
                            with open(VOUCHER_LOG, 'w') as f:
                                json.dump(vouchers, f, indent=4)
                            
                            # Update detailed log to show it's been deleted
                            deleted_voucher['status'] = 'deleted'
                            deleted_voucher['deleted_at'] = datetime.now().isoformat()
                            save_to_detailed_log(voucher=deleted_voucher)
                            return True
                
                # Handle case where vouchers is a dictionary
                elif isinstance(vouchers, dict) and code in vouchers:
                    # Remove the voucher
                    deleted_voucher = vouchers.pop(code)
                    
                    with open(VOUCHER_LOG, 'w') as f:
                        json.dump(vouchers, f, indent=4)
                    
                    # Update detailed log to show it's been deleted
                    deleted_voucher['status'] = 'deleted'
                    deleted_voucher['deleted_at'] = datetime.now().isoformat()
                    save_to_detailed_log(voucher=deleted_voucher)
                    return True
                
            except json.JSONDecodeError:
                pass
    
    return False

