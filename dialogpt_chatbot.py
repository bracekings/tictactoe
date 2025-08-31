from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        # Using GPT-2 medium for better quality responses
        self.model_name = "gpt2-medium"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        
        # Configure the tokenizer
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model.eval()  # Set to evaluation mode
        
        # Initialize conversation history with system prompt
        self.conversation_history = ["You are a helpful, respectful, and honest AI assistant."]
        print("Model loaded successfully!")

    def get_response(self, user_input):
        try:
            # Keep only recent history
            if len(self.conversation_history) > 4:
                self.conversation_history = self.conversation_history[-4:]
            
            # Format the conversation
            prompt = "\n".join(self.conversation_history[-4:])  # Keep last few exchanges for context
            prompt += f"\nHuman: {user_input}\nAssistant:"
            
            # Encode the input with attention mask
            encoded = self.tokenizer(prompt, return_tensors='pt', truncation=True, max_length=512)
            input_ids = encoded['input_ids']
            attention_mask = encoded['attention_mask']
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=100,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.9,
                    do_sample=True,
                    no_repeat_ngram_size=3,
                    num_beams=3,
                    early_stopping=True
                )
            
            # Extract the new content
            response = self.tokenizer.decode(outputs[0][input_ids.shape[-1]:], skip_special_tokens=True)
            
            # Clean up the response
            response = response.strip()
            if not response or len(response) < 2:
                response = "I understand. How can I help you further?"
                
            # Update conversation history
            self.conversation_history.append(f"Human: {user_input}")
            self.conversation_history.append(f"Assistant: {response}")
            
            return response
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
