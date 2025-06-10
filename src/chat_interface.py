import requests
import os
import sys
import time
from typing import Dict, Any, List, Tuple

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.config import HF_API_TOKEN, HF_API_URL

class ChatInterface:
    """
    Handles interactions with the Hugging Face API for generating AI responses.

    This class is responsible for making requests to the specified Hugging Face
    Inference API endpoint, including handling authentication, request formatting,
    and retry mechanisms for API calls.
    """
    def __init__(self):
        """
        Initializes the ChatInterface.

        Checks for the Hugging Face API token and sets up the authorization headers
        for API requests.

        Raises:
            ValueError: If the Hugging Face API token is not found.
        """
        if not HF_API_TOKEN:
            raise ValueError("Hugging Face API token not found. Please check your .env file.")
        self.headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
    def _make_request(self, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """
        Makes a request to the Hugging Face API with a retry mechanism.

        Args:
            payload: The JSON payload for the API request.
            max_retries: The maximum number of times to retry the request.

        Returns:
            The API response as a JSON object or an error message string.
        """
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    HF_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30 # Set a timeout for the request
                )
                
                # Successful response
                if response.status_code == 200:
                    return response.json() # Return the JSON response
                
                # Handle specific HTTP error codes with retry logic
                if response.status_code == 503: # Service Unavailable
                    if attempt < max_retries - 1:
                        # Exponential backoff with a small factor for retries
                        wait_time = (attempt + 1) * 2
                        time.sleep(wait_time)
                        continue # Retry the request
                    return "Service is currently unavailable. Please try again later."
                
                if response.status_code == 403: # Forbidden (likely auth issue)
                    return "Error: Invalid API token. Please check your Hugging Face API token."
                
                if response.status_code == 429: # Too Many Requests
                    if attempt < max_retries - 1:
                        # Exponential backoff for rate limiting
                        time.sleep(2 ** attempt)
                        continue # Retry the request
                    return "Too many requests. Please try again later."
                
                # For other error codes, return a generic error message
                return f"Error: API request failed with status code {response.status_code}"
                
            except requests.exceptions.Timeout: # Handle request timeout
                if attempt < max_retries - 1:
                    continue # Retry on timeout
                return "Request timed out. Please try again."
            
            except requests.exceptions.RequestException as e: # Handle other network errors
                if attempt < max_retries - 1:
                    continue # Retry on other request exceptions
                return f"Network error occurred: {str(e)}"
    
    def get_ai_response(self, prompt: str, conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Gets an AI response from the Hugging Face API, considering conversation history.

        Args:
            prompt: The user's current message/question.
            conversation_history: A list of previous messages in the format
                                  [{"role": "user/assistant", "content": "message"}].
                                  Defaults to None.

        Returns:
            The AI's generated response as a string.
        """
        try:
            # Format the conversation history to be included in the prompt
            conversation_context = ""
            if conversation_history:
                try:
                    conversation_context = "Previous conversation:\n"
                    # Include up to the last 10 messages (5 user, 5 assistant) for context
                    for msg in conversation_history[-10:]:
                        # Basic validation of message structure
                        if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                            continue  # Skip malformed messages
                        role = "User" if msg["role"] == "user" else "Assistant"
                        conversation_context += f"{role}: {msg['content']}\n\n" # Double newline for separation
                except Exception as e:
                    # Log error during history formatting but proceed without context
                    print(f"Error formatting conversation history: {e}")
                    # conversation_context remains empty or partially filled
            
            # Construct the full prompt using a specific instruction format ([INST]...[/INST])
            # This format is often used by instruction-tuned models.
            formatted_prompt = f"""[INST] You are a coding tutor. Use the following conversation history as context for your response:

{conversation_context}Current question:

{prompt}

[/INST]"""
            
            # Define the payload for the Hugging Face API
            payload = {
                "inputs": formatted_prompt,
                "parameters": { # Parameters to control the generation
                    "max_new_tokens": 1024,    # Max length of the generated response
                    "temperature": 0.7,        # Controls randomness (lower is more deterministic)
                    "top_p": 0.95,             # Nucleus sampling: considers a subset of probable tokens
                    "return_full_text": False, # Only return the generated part, not the input prompt
                    "stop": ["[INST]", "Student's question:", "Tutor's response:"] # Stop sequences
                }
            }
            
            # Make the API request
            response = self._make_request(payload)
            
            # If _make_request returned an error string, propagate it
            if isinstance(response, str):
                return response
                
            # Process the successful JSON response
            try:
                # The structure of the response can vary based on the HF model/API version
                if isinstance(response, list) and response: # Often a list with one element
                    response_text = response[0].get('generated_text', '')
                elif isinstance(response, dict): # Sometimes a direct dictionary
                    response_text = response.get('generated_text', '')
                else:
                    # Fallback if the response structure is unexpected
                    response_text = str(response)
                
                # Basic cleanup of the response text
                # These might be artifacts from the model's training or prompt structure
                response_text = response_text.replace("Student's question:", "")
                response_text = response_text.replace("Tutor's response:", "")
                response_text = response_text.strip() # Remove leading/trailing whitespace
                
                return response_text
                
            except Exception as e:
                # Error during response processing
                print(f"Error processing response: {e}")
                return f"Error processing response: {str(e)}"
                
        except Exception as e:
            # Catch-all for any other unexpected errors
            print(f"An unexpected error occurred in get_ai_response: {e}")
            return f"An unexpected error occurred: {str(e)}"

    def _format_response(self, response: str) -> str:
        """
        Formats the AI's response for better readability.

        This method attempts to apply markdown formatting for code blocks,
        bold important keywords, and add horizontal lines for section separation.

        Args:
            response: The raw AI response string.

        Returns:
            The formatted response string. If formatting fails, returns the original response.
        """
        try:
            # Add markdown formatting for code blocks
            # This is a basic attempt to format; more sophisticated markdown parsing might be needed
            lines = response.split('\n')
            formatted_lines = []
            in_code_block = False # Flag to track if currently inside a code block
            
            for line in lines:
                # Heuristic to detect start/end of code blocks or Python code
                if '```' in line: # Explicit markdown code block
                    in_code_block = not in_code_block
                    formatted_lines.append(line)
                # Simple heuristic: if a line looks like Python code (contains def, class, import, or is indented)
                elif any(code_indicator in line for code_indicator in ['def ', 'class ', 'import ', '    ']):
                    if not in_code_block:
                        formatted_lines.append('```python') # Assume Python code
                        in_code_block = True
                    formatted_lines.append(line)
                else: # Not a code line
                    if in_code_block: # If was in a code block, close it
                        formatted_lines.append('```')
                        in_code_block = False
                    formatted_lines.append(line)
            
            # Ensure any open code block is closed at the end
            if in_code_block:
                formatted_lines.append('```')
            
            formatted_response = '\n'.join(formatted_lines)
            
            # Add bold formatting for common emphasis keywords
            for keyword in ['Note:', 'Important:', 'Remember:', 'Tip:', 'Warning:']:
                formatted_response = formatted_response.replace(f'{keyword}', f'**{keyword}**')
            
            # Replace double newlines with a horizontal rule for better section separation
            # This might be too aggressive depending on desired output style
            # formatted_response = formatted_response.replace('\n\n', '\n---\n')
            
            return formatted_response
            
        except Exception as e:
            # If any error occurs during formatting, return the original response
            # This ensures that the user still gets the AI's content
            print(f"Error during response formatting: {e}")
            return response

# Export the class for use in other modules (e.g., from src import ChatInterface)
__all__ = ['ChatInterface'] 