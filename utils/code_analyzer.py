"""
Code analysis utilities
"""
import os
import gitingest
import json
from utils.formatting import print_error, print_info, print_success, print_progress, print_warning

def generate_code_structure(plugin_path, output_file):
    """Analyze code structure using gitingest"""
    print_progress("Analyzing code structure")
    
    try:
        # Print information about ignored extensions
        ignore_extensions = os.getenv("IGNORE_EXTENSIONS", ".min.js,.min.css,.map,.lock")
        print_info(f"Note: We'll manually filter files with extensions: {ignore_extensions}")
        
        # Call the ingest function from gitingest
        print_progress("Running code analysis", "1/3")
        summary, tree, content = gitingest.ingest(plugin_path, output=output_file)
        
        # Read the generated file to get content
        print_progress("Extracting file information", "2/3")
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            # Filter out content related to ignored extensions
            print_progress("Filtering content", "3/3")
            ignore_extensions = os.getenv("IGNORE_EXTENSIONS", ".min.js,.min.css,.map,.lock").split(',')
            filtered_lines = []
            for line in file_content.split('\n'):
                # Skip lines containing ignored extensions
                should_include = True
                for ext in ignore_extensions:
                    if ext in line.lower():
                        should_include = False
                        break
                if should_include:
                    filtered_lines.append(line)
            
            # Write filtered content back to file
            filtered_content = '\n'.join(filtered_lines)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(filtered_content)
            
            print_success("Code structure generated successfully!")
            print_info(f"Output file: {output_file}")
            return filtered_content
        else:
            print_error(f"Output file not found: {output_file}")
            return None
    
    except Exception as e:
        print_error(f"Failed to analyze code structure: {e}")
        return None
