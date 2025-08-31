from transformers import pipeline

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        self.generator = pipeline('text-generation', model='distilgpt2')
        self.conversation_history = []

    def get_response(self, user_input):
        try:
            if len(self.conversation_history) > 5:
                self.conversation_history = self.conversation_history[-5:]
            self.conversation_history.append(user_input)
            
            prompt = " || ".join(self.conversation_history[-3:]) + " ||"
            response = self.generator(prompt, max_length=50, num_return_sequences=1, temperature=0.7)
            
            generated_text = response[0]['generated_text']
            if "||" in generated_text:
                bot_response = generated_text.split("||")[-1].strip()
            else:
                bot_response = generated_text.strip()
            
            if bot_response and bot_response != user_input:
                self.conversation_history.append(bot_response)
                return bot_response
            return "I'm here to help. What would you like to talk about?"
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error. Let's try again."

def main():
    print("Initializing AI chatbot...")
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

if __name__ == "__main__":
    main()
