"""
README & PRIVACY Generator - A tool to generate documentation from plugin manifest and codebase
"""

import os
import sys
import yaml
import json
import re
import requests
import time
import tiktoken
from pathlib import Path
from dotenv import load_dotenv
import gitingest
import argparse
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Import colorama for colored terminal output
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

# Global variable for additional content
additional_content = ""

# Load environment variables from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Get API credentials and settings from environment variables
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
DIFY_API_KEY = os.getenv("DIFY_API_KEY")

# Get retry settings from environment variables (default to 2 retries)
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# Get file extensions to ignore (comma-separated list)
IGNORE_EXTENSIONS = os.getenv("IGNORE_EXTENSIONS", ".min.js,.min.css,.map,.lock")
# Convert to list and ensure each extension starts with a dot
IGNORE_EXTENSIONS = [ext if ext.startswith('.') else f'.{ext}' for ext in IGNORE_EXTENSIONS.split(',')]

# Token limit settings
TOKEN_LIMIT = int(os.getenv("TOKEN_LIMIT", "64000"))  # Default to 64k tokens

if not DIFY_API_KEY:
    print("Error: DIFY_API_KEY environment variable is not set.")
    print("Please create a .env file with your Dify API key.")
    sys.exit(1)

def find_manifest_file(directory):
    """Find manifest.yaml file in the given directory"""
    # Convert to Path object and resolve to absolute path
    dir_path = Path(directory).expanduser().resolve()
    
    # Check if directory exists
    if not dir_path.exists():
        print(f"Error: Directory does not exist: {dir_path}")
        return None
    
    # Look for manifest.yaml
    manifest_path = dir_path / "manifest.yaml"
    if not manifest_path.exists():
        # Debug information
        print(f"Debug: Looking for manifest.yaml in: {dir_path}")
        print(f"Debug: Files in directory:")
        for file in dir_path.iterdir():
            print(f"  - {file.name}")
        print(f"Error: No manifest.yaml file found in {dir_path}")
        return None
    
    return manifest_path

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


def find_manifest_file(directory):
    """Find manifest.yaml file in the given directory"""
    # Check if directory exists
    if not os.path.isdir(directory):
        print_error(f"Directory does not exist: {directory}")
        return None
    
    # Look for manifest.yaml in the directory
    manifest_path = os.path.join(directory, 'manifest.yaml')
    if os.path.isfile(manifest_path):
        print_info(f"Opening manifest file at: {manifest_path}")
        return manifest_path
    
    # If not found, try manifest.yml
    manifest_path = os.path.join(directory, 'manifest.yml')
    if os.path.isfile(manifest_path):
        print_info(f"Opening manifest file at: {manifest_path}")
        return manifest_path
    
    print_error(f"Could not find manifest.yaml or manifest.yml in {directory}")
    return None


def extract_manifest_info(plugin_path):
    """Extract information from manifest.yaml"""
    try:
        # Find the manifest file
        manifest_path = find_manifest_file(plugin_path)
        if not manifest_path:
            return None
            
        # Try to open and parse the manifest file
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = yaml.safe_load(f)
            print_info("Manifest file loaded successfully")
            
        # Extract required fields
        author = manifest_data.get('author', 'unknown')
        version = manifest_data.get('version', '0.0.1')
        plugin_type = manifest_data.get('type', 'plugin')
        name = manifest_data.get('name', 'unnamed_plugin')
        
        # Print extracted information
        print_header("MANIFEST INFORMATION", "─")
        print_success(f"Author: {author}")
        print_success(f"Version: {version}")
        print_success(f"Type: {plugin_type}")
        print_success(f"Name: {name}")
        
        # Return as a dictionary
        return {
            'author': author,
            'version': version,
            'type': plugin_type,
            'name': name
        }
    except Exception as e:
        print_error(f"Error parsing manifest file: {e}")
        return None


def create_plugin_directory(plugin_name):
    """Create a dedicated directory for the plugin"""
    try:
        # Create a safe name for the directory
        safe_name = ''.join(c if c.isalnum() else '_' for c in plugin_name)
        
        # Create plugins directory if it doesn't exist
        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'plugins')
        os.makedirs(plugins_dir, exist_ok=True)
        
        # Create plugin-specific directory
        plugin_dir = os.path.join(plugins_dir, safe_name)
        os.makedirs(plugin_dir, exist_ok=True)
        
        print_info(f"Using plugin directory: {plugin_dir}")
        return plugin_dir
    except Exception as e:
        print_error(f"Error creating plugin directory: {e}")
        return None


