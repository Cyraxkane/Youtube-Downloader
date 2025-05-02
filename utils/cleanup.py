import os
import json
from datetime import datetime, timedelta

from config import DOWNLOAD_DIR, VOUCHER_LOG, RETENTION_PERIOD

def cleanup_old_files():
    """Remove files older than the retention period"""
    if not os.path.exists(VOUCHER_LOG):
        return
    
    now = datetime.now()
    
    # Load vouchers
    with open(VOUCHER_LOG, 'r') as f:
        try:
            vouchers = json.load(f)
        except json.JSONDecodeError:
            return
    
    updated_vouchers = []
    
    for voucher in vouchers:
        try:
            # Check if the voucher has a creation date
            if "created_at" in voucher:
                created_at = datetime.fromisoformat(voucher["created_at"])
                age = now - created_at
                
                # If older than retention period, delete the file and don't include in updated list
                if age > RETENTION_PERIOD:
                    if voucher.get("file_path") and os.path.exists(voucher["file_path"]):
                        os.remove(voucher["file_path"])
                        print(f"Deleted old file: {voucher['file_path']}")
                    # Don't include this voucher in the updated list
                    continue
            
            # For deleted vouchers, check if they've been deleted for more than 7 days
            if voucher.get("status") == "deleted" and "deleted_at" in voucher:
                deleted_at = datetime.fromisoformat(voucher["deleted_at"])
                delete_age = now - deleted_at
                
                # If deleted more than 7 days ago, don't include in updated list
                if delete_age > timedelta(days=7):
                    continue
            
            # Keep this voucher
            updated_vouchers.append(voucher)
                
        except (ValueError, KeyError) as e:
            # Keep vouchers with invalid dates for manual review
            print(f"Error processing voucher: {e}")
            updated_vouchers.append(voucher)
    
    # Save updated vouchers list
    with open(VOUCHER_LOG, 'w') as f:
        json.dump(updated_vouchers, f, indent=2)
