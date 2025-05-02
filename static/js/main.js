// This file can be used for any client-side functionality
document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh voucher status page if download is in progress
    const statusBox = document.querySelector('.status-processing');
    if (statusBox) {
        setTimeout(function() {
            location.reload();
        }, 10000); // Refresh every 10 seconds
    }
});
