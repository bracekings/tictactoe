import os
from openai import OpenAI

class AIchatbot:
    def __init__(self, token=None):
        print("Initializing AI chatbot...")
        
        # Try to get token from parameter first, then environment
        self.hf_token = token or os.getenv('HF_TOKEN') or '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'
        
        # Initialize OpenAI client with Hugging Face router
        try:
            self.client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=self.hf_token
            )
            
            # Initialize conversation history
            self.conversation_history = []
            print("Chatbot initialized successfully!")
            
        except Exception as e:
            print(f"Error initializing chatbot: {str(e)}")
            raise ValueError("Failed to initialize chatbot. Please check your Hugging Face token.")

    def get_response(self, user_input):
        try:
            # Keep conversation history manageable
            if len(self.conversation_history) > 5:
                self.conversation_history = self.conversation_history[-5:]
            
            # Format messages for the API
            messages = []
            for i, msg in enumerate(self.conversation_history):
                role = "assistant" if i % 2 else "user"
                messages.append({"role": role, "content": msg})
            
            # Add current user message
            messages.append({"role": "user", "content": user_input})
            
            # Get response from the model
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-120b:together",
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.6
            )
            
            # Extract the response
            bot_response = completion.choices[0].message.content.strip()
            
            # Update conversation history
            self.conversation_history.append(user_input)
            if bot_response:
                self.conversation_history.append(bot_response)
                return bot_response
            return "I'm here to help. What would you like to talk about?"
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error. Let's try again."

def main():
    try:
        # You can also pass the token directly if needed
        # chatbot = AIchatbot(token='your-token-here')
        chatbot = AIchatbot()

        print("\nAI Chatbot is ready! Type 'quit' to exit.")
        print("You can ask me anything!")
        print("-" * 50)

        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye!")
                break

            response = chatbot.get_response(user_input)
            print(f"\nChatbot: {response}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you have a valid Hugging Face token")
        print("2. Check your internet connection")
        print("3. Try setting the token manually:")
        print("   $env:HF_TOKEN='your-token-here'")

if __name__ == "__main__":
    main()