def generate_code_structure(plugin_path, output_file):
    """Analyze code structure using gitingest"""
    try:
        # Print information about ignored extensions
        print_progress("Analyzing code with gitingest...")
        print_info(f"Note: We'll manually filter files with extensions: {', '.join(IGNORE_EXTENSIONS)}")
        
        # Call the ingest function from gitingest
        output_path = output_file  # Use the output file path directly
        summary, tree, content = gitingest.ingest(plugin_path, output=output_path)
        
        # Read the generated file to get content
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            # Filter out content related to ignored extensions
            filtered_lines = []
            for line in file_content.split('\n'):
                # Skip lines containing ignored extensions
                should_include = True
                for ext in IGNORE_EXTENSIONS:
                    if ext in line.lower():
                        should_include = False
                        break
                if should_include:
                    filtered_lines.append(line)
            
            # Write filtered content back to file
            filtered_content = '\n'.join(filtered_lines)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(filtered_content)
            
            print_success("Code structure generated successfully!")
            print_info(f"Output file: {output_file}")
            return filtered_content
        else:
            print_error(f"Output file not found: {output_file}")
            return None
    except Exception as e:
        print_error(f"Error analyzing code structure: {e}")
        return None


def count_tokens(text):
    """Count the number of tokens in a text using tiktoken"""
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        tokens = encoding.encode(text)
        return len(tokens)
    except ImportError:
        # If tiktoken is not installed, estimate tokens (1 token ≈ 4 chars)
        return len(text) // 4


def call_dify_api(plugin_dir, manifest_info, inputs, query, max_retries=0):
    """Call Dify API with extracted information"""
    global last_api_response  # Use global variable to store last response for error logging
    global last_error_details  # Store error details for better logging
    
    # Reset error tracking variables
    last_api_response = None
    last_error_details = ""
    
    # Get API key from environment variable
    api_key = os.getenv("DIFY_API_KEY")
    if not api_key:
        print_error("DIFY_API_KEY not found in environment variables")
        print_error("Please set DIFY_API_KEY in .env file")
        return None
    
    # Get API base URL from environment variable or use default
    base_url = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Make sure inputs contains the required author field
    if 'manifest_info' in inputs and isinstance(inputs['manifest_info'], str):
        # manifest_info is already a JSON string, we don't need to modify it
        pass
    else:
        # Add author, version, type, and name directly to inputs
        inputs['author'] = manifest_info['author']
        inputs['version'] = manifest_info['version']
        inputs['type'] = manifest_info['type']
        inputs['name'] = manifest_info['name']
    
    # Prepare payload with manifest info and code structure
    user_identifier = f"{manifest_info['name']}_{manifest_info['author']}"
    payload = {
        "inputs": inputs,
        "query": query,
        "response_mode": "blocking",
        "user": user_identifier
    }
    
    try:
        print_header("SENDING REQUEST TO DIFY API", "─")
        print_progress("This may take up to 10 minutes...")
        
        # Add a simple spinner to show progress
        spinner = ['|', '/', '-', '\\']
        spinner_idx = 0
        start_time = time.time()
        
        # Set timeout to 10 minutes (600 seconds)
        # Show a spinner while waiting
        print("\r" + Fore.CYAN + "Waiting for response ", end="")
        
        # Make the API request - print limited request details for debugging
        request_url = f"{DIFY_BASE_URL}/chat-messages"
        print_info(f"Request URL: {request_url}")
        # Don't print headers as they contain sensitive information
        
        # Count tokens in payload instead of characters
        payload_str = json.dumps(payload)
        token_count = count_tokens(payload_str)
        print_info(f"Request payload size: {token_count} tokens (approximately {len(payload_str)} characters)")
        
        # No longer saving request payload
        
        # Make the actual request
        response = requests.post(
            request_url, 
            headers=headers, 
            json=payload,
            timeout=600  # 10 minute timeout
        )
        
        # Clear the spinner line
        print("\r" + " " * 50 + "\r", end="")
        
        # No longer saving raw response
        
        # Store response for error logging
        last_api_response = response
        
        # Print response details
        print_info(f"Response status code: {response.status_code}")
        print_info(f"Response headers: {dict(response.headers)}")
        
        # Handle successful response
        if response.status_code == 200:
            try:
                result = response.json()
                elapsed_time = time.time() - start_time
                print_success(f"API response received successfully! ({elapsed_time:.1f}s)")
                
                # No longer saving JSON response
                
                # Save the answer text if present
                if 'answer' in result:
                    answer_path = os.path.join(plugin_dir, 'response.md')
                    with open(answer_path, 'w', encoding='utf-8') as f:
                        f.write(result['answer'])
                    print_info(f"Answer text saved to: {answer_path}")
                    print_info("Response content (first 200 chars):")
                    print(f"\n{Fore.WHITE}{result['answer'][:200]}...")
                    
                    # Extract metadata if present
                    if 'metadata' in result and 'usage' in result['metadata']:
                        usage = result['metadata']['usage']
                        cost = usage.get('total_price', 'N/A')
                        currency = usage.get('currency', 'USD')
                        tokens = usage.get('total_tokens', 'N/A')
                        
                        # Print usage information
                        print_info(f"Cost: {cost} {currency}")
                        print_info(f"Total tokens: {tokens}")
                        
                        # Save cost and token information to response.md with proper markdown formatting
                        cost_info = f"\n\n---\n\n## Usage Information\n\nCost: {cost} {currency}\nTotal tokens: {tokens}"
                        cost_path = os.path.join(plugin_dir, 'response.md')
                        try:
                            with open(cost_path, 'a', encoding='utf-8') as f:
                                f.write(cost_info)
                            print_info(f"Cost information saved to: {cost_path}")
                        except Exception as e:
                            print_error(f"Failed to save cost information: {e}")
                else:
                    print_warning("Response does not contain 'answer' field")
            except Exception as e:
                print_error(f"Error processing successful response: {e}")
                return None
            
            # Check if response has the expected format
            if 'answer' in result and result['answer']:
                # Store the raw answer for error logging
                last_error_details = f"Raw API response: {result['answer'][:500]}..."
                return result
            else:
                print_warning("API response does not contain expected 'answer' field")
                last_error_details = f"API response missing 'answer' field: {str(result)[:500]}..."
                return None
        else:
            error_text = response.text
            last_error_details = f"HTTP {response.status_code}: {error_text[:1000]}"
            print_error(f"Dify API returned error {response.status_code}")
            print_error(f"Error details: {error_text[:200]}..." if len(error_text) > 200 else error_text)
            return None
    except requests.exceptions.Timeout:
        print_error("Request timed out after 10 minutes")
        print_error("The server is taking too long to respond")
        return None
    except Exception as e:
        print_error(f"API request failed: {str(e)}")
        return None


