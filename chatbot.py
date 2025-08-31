import requests
import os
import json

class AIchatbot:
    def __init__(self):
        # Initialize with your API token
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.api_token:
            raise ValueError("HUGGINGFACE_API_TOKEN environment variable is not set")
        self.conversation_history = []
        # Using DialoGPT-medium for chat
        self.model = "microsoft/DialoGPT-medium"

    def get_response(self, user_input):
        try:
            # Keep conversation context manageable
            if len(self.conversation_history) > 5:
                self.conversation_history = self.conversation_history[-5:]
            
            # Add user input to history
            self.conversation_history.append(user_input)
            
            # Make API request to Hugging Face
            api_url = "https://api-inference.huggingface.co/models/gpt2"
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            # Prepare the payload
            payload = {
                "inputs": user_input,
                "parameters": {
                    "max_length": 50,
                    "num_return_sequences": 1
                }
            }
            
            # Make the request
            print("Sending request to DialoGPT...")
            response = requests.post(api_url, headers=headers, json=payload)
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"API Error: Status {response.status_code}")
                print(f"Response: {response.text}")
                return "I'm having trouble connecting. Please try again."
            
            # Parse the response
            try:
                response_json = response.json()
                print(f"Raw response: {response_json}")
                if isinstance(response_json, list) and len(response_json) > 0:
                    bot_response = response_json[0].get('generated_text', '').strip()
                    if bot_response:
                        self.conversation_history.append(bot_response)
                        return bot_response
                return "I'm not sure how to respond to that."
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                print(f"Raw response content: {response.content}")
                return "I'm having trouble understanding the response."
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {str(e)}")
            return f"Error: Network issue - {str(e)}"
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return f"Error: {str(e)}"

def initialize_chatbot():
    return AIchatbot()

def generate_response(chatbot, user_input, conversation_history=None):

    # Generate a response
    # Encode the input
    # Get response using OpenAI
    response = chatbot.get_response(user_input)
    return response

def main():
    if not os.getenv("HUGGINGFACE_API_TOKEN"):
        print("Error: Please set the HUGGINGFACE_API_TOKEN environment variable")
        return

    print("Initializing AI chatbot...")
    chatbot = initialize_chatbot()
    conversation_history = None

    print("\nAI Chatbot is ready! Type 'quit' to exit.")
    print("You can ask me anything!")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        response = generate_response(chatbot, user_input, conversation_history)
        print(f"\nChatbot: {response}")
        
        # Update conversation history
        conversation_history = response

if __name__ == "__main__":
    main()
