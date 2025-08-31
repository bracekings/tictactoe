from transformers import pipeline
import os

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        # Using a small model that's quick to load
        self.generator = pipeline('text-generation', model='distilgpt2')
        self.conversation_history = []

    def get_response(self, user_input):
        try:
            # Keep conversation context manageable
            if len(self.conversation_history) > 5:
                self.conversation_history = self.conversation_history[-5:]
            
            # Add user input to history
            self.conversation_history.append(user_input)
            
            # Create prompt from conversation history
            prompt = " || ".join(self.conversation_history[-3:]) + " ||"
            
            # Generate response
            response = self.generator(
                prompt,
                max_length=50,
                num_return_sequences=1,
                temperature=0.7,
                pad_token_id=50256
            )
            
            # Parse the response
            try:
                response_json = response.json()
                print(f"Response received: {response.status_code}")
                
                if isinstance(response_json, list) and len(response_json) > 0:
                    bot_response = response_json[0].get('generated_text', '').strip()
                    
                    # Clean up the response
                    if bot_response:
                        # Remove any extra "Assistant:" or "User:" prefixes
                        if "Assistant:" in bot_response:
                            bot_response = bot_response.split("Assistant:", 1)[1]
                        if "User:" in bot_response:
                            bot_response = bot_response.split("User:", 1)[0]
                        
                        bot_response = bot_response.strip()
                        if bot_response:
                            self.conversation_history.append(bot_response)
                            return bot_response
                
                return "I'm here to help. What would you like to talk about?"
                
            except Exception as e:
                print(f"Error processing response: {str(e)}")
                if response.status_code == 503:
                    return "I'm currently loading. Please try again in a few seconds."
                elif response.status_code == 404:
                    return "I'm having trouble accessing my language model. Please check the model configuration."
                else:
                    return "I encountered an error. Let's try again."
            
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
