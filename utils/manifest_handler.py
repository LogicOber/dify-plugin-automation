"""
Manifest file handling utilities
"""
import os
import yaml
import json
from utils.formatting import print_error, print_info, print_success, print_progress

def extract_manifest_info(plugin_path):
    """Extract information from manifest.yaml"""
    manifest_path = os.path.join(plugin_path, "manifest.yaml")
    
    try:
        # Attempt to open and parse the manifest file
        print_progress(f"Reading manifest from: {manifest_path}")
        with open(manifest_path, "r") as f:
            manifest_data = yaml.safe_load(f)
        
        # Debug output of parsed manifest
        print_info(f"Successfully parsed manifest for plugin: {manifest_data.get('name', 'Unknown')}")
        
        # Extract essential information
        info = {
            "name": manifest_data.get("name", ""),
            "description": manifest_data.get("description", ""),
            "version": manifest_data.get("version", ""),
            "author": manifest_data.get("author", ""),
            "type": manifest_data.get("type", ""),
            "repository": manifest_data.get("repository", {}).get("url", "")
        }
        
        # Add other useful information if available
        if "ui" in manifest_data:
            info["ui"] = manifest_data["ui"]
        if "api" in manifest_data:
            info["api"] = manifest_data["api"]
        if "dependencies" in manifest_data:
            info["dependencies"] = manifest_data["dependencies"]
        
        print_success(f"Extracted manifest info for: {info['name']} v{info['version']}")
        return info
    
    except Exception as e:
        print_error(f"Failed to extract manifest info: {e}")
        return None
