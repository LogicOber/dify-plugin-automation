"""
API handling utilities for Dify
"""
import os
import requests
import json
import time
from utils.formatting import print_error, print_info, print_success, print_warning, print_progress

def extract_content_from_response(full_response, plugin_dir=None, save_docs=True):
    """
    Extract README and PRIVACY content from the full API response
    
    Args:
        full_response (str): The complete API response text
        plugin_dir (str): Directory to save extracted files (if save_docs is True)
        save_docs (bool): Whether to save extracted content to files
        
    Returns:
        tuple: (readme_content, privacy_content, readme_complete, privacy_complete)
    """
    # 保存完整响应但不输出日志
    if plugin_dir:
        full_response_path = os.path.join(plugin_dir, "full_response.txt")
        try:
            with open(full_response_path, "w") as f:
                f.write(full_response)
        except Exception as e:
            pass  # 忽略保存错误
    
    # Initialize variables
    readme_content = ""
    privacy_content = ""
    readme_complete = False
    privacy_complete = False
    
    # Extract README content
    readme_start = full_response.lower().find("<readme>")
    if readme_start != -1:
        readme_start += len("<readme>")
        readme_end = full_response.lower().find("</readme>", readme_start)
        if readme_end != -1:
            readme_content = full_response[readme_start:readme_end].strip()
            readme_complete = True
        else:
            # Try to get partial content if no end tag
            readme_content = full_response[readme_start:].strip()
    
    # Extract PRIVACY content
    privacy_start = full_response.lower().find("<privacy_policy>")
    if privacy_start != -1:
        privacy_start += len("<privacy_policy>")
        privacy_end = full_response.lower().find("</privacy_policy>", privacy_start)
        if privacy_end != -1:
            privacy_content = full_response[privacy_start:privacy_end].strip()
            privacy_complete = True
        else:
            # Try to get partial content if no end tag
            privacy_content = full_response[privacy_start:].strip()
    
    # Save extracted content to files if requested
    if save_docs and plugin_dir:
        from utils.file_operations import save_documentation_file
        
        # 简化文件保存日志
        if readme_content:
            save_documentation_file(plugin_dir, "README.md", readme_content, "README")
        
        if privacy_content:
            save_documentation_file(plugin_dir, "PRIVACY.md", privacy_content, "PRIVACY")
    
    return readme_content, privacy_content, readme_complete, privacy_complete


