"""
Logging utilities
"""
import os
import datetime
from utils.formatting import print_info, print_error

def write_error_log(error_message, error_details, plugin_dir):
    """Write error information to a log file
    
    Args:
        error_message: Brief description of the error
        error_details: Detailed error information
        plugin_dir: Directory to save log file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create log file path
        log_file = os.path.join(plugin_dir, "error_log.txt")
        
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write error information to log file
        with open(log_file, "a") as f:
            f.write(f"==== ERROR LOG: {timestamp} ====\n")
            f.write(f"Error: {error_message}\n")
            f.write("Details:\n")
            f.write(f"{error_details}\n")
            f.write("="*50 + "\n\n")
        
        print_info(f"Error details written to: {log_file}")
        return True
    
    except Exception as e:
        print_error(f"Failed to write error log: {e}")
        return False
