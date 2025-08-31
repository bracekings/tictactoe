from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        # Using a smaller model that works on CPU
        self.model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU
            device_map="auto"
        )
        self.conversation_history = []
        print("Model loaded successfully!")

    def get_response(self, user_input):
        try:
            # Keep conversation history manageable
            if len(self.conversation_history) > 5:
                self.conversation_history = self.conversation_history[-5:]
            
            # Create messages format
            messages = []
            for i, msg in enumerate(self.conversation_history):
                role = "assistant" if i % 2 else "user"
                messages.append({"role": role, "content": msg})
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Prepare input for the model
            inputs = self.tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                return_tensors="pt"
            ).to(self.model.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=100,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    no_repeat_ngram_size=3,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the response
            bot_response = self.tokenizer.decode(
                outputs[0][inputs.shape[1]:],
                skip_special_tokens=True
            ).strip()
            
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
