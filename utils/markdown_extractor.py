"""
Markdown extraction utilities
"""
import os
import re
from utils.formatting import print_error, print_info, print_success, print_warning, print_progress

def extract_markdown_files(api_response, plugin_dir):
    """Extract README.md and PRIVACY.md content directly from API response
    
    Args:
        api_response: String containing API response with markdown content
        plugin_dir: Directory to save extracted files
    
    Returns:
        List of filenames that were successfully extracted
    """
    # Initialize list of extracted files
    extracted_files = []
    
    # Function to extract content between markdown code blocks
    def extract_markdown_content(text, file_prefix):
        pattern = r"```md(?:own)?(?:arkdown)?\s+# " + file_prefix + r"[\s\S]+?```"
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            # Take the first match
            content = matches[0]
            # Remove markdown code block markers
            content = re.sub(r"```md(?:own)?(?:arkdown)?\s+", "", content, flags=re.IGNORECASE)
            content = re.sub(r"```\s*$", "", content)
            return content
        
        # Try an alternative pattern (just using file name)
        alt_pattern = r"# " + file_prefix + r"[\s\S]+?(?=# |$)"
        matches = re.findall(alt_pattern, text)
        
        if matches:
            return matches[0]
        
        return None
    
    try:
        # Extract README.md content
        readme_content = extract_markdown_content(api_response, "README")
        if readme_content:
            # Save README.md content to file
            readme_path = os.path.join(plugin_dir, "README.md")
            with open(readme_path, "w") as f:
                f.write(readme_content)
            print_success(f"Extracted README.md ({len(readme_content)} characters)")
            extracted_files.append("README.md")
        else:
            print_warning("Could not extract README.md content from API response")
        
        # Extract PRIVACY.md content
        privacy_content = extract_markdown_content(api_response, "PRIVACY")
        if privacy_content:
            # Save PRIVACY.md content to file
            privacy_path = os.path.join(plugin_dir, "PRIVACY.md")
            with open(privacy_path, "w") as f:
                f.write(privacy_content)
            print_success(f"Extracted PRIVACY.md ({len(privacy_content)} characters)")
            extracted_files.append("PRIVACY.md")
        else:
            # Try to find content for privacy policy using alternative patterns
            alt_patterns = [
                r"# Privacy Policy[\s\S]+?(?=# |$)",
                r"## Privacy Policy[\s\S]+?(?=## |$)",
                r"# PRIVACY POLICY[\s\S]+?(?=# |$)",
                r"## PRIVACY POLICY[\s\S]+?(?=## |$)"
            ]
            
            for pattern in alt_patterns:
                matches = re.findall(pattern, api_response)
                if matches:
                    privacy_content = matches[0]
                    # Save PRIVACY.md content to file
                    privacy_path = os.path.join(plugin_dir, "PRIVACY.md")
                    with open(privacy_path, "w") as f:
                        f.write(privacy_content)
                    print_success(f"Extracted PRIVACY.md using alternative pattern ({len(privacy_content)} characters)")
                    extracted_files.append("PRIVACY.md")
                    break
            else:
                print_warning("Could not extract PRIVACY.md content from API response")
        
        # Extract additional content if any (e.g., API documentation, installation guide)
        # This is optional and depends on the specific requirements
        
        return extracted_files
    
    except Exception as e:
        print_error(f"Error extracting markdown files: {e}")
        return extracted_files
