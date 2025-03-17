# Import necessary modules from PyQt6
from PyQt6.QtCore import *      # Core functionality for PyQt6
from PyQt6.QtWidgets import *   # Widgets for GUI elements
from PyQt6.QtGui import *       # GUI elements
import server_interaction       # Import custom module for server communication
import crypto_interaction       # Import custom module for cryptography tools
import re                       # Import the regex module

# Global variables for UI elements
text_area = ""  # Placeholder for text area widget
message = ""    # Placeholder for message input field

def load_window():
    """
    Initializes and displays the chat window.
    Handles user message input and manages server connection.
    """
    
    app = QApplication([])  # Initialize the PyQt6 application
    app.setApplicationDisplayName("ISC - Internet Secured Chat")
    app.setWindowIcon(QIcon("ISC-logo.png"))

    # Define the global text area widget (read-only message history)
    global text_area
    text_area = QPlainTextEdit()                        # Multi-line text area
    text_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)    # Disable direct editing

    # Define the global message input field (for user input)
    global message
    message = QLineEdit()           # Single-line text input

    # Create a vertical layout and add the UI elements
    layout = QVBoxLayout()
    layout.addWidget(text_area)     # Add text area to layout
    layout.addWidget(message)       # Add message input field to layout

    # Create the main window and set the layout
    window = QWidget()
    window.setLayout(layout)
    window.setMinimumSize(500, 350)
    window.show()                   # Display the window
    

    def send_message():
        """
        Sends the user input message to the server when 'Enter' is pressed.
        """
        type = server_interaction.mode

        if re.search("task (shift|vigenere|RSA) (encode|decode) ([1-9][0-9]{0,3}|10000)", message.text()) != None:
            type = "s"
            if message.text().__contains__("shift"):
                crypto_interaction.isShifting = True
                crypto_interaction.server_msg.clear()
            elif message.text().__contains__("vigenere"):
                crypto_interaction.isVigenering = True
                crypto_interaction.server_msg.clear()
            elif message.text().__contains__("RSA"):
                crypto_interaction.isRSAing = True
                crypto_interaction.server_msg.clear()
            
            if message.text().__contains__("encode"):
                crypto_interaction.isEncoding = True
                crypto_interaction.server_msg.clear()

        if message.text().startswith("/s "):
            type = "s"
            message.setText(message.text()[3:])

        if message.text().startswith( "/crypto"):
            crypto_interaction.crypto(message.text().split(" ")[1:])
        else: 
            server_interaction.send_message(type, message.text())  # Send message to the server

        message.setText("")

    # Connect the return key event to the send_message function
    message.returnPressed.connect(send_message)

    # Wait for the server connection to be established (-1 means still trying)
    while server_interaction.connection_state == -1:
        pass        # Do nothing, just wait for the state to change

    # If the connection could not be established (0 indicates failure)
    if server_interaction.connection_state == 0:
        print("[Window] Connection failed, window will not open.")
        exit(1)     # Exit the program

    # If the connection is successful, execute the application loop
    out_code = app.exec()

    # Close the server connection when the window is closed
    server_interaction.close_connection()

    exit(out_code)      # Exit the program with the application's exit code

def add_message(text):
    """
    Appends a new message to the text area and clears the input field.
    :param text: The message to add to the chat history.
    """
    
    global text_area
    text_area.appendPlainText(text)     # Append the new message to the text area
    return