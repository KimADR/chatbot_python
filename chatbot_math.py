from chatterbot import ChatBot
from chatterbot.conversation import Statement

# Create a chatbot instance with the MathematicalEvaluation logic adapter
bot = ChatBot("Math", logic_adapters=["chatterbot.logic.MathematicalEvaluation"])

print("------------------Math Chatbot-------------------")

while True:
    # Get user input
    user_text = input("Type the math equation that you want to solve: ")

    # Exit if the user types 'exit' or 'quit'
    if user_text.lower() in ["exit", "quit"]:
        print("Exiting Math Chatbot. Goodbye!")
        break

    # Get and print the chatbot's response
    try:
        # Create a Statement object from user input
        input_statement = Statement(text=user_text)
        
        # Get response using the Statement object
        response = bot.get_response(input_statement)
        
        print("Chatbot: " + str(response))

    except SyntaxError:
        print("Error: Invalid mathematical expression. Please use correct syntax.")
    except TypeError:
        print("Error: Invalid input type. Please enter a valid equation.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
