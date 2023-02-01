from data import Data
import pyinputplus as pyip
from time import sleep

"""
    SUMMARY:
    
    Few things which I did to make my code better:
        1. Divide the code in two classes to increase readability for debugging and for understanding the code.
        2. Classes:
            a. Frontend -> Class MessageBoard:
                User can easily interact and understand the code without thinking about how things in background are working.
                
            b. Business Logic -> Class Data:
                This class is responsible for making background threads, so the user can act as server and client at same time and
                also close them when user is exiting. This class read/write all the data from/to a file and also handle the data for
                runtime.
                
"""


class MessageBoard:
    def __init__(self, file_name, author_name):
        # making instance of Data class which will make background threads for peers to interact
        # and also serve current user.
        self.data = Data(file_name, author_name)

    # Function for user to interact from terminal
    def menu(self):
        while True:
            print("\n====== Message Board's Menu ======")
            print("1. Get messages from Peer")
            print("2. Add a message")
            print("3. Print all messages")
            print("4. Exit")
            print("==================================")

            option = pyip.inputNum("\nEnter option number: ")

            if option == 1:
                port_number = pyip.inputNum("\nEnter port of peer: ")
                self.data.get_data_peer(port_number)

            elif option == 2:
                self.add_message()

            elif option == 3:
                self.data.print_messages()

            elif option == 4:
                self.data.stop_all_threads()
                break

    # Function to add message
    def add_message(self):
        message = pyip.inputStr("\nEnter message: ")
        self.data.add_message(message)


if __name__ == "__main__":
    author_name = pyip.inputStr("Enter author name: ")
    file_name = pyip.inputStr("Enter file name: ")

    message_board = MessageBoard(file_name, author_name)
    sleep(0.5)
    message_board.menu()
