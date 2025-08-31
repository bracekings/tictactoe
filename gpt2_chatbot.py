import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer

class Chatbot:
    def __init__(self):
        print("Initializing AI chatbot...")
        print("Loading the model (this might take a minute)...")
        
        # Load tokenizer
        print("Loading tokenizer...")
        self.tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        print("Loading model...")
        self.model = GPT2LMHeadModel.from_pretrained('gpt2')
        self.model.eval()
        
        # Initialize conversation history
        self.conversation_history = []
        print("\nModel loaded successfully!")

    def format_prompt(self, user_input):
        # Format the conversation history and current input
        prompt = "The following is a conversation with an AI assistant. The assistant is helpful, creative, clever, and very friendly.\n\n"
        
        for h in self.conversation_history[-3:]:  # Only keep last 3 exchanges for context
            prompt += f"Human: {h[0]}\nAssistant: {h[1]}\n"
        
        prompt += f"Human: {user_input}\nAssistant:"
        return prompt

    def get_response(self, user_input):
        try:
            # Format the prompt with conversation history
            prompt = self.format_prompt(user_input)
            
            # Encode the prompt
            encoded = self.tokenizer(prompt, return_tensors='pt', truncation=True, max_length=512)
            input_ids = encoded['input_ids']
            attention_mask = encoded['attention_mask']
            
            # Calculate max_new_tokens based on input length
            input_length = len(input_ids[0])
            max_new_tokens = min(100, 512 - input_length)  # Keep total length under 512
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=max_new_tokens,
                    num_return_sequences=1,
                    temperature=0.7,  # Slightly lower temperature for more focused responses
                    top_k=50,
                    top_p=0.92,
                    pad_token_id=self.tokenizer.eos_token_id,
                    do_sample=True,
                    no_repeat_ngram_size=3,  # Prevent more repetition
                    num_beams=3,  # Use beam search for better quality
                    early_stopping=True
                )
            
            # Decode and clean up the response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the assistant's response
            response = full_response[len(prompt):].split("Human:")[0].strip()
            
            # Clean up any incomplete sentences
            if response:
                sentences = response.split('.')
                if len(sentences) > 1:
                    response = '.'.join(sentences[:-1]) + '.'
            
            # If response is empty or too short, provide a fallback
            if not response or len(response) < 2:
                response = "I'm happy to help! What would you like to discuss?"
            
            # Update conversation history
            self.conversation_history.append((user_input, response))
            if len(self.conversation_history) > 5:
                self.conversation_history.pop(0)
            
            return response
        
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error. Could you please try again?"

def main():
    chatbot = Chatbot()
    print("\nAI Chatbot is ready! Type 'quit' to exit.")
    print("You can ask me anything!")
    print("-" * 50 + "\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'quit':
            print("Goodbye!")
            break
        
        response = chatbot.get_response(user_input)
        print(f"Assistant: {response}\n")

if __name__ == "__main__":
    main()
