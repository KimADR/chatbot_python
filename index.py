from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer

# Create a new ChatBot instance
bot = ChatBot("chatbot", read_only=False, 
    logic_adapters=[

        {
            "import_path":"chatterbot.logic.BestMatch",
            "default_response":"Sorry I don't have a answer",
            "maximum_similarity_threshold":0.9
        }

        ])
         
trainer = ChatterBotCorpusTrainer(bot)

trainer.train("chatterbot.corpus.english")

# Optional: Test the chatbot response
while True:
    user_response = input("User: ")
    print("Chatbot: " + str(bot.get_response(user_response)))

