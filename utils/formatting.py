"""
Formatting utilities for console output
"""

import os
try:
    from colorama import init, Fore, Back, Style
    # Initialize colorama
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # If colorama is not available, define dummy color constants
    class DummyFore:
        def __getattr__(self, name):
            return ''
    
    class DummyBack:
        def __getattr__(self, name):
            return ''
    
    class DummyStyle:
        def __getattr__(self, name):
            return ''
    
    Fore = DummyFore()
    Back = DummyBack()
    Style = DummyStyle()
    COLORS_AVAILABLE = False





def print_header(message, symbol='='):
    """Print a formatted header with color"""
    width = 70
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{symbol * width}")
    print(f"{message.center(width)}")
    print(f"{symbol * width}{Style.RESET_ALL}")


def print_success(message):
    """Print a success message"""
    print(f"{Fore.GREEN}{Style.BRIGHT}✓ {message}{Style.RESET_ALL}")


def print_info(message):
    """Print an info message"""
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")


def print_warning(message):
    """Print a warning message"""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_error(message):
    """Print an error message"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")


def print_progress(message, progress=""):
    """Print a progress message"""
    if progress:
        progress = f"[{progress}] "
    print(f"{Fore.MAGENTA}→ {progress}{message}{Style.RESET_ALL}")
