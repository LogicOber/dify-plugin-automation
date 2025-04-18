"""
README & PRIVACY Generator - A tool to generate documentation from plugin manifest and codebase
"""

# Standard library imports
import os
import sys
import json
import argparse
from pathlib import Path

# Setup import path for local modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Third-party imports
from dotenv import load_dotenv

# Local module imports
from utils.formatting import (
    print_header, print_success, print_info, 
    print_warning, print_error, print_progress
)
from utils.file_operations import find_manifest_file, create_plugin_directory, create_reminder_file
from utils.manifest_handler import extract_manifest_info
from utils.code_analyzer import generate_code_structure
from utils.token_counter import count_tokens
from utils.api_handler import call_dify_api
# No longer needed: from utils.markdown_extractor import extract_markdown_files
from utils.logging import write_error_log

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
    print_error("DIFY_API_KEY environment variable is not set.")
    print_info("Please create a .env file with your Dify API key.")
    sys.exit(1)


def main():
    """Main function to run the README & PRIVACY Generator"""
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
    plugin_dir = create_plugin_directory(manifest_info["name"])
    if not plugin_dir:
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
    print_header("GENERATING DOCUMENTATION", "─")
    max_retries = int(os.getenv("MAX_RETRIES", "0"))
    
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
    
    # Make the API call with XML tag extraction enabled
    print_info("Generating documentation using Dify API...")
    api_response, error_details = call_dify_api(plugin_dir, manifest_info, inputs, query, max_retries, save_docs=True)
    
    if api_response:
        # Check if README and PRIVACY content was extracted
        readme_found = api_response.get('readme_content', '') != ''
        privacy_found = api_response.get('privacy_content', '') != ''
        
        # Report on extraction results
        print_header("DOCUMENTATION RESULTS", "─")
        
        if readme_found or privacy_found:
            # At least one document was generated
            if readme_found and privacy_found:
                print_success("Generated both README.md and PRIVACY.md files")
                print_info(f"Files saved to: {plugin_dir}")
            elif readme_found:
                print_success("Generated README.md file")
                print_info(f"File saved to: {plugin_dir}")
            elif privacy_found:
                print_success("Generated PRIVACY.md file")
                print_info(f"File saved to: {plugin_dir}")
            
            # Copy generated files to source directory
            print_info(f"Copying documentation to source directory: {plugin_path}")
            from utils.file_operations import copy_docs_to_source
            readme_copied, privacy_copied = copy_docs_to_source(
                plugin_dir, plugin_path, readme_found, privacy_found
            )
            
            # Report on copy results
            if readme_copied or privacy_copied:
                print_success("Documentation copied to source directory successfully")
            else:
                print_warning("Failed to copy documentation to source directory")
        else:
            print_error("Failed to generate documentation files")
            error_message = "Failed to extract documentation content from API response."
            write_error_log(error_message, error_details, plugin_dir)
            print_info("Check error_log.txt for details")
    else:
        print_error("Failed to get API response. Check error log for details.")
        if error_details:
            write_error_log("API call failed", error_details, plugin_dir)
            print_info("Error details written to error_log.txt")
    
    print("")
    print_header("PROCESS COMPLETED", "=")


if __name__ == "__main__":
    main()