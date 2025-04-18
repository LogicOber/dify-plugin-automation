"""
Token counting utilities
"""
import tiktoken
from utils.formatting import print_info, print_error

def count_tokens(text):
    """Count the number of tokens in a text using tiktoken"""
    try:
        # Use cl100k_base encoding (used by GPT models)
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        print_error(f"Error counting tokens: {e}")
        # Return an approximate count as fallback (rough estimate)
        return len(text) // 4  # Very rough approximation
