from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

# Create a new ChatBot instance
bot = ChatBot("chatbot", read_only=False, 
    logic_adapters=[

        {
            "import_path":"chatterbot.logic.BestMatch",
            "default_response":"Sorry I don't have a answer",
            "maximum_similarity_threshold":0.9
        }

        ])
         

# Define a list of conversation pairs
list_to_train = [
    "hi",
    "hi there",
    "What's your name?",
    "I'm a chatbot",
    "How old are you?",
    "I'm ageless!",
    "why are you so mad?",
    "I'm not",
    "do you have iPhone",
    "I've everything!",
    "What's your favorite food?",
    "I don't eat",
    "what's your job?",
    "I'm here to answer your questions",
    "I don't know what are you talking about"
]

# Create a ListTrainer instance
list_trainer = ListTrainer(bot)

# Train the chatbot with the conversation list
list_trainer.train(list_to_train)

# Optional: Test the chatbot response
while True:
    user_response = input("User: ")
    print("Chatbot: " + str(bot.get_response(user_response)))