def extract_markdown_files(api_response, plugin_dir):
    """Extract README.md and PRIVACY.md content directly from API response"""
    global last_error_details
    error_log = ""
    files_extracted = []
    
    # Extract README.md content - look for markdown section headers
    readme_pattern = r'(?:#+\s*README\.md.*?\n+)(.*?)(?:(?:#+\s*|$))'  # Match content between README.md header and next header or end
    readme_match = re.search(readme_pattern, api_response, re.DOTALL)
    
    if readme_match:
        readme_content = readme_match.group(1).strip()
        readme_path = os.path.join(plugin_dir, 'README.md')
        try:
            print_header("EXTRACTING README.md", "─")
            print_info(f"Found README.md content ({len(readme_content)} characters)")
            
            # Save the content as Markdown
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            print_success(f"README.md saved to: {readme_path}")
            files_extracted.append('README.md')
        except Exception as e:
            error_msg = f"Error saving README.md: {e}"
            print_error(error_msg)
            error_log += f"{error_msg}\n"
    else:
        # Try alternative pattern
        readme_pattern2 = r'```markdown\s*?#\s*README\s*?\n(.*?)```'
        readme_match2 = re.search(readme_pattern2, api_response, re.DOTALL)
        if readme_match2:
            readme_content = readme_match2.group(1).strip()
            readme_path = os.path.join(plugin_dir, 'README.md')
            try:
                print_header("EXTRACTING README.md", "─")
                print_info(f"Found README.md content ({len(readme_content)} characters)")
                
                # Save the content as Markdown
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                print_success(f"README.md saved to: {readme_path}")
                files_extracted.append('README.md')
            except Exception as e:
                error_msg = f"Error saving README.md: {e}"
                print_error(error_msg)
                error_log += f"{error_msg}\n"
        else:
            error_msg = "Could not find README.md content in the API response"
            print_warning(error_msg)
            error_log += f"{error_msg}\n"
    
    # Extract PRIVACY.md content
    privacy_pattern = r'(?:#+\s*PRIVACY\.md.*?\n+)(.*?)(?:(?:#+\s*|$))'  # Match content between PRIVACY.md header and next header or end
    privacy_match = re.search(privacy_pattern, api_response, re.DOTALL)
    
    if privacy_match:
        privacy_content = privacy_match.group(1).strip()
        privacy_path = os.path.join(plugin_dir, 'PRIVACY.md')
        try:
            print_header("EXTRACTING PRIVACY.md", "─")
            print_info(f"Found PRIVACY.md content ({len(privacy_content)} characters)")
            
            # Save the content as Markdown
            with open(privacy_path, 'w', encoding='utf-8') as f:
                f.write(privacy_content)
            print_success(f"PRIVACY.md saved to: {privacy_path}")
            files_extracted.append('PRIVACY.md')
        except Exception as e:
            error_msg = f"Error saving PRIVACY.md: {e}"
            print_error(error_msg)
            error_log += f"{error_msg}\n"
    else:
        # Try alternative pattern
        privacy_pattern2 = r'```markdown\s*?#\s*PRIVACY\s*?\n(.*?)```'
        privacy_match2 = re.search(privacy_pattern2, api_response, re.DOTALL)
        if privacy_match2:
            privacy_content = privacy_match2.group(1).strip()
            privacy_path = os.path.join(plugin_dir, 'PRIVACY.md')
            try:
                print_header("EXTRACTING PRIVACY.md", "─")
                print_info(f"Found PRIVACY.md content ({len(privacy_content)} characters)")
                
                # Save the content as Markdown
                with open(privacy_path, 'w', encoding='utf-8') as f:
                    f.write(privacy_content)
                print_success(f"PRIVACY.md saved to: {privacy_path}")
                files_extracted.append('PRIVACY.md')
            except Exception as e:
                error_msg = f"Error saving PRIVACY.md: {e}"
                print_error(error_msg)
                error_log += f"{error_msg}\n"
        else:
            error_msg = "Could not find PRIVACY.md content in the API response"
            print_warning(error_msg)
            error_log += f"{error_msg}\n"
    
    # Update last_error_details with the error log
    if error_log and not files_extracted:
        last_error_details = error_log
    
    return files_extracted


