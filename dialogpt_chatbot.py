from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        # Load a smaller model specifically trained for dialogue
        self.model_name = "microsoft/DialoGPT-small"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.conversation_history = []
        print("Model loaded successfully!")

    def get_response(self, user_input):
        try:
            # Keep only recent history
            if len(self.conversation_history) > 4:
                self.conversation_history = self.conversation_history[-4:]
            
            # Add user input to history
            self.conversation_history.append(user_input)
            
            # Encode the input
            input_ids = self.tokenizer.encode(" ".join(self.conversation_history) + self.tokenizer.eos_token, 
                                            return_tensors='pt')
            
            # Generate response
            with torch.no_grad():
                response_ids = self.model.generate(
                    input_ids,
                    max_length=1000,
                    pad_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=3,
                    do_sample=True,
                    top_k=50,
                    top_p=0.9,
                    temperature=0.7
                )
            
            # Decode the response
            bot_response = self.tokenizer.decode(response_ids[:, input_ids.shape[-1]:][0], 
                                               skip_special_tokens=True)
            
            if bot_response.strip():
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
