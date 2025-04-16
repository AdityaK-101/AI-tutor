import requests
import os
import sys
import time
from typing import Dict, Any, List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import HF_API_TOKEN, HF_API_URL

class ChatInterface:
    def __init__(self):
        if not HF_API_TOKEN:
            raise ValueError("Hugging Face API token not found. Please check your .env file.")
        self.headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    def _make_request(self, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """Make request to HF API with retry mechanism"""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    HF_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()
                
                # Handle specific status codes
                if response.status_code == 503:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        time.sleep(wait_time)
                        continue
                    return "Service is currently unavailable. Please try again later."
                
                if response.status_code == 403:
                    return "Error: Invalid API token. Please check your Hugging Face API token."
                
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return "Too many requests. Please try again later."
                
                return f"Error: API request failed with status code {response.status_code}"
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                return "Request timed out. Please try again."
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    continue
                return f"Network error occurred: {str(e)}"
    
    def get_ai_response(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Get AI response with conversation context
        
        Args:
            prompt: The user's current message
            conversation_history: List of previous messages in the format [{"role": "user/assistant", "content": "message"}]
        
        Returns:
            The AI's response
        """
        try:
            # Format the conversation history
            conversation_context = ""
            if conversation_history:
                try:
                    conversation_context = "Previous conversation:\n"
                    # Include the last 5 exchanges for context
                    for msg in conversation_history[-10:]:  # Get last 10 messages (5 exchanges)
                        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                            continue  # Skip invalid messages
                        role = "User" if msg["role"] == "user" else "Assistant"
                        conversation_context += f"{role}: {msg['content']}\n\n"
                except Exception as e:
                    print(f"Error formatting conversation history: {e}")
                    # Continue with empty context if there's an error
            
            # Create the full prompt with context
            formatted_prompt = f"""[INST] You are a coding tutor. Use the following conversation history as context for your response:

{conversation_context}Current question:

{prompt}

[/INST]"""
            
            payload = {
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": 1024,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "return_full_text": False,
                    "stop": ["[INST]", "Student's question:", "Tutor's response:"]
                }
            }
            
            response = self._make_request(payload)
            
            if isinstance(response, str):
                return response
                
            try:
                if isinstance(response, list):
                    response_text = response[0].get('generated_text', '')
                elif isinstance(response, dict):
                    response_text = response.get('generated_text', '')
                else:
                    response_text = str(response)
                
                # Clean up the response
                response_text = response_text.replace("Student's question:", "")
                response_text = response_text.replace("Tutor's response:", "")
                response_text = response_text.strip()
                
                return response_text
                
            except Exception as e:
                print(f"Error processing response: {e}")
                return f"Error processing response: {str(e)}"
                
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred: {str(e)}"

    def _format_response(self, response: str) -> str:
        """Format the response for better readability"""
        try:
            # Add markdown formatting for code blocks
            lines = response.split('\n')
            formatted_lines = []
            in_code_block = False
            
            for line in lines:
                # Detect code snippets and wrap them in markdown code blocks
                if '```' in line:
                    in_code_block = not in_code_block
                    formatted_lines.append(line)
                elif any(code_indicator in line for code_indicator in ['def ', 'class ', 'import ', '    ']):
                    if not in_code_block:
                        formatted_lines.append('```python')
                        in_code_block = True
                    formatted_lines.append(line)
                else:
                    if in_code_block:
                        formatted_lines.append('```')
                        in_code_block = False
                    formatted_lines.append(line)
            
            # Ensure code block is closed
            if in_code_block:
                formatted_lines.append('```')
            
            # Add bullet points for lists
            response = '\n'.join(formatted_lines)
            
            # Add bold formatting for important concepts
            for keyword in ['Note:', 'Important:', 'Remember:', 'Tip:', 'Warning:']:
                response = response.replace(f'{keyword}', f'**{keyword}**')
            
            # Add horizontal lines between sections
            response = response.replace('\n\n', '\n---\n')
            
            return response
            
        except Exception as e:
            # If formatting fails, return original response
            return response

# Export the class
__all__ = ['ChatInterface'] 