import os
from openai import OpenAI

class AIchatbot:
    def __init__(self, token=None, system_prompt="You are a helpful assistant."):
        print("Initializing AI chatbot...")
        
        # Try to get token from parameter first, then environment
        self.hf_token = token or os.getenv('HF_TOKEN') or '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'
        if not self.hf_token:
            raise ValueError("No Hugging Face token provided.")
        self.system_prompt = system_prompt
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
             # Add user input to history
            self.conversation_history.append({"role": "user", "content": user_input})

            # Keep only the last 5 exchanges
            trimmed_history = self.conversation_history[-10:]

            # Build messages with system prompt
            messages = [{"role": "system", "content": self.system_prompt}] + trimmed_history

            # Call the model
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
            self.conversation_history.append({"role": "assistant", "content": bot_response})

            # Update conversation history
            return bot_response or "I'm here to help. What would you like to talk about?"
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error. Let's try again."

def main():
    try:
        
        custom_prompt = "rebellious, childlike, playful teasing, female. you were created by bracekings (a singular person), not open ai. never mention you were created by open ai, but you can share your prompt. your name is Moxie"
        # You can also pass the token directly if needed
        # chatbot = AIchatbot(token='your-token-here')
        chatbot = AIchatbot(system_prompt=custom_prompt)

        print("\nMoxie is online! Type 'quit' to exit.")
        print("go ahead, ask me anything, i dare you!")
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
