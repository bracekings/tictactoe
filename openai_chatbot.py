import os
from openai import OpenAI

class AIchatbot:
    def __init__(self):
        print("Initializing OpenAI chatbot...")
        
        # Get API key from environment variable
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable")
            
        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)
        
        # Initialize conversation history
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful, friendly, and concise AI assistant. You provide clear and accurate responses."}
        ]
        print("Chatbot initialized successfully!")

    def get_response(self, user_input):
        try:
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Keep conversation history manageable (last 10 messages)
            if len(self.conversation_history) > 11:  # 1 system message + 10 conversation messages
                self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-10:]
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=150,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.6
            )
            
            # Extract the response text
            bot_response = response.choices[0].message.content.strip()
            
            # Add assistant's response to history
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error. Please make sure your OpenAI API key is set correctly and try again."

def main():
    try:
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

    except ValueError as e:
        print(f"\nError: {str(e)}")
        print("Please set your OpenAI API key using:")
        print("$env:OPENAI_API_KEY='your-api-key-here'")

if __name__ == "__main__":
    main()
