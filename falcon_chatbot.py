from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class AIchatbot:
    def __init__(self):
        print("Loading the model (this might take a minute)...")
        # Using Falcon-7B-Instruct, optimized for chat and instruction following
        self.model_name = "tiiuae/falcon-7b-instruct"
        
        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            padding_side="left"
        )
        
        print("Loading model...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU
            device_map="auto",
            low_cpu_mem_usage=True
        )
        self.conversation_history = []
        print("Model loaded successfully!")

    def format_prompt(self, user_input):
        # Format the conversation history and current input
        if not self.conversation_history:
            return f"User: {user_input}\nAssistant:"
        
        prompt = ""
        for i, message in enumerate(self.conversation_history):
            role = "Assistant" if i % 2 else "User"
            prompt += f"{role}: {message}\n"
        prompt += f"User: {user_input}\nAssistant:"
        return prompt

    def get_response(self, user_input):
        try:
            # Keep conversation context manageable
            if len(self.conversation_history) > 4:
                self.conversation_history = self.conversation_history[-4:]
            
            # Create the prompt
            prompt = self.format_prompt(user_input)
            
            # Encode the prompt
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                pad_to_multiple_of=8,
                return_attention_mask=True
            ).to(self.model.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs["attention_mask"],
                    max_new_tokens=150,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    no_repeat_ngram_size=3,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2
                )
            
            # Decode the response
            response_text = self.tokenizer.decode(
                outputs[0][inputs["input_ids"].shape[1]:],
                skip_special_tokens=True
            )
            
            # Clean up response
            response_text = response_text.strip()
            if response_text:
                # Update conversation history
                self.conversation_history.append(user_input)
                self.conversation_history.append(response_text)
                return response_text
            
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
