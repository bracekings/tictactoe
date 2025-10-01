from deepseek_chatbot import AIchatbot

# Initialize bot (uses HF_TOKEN from environment or built-in fallback in code)
bot = AIchatbot()

# Simulate Alice speaking
print('\n--- Alice -> "hello"')
resp1 = bot.get_response('hello', sender='Alice')
print('Moxie:', resp1)

# Simulate Bob speaking next
print('\n--- Bob -> "hi there"')
resp2 = bot.get_response('hi there', sender='Bob')
print('Moxie:', resp2)

# Simulate Alice again
print('\n--- Alice -> "welcome back"')
resp3 = bot.get_response('welcome back', sender='Alice')
print('Moxie:', resp3)