def create_reminder_file(plugin_dir, plugin_name):
    """Create a reminder file for developers to check and modify the generated docs"""
    reminder_path = os.path.join(plugin_dir, "PLEASE_NOTE.md")
    
    reminder_content = f"""# IMPORTANT NOTES FOR PLUGIN DEVELOPERS

Thank you for using the README & PRIVACY Generator tool!

While we've generated documentation for your '{plugin_name}' plugin, please review and consider the following:

- [ ] **Copy the full content** from README.md and PRIVACY.md files to your plugin's own markdown files (don't just paste links)

- [ ] Check if the PRIVACY.md content meets your expectations and complies with relevant regulations

- [ ] Ensure the README.md is user-friendly and accurately describes your plugin's functionality

- [ ] Add your contact email in the Support section of README.md

- [ ] Consider adding screenshots or example DSL files if they would help users understand your plugin

## Next Steps

1. Copy the content from README.md to your plugin's README.md file
2. Copy the content from PRIVACY.md to your plugin's PRIVACY.md file
3. Make any necessary edits to customize the documentation for your plugin

Remember that well-documented plugins tend to get more downloads and positive feedback!

---

*This reminder was automatically generated by the README & PRIVACY Generator tool.*
"""
    
    try:
        with open(reminder_path, 'w', encoding='utf-8') as f:
            f.write(reminder_content)
        print_info(f"Created reminder file: {reminder_path}")
        return True
    except Exception as e:
        print_error(f"Error creating reminder file: {e}")
        return False


def write_error_log(error_message, error_details, plugin_dir):
    """Write error information to a log file"""
    log_path = os.path.join(plugin_dir, 'error_log.txt')
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Error occurred at {timestamp}\n\n")
            f.write(f"{error_message}\n\n")
            f.write("Error Details:\n")
            f.write(f"{error_details}\n")
        print_info(f"Error details have been saved to: {log_path}")
        return True
    except Exception as e:
        print_error(f"Failed to write error log: {e}")
        return False


# Global variables to store API response and error details for logging
last_api_response = None
last_error_details = ""


