from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        # Use the base GPT-2 model for better stability
        self.model_name = "gpt2"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        self.chat_history = ""

        # Configure the model and tokenizer
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model.config.pad_token_id = self.model.config.eos_token_id
        self.model.eval()
        
        print("Model loaded successfully!")

    def get_response(self, user_input):
        try:
            # Create a simple prompt format
            system_prompt = "You are a witty, friendly AI assistant who loves helping people."
            prompt = f"{system_prompt}\n{self.chat_history}"
            self.chat_history += f"Human: {user_input}\nAssistant:"
            prompt = self.chat_history
            # Limit history to last 4 exchanges


        
            # Encode with attention mask
            inputs = self.tokenizer(prompt, return_tensors='pt', truncation=True, max_length=512)
            input_ids = inputs['input_ids']
            attention_mask = inputs['attention_mask']
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=50,
                    num_return_sequences=1,
                    temperature=0.7,
                    top_k=50,
                    top_p=0.95,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=2,
                    early_stopping=True
                )
            
            # Decode the response and clean it up
            response = self.tokenizer.decode(outputs[0][len(input_ids[0]):], skip_special_tokens=True)
            
            # Clean up any incomplete sentences
            sentences = response.split('.')
            if len(sentences) > 1:
                response = '.'.join(sentences[:-1]) + '.'
            
            response = response.strip()
            
            # Fallback for empty responses
            if not response:
                return "I understand. How can I help you further?"

            self.chat_history += f" {response}\n"   
            
            return response
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I encountered an error. Could you please try again?"

import time
def simulate_typing(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.02)
    print()

import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

def main():
    chatbot = AIchatbot()
    print("\nAI Chatbot is ready! Type 'quit' to exit.")
    print("You can ask me anything!")
    print("-" * 50 + "\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == 'quit':
            print("\nGoodbye!")
            break
        
        response = chatbot.get_response(user_input)
        print("\nAssistant: ", end='')
        simulate_typing(response)
        print()


if __name__ == "__main__":
    main()
