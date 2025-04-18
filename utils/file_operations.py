"""
File and directory operations utilities
"""
import os
import sys
from pathlib import Path
from utils.formatting import print_error, print_info, print_success

def find_manifest_file(directory):
    """Find manifest.yaml file in the given directory"""
    # Check if directory exists
    if not os.path.isdir(directory):
        print_error(f"Directory does not exist: {directory}")
        return None
    
    # Look for manifest.yaml in the directory
    manifest_path = os.path.join(directory, "manifest.yaml")
    if not os.path.isfile(manifest_path):
        print_error(f"No manifest.yaml file found in {directory}")
        return None
    
    return manifest_path


def create_plugin_directory(plugin_name):
    """Create a dedicated directory for the plugin"""
    # Create plugin directory path
    plugin_dir = os.path.join(os.getcwd(), "plugins", plugin_name)
    
    try:
        # Create plugin directory if it doesn't exist
        os.makedirs(plugin_dir, exist_ok=True)
        print_success(f"Created plugin directory: {plugin_dir}")
        
        # 不再创建 docs 子目录，直接将文件保存在插件目录下
        
        return plugin_dir
    except Exception as e:
        print_error(f"Failed to create plugin directory: {e}")
        return None


def create_reminder_file(plugin_dir, plugin_name):
    """Create a reminder file for developers to check and modify the generated docs"""
    reminder_path = os.path.join(plugin_dir, "IMPORTANT_NOTE.txt")
    
    try:
        with open(reminder_path, "w") as f:
            f.write(f"""IMPORTANT NOTE FOR {plugin_name.upper()} PLUGIN DEVELOPER
=====================================================

The README.md and PRIVACY.md files have been automatically generated 
based on your plugin's manifest and code structure.

BEFORE PUBLISHING YOUR PLUGIN, PLEASE:

1. Review both files thoroughly for accuracy and completeness
2. Modify/enhance the content as needed for your specific plugin
3. Ensure all sections are appropriate for your plugin
4. Add any missing information that would be helpful for users
5. Check that all links and references are correct
6. Remove any placeholder text or irrelevant sections
7. Ensure you replace the default icon.svg with a more elegant icon

These files are STARTING POINTS and may require significant editing 
depending on your plugin's complexity and unique features.

For any issues with the generated documentation, please report to the Dify team.

Generated on: {os.path.basename(__file__)} tool
=====================================================
""")
        print_success(f"Created reminder file: {os.path.basename(reminder_path)}")
        return True
    except Exception as e:
        print_error(f"Failed to create reminder file: {e}")
        return False


def clean_xml_tags(content):
    """Clean XML tags from content
    
    This function removes any XML tags that might be present in the content,
    particularly focusing on closing tags that might have been included.
    
    Args:
        content (str): The content to clean
        
    Returns:
        str: The cleaned content
    """
    # Remove common XML closing tags that might be in the content
    closing_tags = [
        "</readme>", "</README>", 
        "</privacy_policy>", "</PRIVACY_POLICY>",
        "</R>", "</P>"
    ]
    
    cleaned_content = content
    for tag in closing_tags:
        cleaned_content = cleaned_content.replace(tag, "")
    
    return cleaned_content


def save_documentation_file(plugin_dir, filename, content, file_type="markdown"):
    """Save documentation content to a file in the plugin directory
    
    Args:
        plugin_dir (str): Path to the plugin directory
        filename (str): Name of the file to save (e.g., "README.md")
        content (str): Content to write to the file
        file_type (str): Type of file for logging purposes
        
    Returns:
        bool: True if successful, False otherwise
    """
    file_path = os.path.join(plugin_dir, filename)
    
    # Clean any XML tags from the content
    cleaned_content = clean_xml_tags(content)
    
    try:
        with open(file_path, "w") as f:
            f.write(cleaned_content)
        print_success(f"Created {file_type} file: {filename}")
        return True
    except Exception as e:
        print_error(f"Failed to create {file_type} file: {e}")
        return False


def copy_docs_to_source(plugin_dir, source_dir, readme_success=False, privacy_success=False):
    """Copy generated documentation files to the source plugin directory
    
    Args:
        plugin_dir (str): Path to the generated plugin directory
        source_dir (str): Path to the original source plugin directory
        readme_success (bool): Whether README.md was successfully generated
        privacy_success (bool): Whether PRIVACY.md was successfully generated
        
    Returns:
        tuple: (readme_copied, privacy_copied) indicating success status
    """
    readme_copied = False
    privacy_copied = False
    
    # Only copy files that were successfully generated
    if readme_success:
        readme_src = os.path.join(plugin_dir, "README.md")
        readme_dst = os.path.join(source_dir, "README.md")
        
        if os.path.exists(readme_src):
            try:
                import shutil
                shutil.copy2(readme_src, readme_dst)
                print_success(f"Copied README.md to source directory: {source_dir}")
                readme_copied = True
            except Exception as e:
                print_error(f"Failed to copy README.md to source directory: {e}")
    
    if privacy_success:
        privacy_src = os.path.join(plugin_dir, "PRIVACY.md")
        privacy_dst = os.path.join(source_dir, "PRIVACY.md")
        
        if os.path.exists(privacy_src):
            try:
                import shutil
                shutil.copy2(privacy_src, privacy_dst)
                print_success(f"Copied PRIVACY.md to source directory: {source_dir}")
                privacy_copied = True
            except Exception as e:
                print_error(f"Failed to copy PRIVACY.md to source directory: {e}")
    
    return readme_copied, privacy_copied