def main():
    """Main function to run the README & PRIVACY Generator"""
    global plugin_dir  # Make plugin_dir global so it can be accessed in API call function
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate README & PRIVACY documentation for Dify plugins.')
    parser.add_argument('-p', '--path', help='Path to the plugin directory')
    parser.add_argument('-y', '--yes', action='store_true', help='Run in non-interactive mode (skip additional instructions)')
    args = parser.parse_args()
    
    print_header("README & PRIVACY Generator", "=")
    print("\nThis tool generates README & PRIVACY documentation for Dify plugins")
    print("It extracts information from manifest.yaml and analyzes code structure")
    
    # Get plugin directory from user or command line
    if args.path:
        plugin_path = args.path.strip('"').strip("'")  # Remove quotes if present
        print_info(f"Using plugin path from command line: {plugin_path}")
    else:
        plugin_path = input("Enter the plugin directory path: ")
        plugin_path = plugin_path.strip('"').strip("'")  # Remove quotes if present
    
    # Validate the path
    if not os.path.isdir(plugin_path):
        print_error(f"Directory not found: {plugin_path}")
        sys.exit(1)
    
    # Extract manifest information
    manifest_info = extract_manifest_info(plugin_path)
    if not manifest_info:
        print_error("Failed to extract manifest information. Exiting.")
        sys.exit(1)
    
    # Create plugin directory if it doesn't exist
    plugin_dir = os.path.join(os.getcwd(), "plugins", manifest_info["name"])
    try:
        os.makedirs(plugin_dir, exist_ok=True)
    except Exception as e:
        print_error(f"Failed to create plugin directory: {e}")
        print_error("Failed to create plugin directory. Exiting.")
        sys.exit(1)
    
    # Create reminder file immediately after getting plugin info
    create_reminder_file(plugin_dir, manifest_info["name"])
    
    # Generate code structure file
    print_header("GENERATING CODE STRUCTURE", "─")
    output_file = os.path.join(plugin_dir, f"{manifest_info['name']}_structure.txt")
    code_structure = generate_code_structure(plugin_path, output_file)
    if not code_structure:
        print_error("Failed to generate code structure. Exiting.")
        sys.exit(1)
        
    # Count tokens in code structure
    token_count = count_tokens(code_structure)
    print_info(f"Code structure contains approximately {token_count} tokens")
    
    # Check if token count exceeds limit
    token_limit = int(os.getenv("TOKEN_LIMIT", "64000"))
    if token_count > token_limit:
        print_warning(f"Code structure exceeds token limit of {token_limit}!")
        print_warning("This may cause issues with the API call.")
        if args.yes:
            print_info("Running in non-interactive mode, proceeding anyway...")
            proceed = 'y'
        else:
            proceed = input("Do you want to proceed anyway? (y/n): ").lower()
        if proceed != 'y':
            print_info("Exiting. Consider reducing the code structure size.")
            sys.exit(0)
    
    # Get any additional instructions from user (unless in non-interactive mode)
    if args.yes:
        print_info("Running in non-interactive mode (skipping additional instructions)")
        additional_instructions = ""
    else:
        additional_instructions = input("Any additional instructions? (Press Enter to skip): ")
    
    # Call Dify API
    print_header("CALLING DIFY API", "─")
    max_retries = int(os.getenv("MAX_RETRIES", "0"))
    print_info(f"Maximum retry attempts: {max_retries}")
    
    # Prepare inputs for API call
    inputs = {
        "author": manifest_info['author'],
        "version": manifest_info['version'],
        "type": manifest_info['type'],
        "name": manifest_info['name'],
        "manifest_info": json.dumps(manifest_info, indent=2),
        "code_files": code_structure
    }
    
    if additional_instructions:
        inputs["additional_instructions"] = additional_instructions
    
    # Query for API
    query = "Generate README.md and PRIVACY.md for this Dify plugin"
    
    # Make the API call
    print_info("Sending request to Dify API...")
    api_response = call_dify_api(plugin_dir, manifest_info, inputs, query, max_retries)
    
    if api_response and 'answer' in api_response:
        # Extract markdown files from API response
        print_header("EXTRACTING MARKDOWN FILES", "─")
        files_extracted = extract_markdown_files(api_response['answer'], plugin_dir)
        
        if files_extracted:
            print_success(f"Successfully extracted {len(files_extracted)} files: {', '.join(files_extracted)}")
            print_info(f"Files saved to: {plugin_dir}")
        else:
            print_error("Failed to extract any markdown files from API response.")
            error_message = "Failed to extract markdown files from API response."
            write_error_log(error_message, last_error_details, plugin_dir)
            print_info("Check error_log.txt for details")
    else:
        print_error("Failed to get API response. Check error log for details.")
    
    print("")
    print_header("PROCESS COMPLETED", "=")

if __name__ == "__main__":
    main()