def call_dify_api(plugin_dir, manifest_info, inputs, query, max_retries=0, save_docs=True):
    """Call Dify API with extracted information
    
    Args:
        plugin_dir: Directory where the plugin is located
        manifest_info: Information extracted from manifest.yaml
        inputs: Dictionary of inputs for the API call
        query: Query string for the API call
        max_retries: Maximum number of retries for API call
    
    Returns:
        API response if successful, None otherwise
    """
    # Get API credentials and settings from environment variables
    dify_base_url = os.getenv("DIFY_BASE_URL", "https://api.dify.ai/v1")
    dify_api_key = os.getenv("DIFY_API_KEY")
    
    # API endpoint for chat completions
    endpoint = f"{dify_base_url}/chat-messages"
    
    # Headers for API request
    headers = {
        "Authorization": f"Bearer {dify_api_key}",
        "Content-Type": "application/json"
    }
    
    # Current attempt counter
    current_attempt = 0
    max_attempts = max_retries + 1
    
    # Variable to store error details
    error_details = ""
    
    while current_attempt < max_attempts:
        current_attempt += 1
        
        # Debug information
        print_progress(f"API Call Attempt {current_attempt}/{max_attempts}")
        
        try:
            # Prepare request data
            data = {
                "inputs": inputs,
                "query": query,
                "response_mode": "streaming",  # Changed from blocking to streaming
                "conversation_id": None,
                "user": "readme-generator"
            }
            
            # 显示代码结构大小，确保发送完整内容
            code_size = len(str(inputs.get('code_files', ''))) if 'code_files' in inputs else 0
            print_info(f"Sending API request to Dify with {code_size} characters of code structure...")
            
            # For streaming mode, we need to process the response differently
            response = requests.post(
                endpoint,
                headers=headers,
                json=data,
                stream=True,  # Enable streaming
                timeout=60 * 10  # 10 minute timeout
            )
            
            # Check if response is successful
            if response.status_code == 200:
                # 简化API响应日志
                print_success(f"API Response: {response.status_code} OK (Streaming)")
                
                # Initialize variables to collect the response
                full_response = ""
                answer = ""
                
                # We'll collect the full response and extract content later
                # No need to track XML tags during streaming
                
                # Process the streaming response
                try:
                    for line in response.iter_lines():
                        if line:
                            # Debug raw response for troubleshooting
                            line_text = line.decode('utf-8')
                            # Only print data lines with actual content
                            if line_text.startswith('data:') and len(line_text) > 10 and not 'event' in line_text:
                                print_info(f"Data received: {len(line_text)} chars")
                            
                            # Handle SSE format - lines start with 'data: '
                            if line_text.startswith('data: '):
                                # Extract the JSON part
                                json_str = line_text[6:]  # Skip 'data: '
                                try:
                                    # Parse the JSON data
                                    line_data = json.loads(json_str)
                                    
                                    # 不再打印进度信息
                                    pass
                                    
                                    # Extract the answer based on event type
                                    if 'event' in line_data:
                                        if line_data['event'] == 'message':
                                            # Direct answer chunk in the message event
                                            if 'answer' in line_data:
                                                answer_chunk = line_data['answer']
                                                answer += answer_chunk
                                                full_response += answer_chunk
                                                
                                                # 完全删除处理块的信息输出
                                                
                                                # 不再输出任何标签信息
                                        
                                        # Check for end of stream
                                        elif line_data['event'] == 'message_end':
                                            print_success("Response received successfully")
                                            break
                                except json.JSONDecodeError as e:
                                    print_warning(f"Skipping invalid JSON in stream: {e}")
                            else:
                                # Skip non-data lines (like empty lines for keep-alive)
                                pass
                    
                    print_info("Extracting documentation content...")
                    
                    # 使用新的提取函数处理完整响应
                    readme_content, privacy_content, readme_complete, privacy_complete = extract_content_from_response(
                        answer, plugin_dir, save_docs
                    )
                    
                    # 创建响应对象
                    api_response = {
                        "answer": answer,
                        "readme_content": readme_content,
                        "privacy_content": privacy_content,
                        "readme_complete": readme_complete,
                        "privacy_complete": privacy_complete
                    }
                    
                    # Return successful response and empty error details
                    return api_response, ""
                    
                except Exception as e:
                    # Log error in processing streaming response
                    error_message = f"Error processing streaming response: {str(e)}"
                    print_error(error_message)
                    error_details = error_message
                    
                    # 如果收集到了一些响应，尝试使用它
                    if answer:
                        print_warning("Using partial response due to streaming error")
                        
                        # 尝试从部分响应中提取内容
                        readme_content, privacy_content, readme_complete, privacy_complete = extract_content_from_response(
                            answer, plugin_dir, save_docs
                        )
                        
                        # 创建部分响应对象
                        partial_response = {
                            "answer": answer,
                            "readme_content": readme_content,
                            "privacy_content": privacy_content,
                            "readme_complete": readme_complete,
                            "privacy_complete": privacy_complete
                        }
                        
                        return partial_response, error_details
                
                # If we get here without returning, there was an issue with the response format
                error_message = "API streaming response format is unexpected"
                print_error(error_message)
                error_details = f"{error_message}\nPartial Response: {full_response[:500]}..."
                
                # Retry if this is not the last attempt
                if current_attempt < max_attempts:
                    print_warning(f"Retrying API call ({current_attempt}/{max_attempts})...")
                    time.sleep(2)  # Wait 2 seconds before retrying
                    continue
            else:
                # Log error
                error_message = f"API request failed with status code: {response.status_code}"
                print_error(error_message)
                error_details = f"{error_message}\nResponse: {response.text}"
                
                # Retry if this is not the last attempt
                if current_attempt < max_attempts:
                    print_warning(f"Retrying API call ({current_attempt}/{max_attempts})...")
                    time.sleep(2)  # Wait 2 seconds before retrying
                    continue
        
        except Exception as e:
            # Log error
            error_message = f"Exception during API call: {str(e)}"
            print_error(error_message)
            error_details = error_message
            
            # Retry if this is not the last attempt
            if current_attempt < max_attempts:
                print_warning(f"Retrying API call ({current_attempt}/{max_attempts})...")
                time.sleep(2)  # Wait 2 seconds before retrying
                continue
    
    # All attempts failed
    print_error(f"All API call attempts failed ({max_attempts} attempts)")
    return None, error_details
