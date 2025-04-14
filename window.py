import random      # For generating random numbers (used in click_task to add a random number)
import re          # For working with regular expressions (used to verify task command formats)
import sys         # Provides access to system-specific parameters and functions (e.g., sys.argv)

# Import PySide6 modules for building the GUI application:
from PySide6.QtWidgets import (
    QApplication,      # To create the application instance
    QMainWindow,       # The base class for main application windows
    QWidget,         # The base class for all UI objects
    QVBoxLayout,     # Layout manager for vertical stacking of widgets
    QHBoxLayout,     # Layout manager for horizontal stacking of widgets
    QLineEdit,       # Single-line text input widget
    QTextEdit,       # Multi-line text display/edit widget
    QPushButton,     # Clickable button widget
    QStyle,          # Provides standard icons and style elements
    QSizePolicy,     # Used to control the resizing behavior of widgets
    QLabel           # Widget to display text or images
)
from PySide6.QtGui import QIcon   # For handling icons in the application
from PySide6.QtCore import Qt      # Contains various identifiers used for widget behavior and event handling

# Import custom modules for cryptographic and server interaction
import crypto_interaction    # Handles encoding/cryptography-related tasks
import server_interaction    # Handles the communication with a server
from communicator import comm  # Provides communication signals (e.g., for chat messages)

# Global variables:
_window = None   # Holds the main window instance (used for global access to the window)
_max = 20        # Maximum value used for generating random numbers for tasks

# -----------------------------------------------------------------------------
# Custom QPushButton subclass that toggles its mode on right-click events
# -----------------------------------------------------------------------------
class ToggleButton(QPushButton):
    def __init__(self, text, toggle_mapping, parent=None):
        """
        Constructor for ToggleButton.
        
        :param text: The initial text displayed on the button.
        :param toggle_mapping: A dictionary mapping current mode to toggled mode,
                               e.g., {"encode": "decode", "decode": "encode"}
        :param parent: Optional parent widget.
        """
        super().__init__(text, parent)
        self.toggle_mapping = toggle_mapping  # Save the mapping for toggling text modes

    def mousePressEvent(self, event):
        # Check if the right mouse button is pressed.
        if event.button() == Qt.RightButton:
            # Split the button text to separate the label from the mode.
            # Expected format: "Label mode"
            parts = self.text().rsplit(' ', 1)
            if len(parts) == 2:
                label, mode = parts  # Unpack the label and current mode
                # Get the toggled mode from the mapping; default to same mode if not found.
                toggled_mode = self.toggle_mapping.get(mode, mode)
                self.setText(f"{label} {toggled_mode}")  # Update button text with toggled mode
        else:
            # For any click other than right-click, perform the default behavior (emitting clicked signal)
            super().mousePressEvent(event)

# -----------------------------------------------------------------------------
# A helper function to retrieve the global main window instance.
# -----------------------------------------------------------------------------
def getWindow():
    return _window

# -----------------------------------------------------------------------------
# Main window class for the chat application.
# -----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set the window title and icon
        self.setWindowTitle("ISC - Internet Secured Chat")
        self.setWindowIcon(QIcon("ISC-logo.png"))
        self.setFixedSize(1280, 720)  # Fix the size of the main window

        # -------------------------------------------------------------------------
        # Set up the main container and layout.
        # The main layout is horizontal: left for messages, right for command panel & images.
        # -------------------------------------------------------------------------
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # ---------------------
        # Left Panel: Message Area
        # ---------------------
        message_panel = QWidget()
        message_panel.setFixedWidth(1100)     # Fix the width for messages
        message_layout = QVBoxLayout(message_panel)

        # Create a QTextEdit widget to display messages (read-only with rich text support)
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        # Uncomment below to set a placeholder message:
        # self.message_display.setPlaceholderText("Waiting for messages...")
        self.message_display.setAcceptRichText(True)
        message_layout.addWidget(self.message_display)

        # Input area for sending messages/commands:
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message or command...")
        # Connect pressing return to sending a message
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)

        # Button to send messages when clicked
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        message_layout.addLayout(input_layout)

        # ---------------------
        # Right Container: Command Panel, Image Toggle, etc.
        # ---------------------
        right_container = QWidget()
        right_container_layout = QHBoxLayout(right_container)

        # Command Panel: Contains buttons for different tasks
        command_panel = QWidget()
        command_panel.setFixedWidth(160)
        command_layout = QVBoxLayout(command_panel)

        # Dictionaries for toggling: these map modes to their opposite (e.g., "encode" ↔ "decode")
        encode_toggle = {"encode": "decode", "decode": "encode"}
        hash_toggle = {"hash": "verify", "verify": "hash"}
        
        # Create a Shift button with toggling capability
        btn_shift = ToggleButton("Shift encode", encode_toggle)
        btn_shift.setFixedSize(150, 30)
        # On click, convert button text to lowercase and pass it to click_task
        btn_shift.clicked.connect(lambda: self.click_task(btn_shift.text().lower()))
        command_layout.addWidget(btn_shift)
        
        # Create a Vigenere button with toggling capability
        btn_vigenere = ToggleButton("Vigenere encode", encode_toggle)
        btn_vigenere.setFixedSize(150, 30)
        btn_vigenere.clicked.connect(lambda: self.click_task(btn_vigenere.text().lower()))
        command_layout.addWidget(btn_vigenere)
        
        # Create an RSA button (no toggle on right-click for RSA)
        btn_rsa = ToggleButton("RSA encode", encode_toggle)
        btn_rsa.setFixedSize(150, 30)
        btn_rsa.clicked.connect(lambda: self.click_task("RSA encode"))
        command_layout.addWidget(btn_rsa)

        # Create a Hash button with toggling between hash and verify
        btn_hash = ToggleButton("Hash hash", hash_toggle)
        btn_hash.setFixedSize(150, 30)
        btn_hash.clicked.connect(lambda: self.click_task(btn_hash.text().lower()))
        command_layout.addWidget(btn_hash)

        # Create a Diffie-Hellman button (named "Diffie-Hellman encode")
        btn_dh = QPushButton("Diffie-Hellman encode")
        btn_dh.setFixedSize(150, 30)
        # Use a short key "DifHel" to identify Diffie-Hellman tasks
        btn_dh.clicked.connect(lambda: self.click_task("DifHel"))
        command_layout.addWidget(btn_dh)

        # Add the command panel to the right container layout
        right_container_layout.addWidget(command_panel)

        # Connect communication signals (for handling incoming chat messages or images)
        comm.chat_msg.connect(self.add_message)
        comm.chat_img.connect(self.add_image)

        # Add the two main containers to the overall horizontal layout
        main_layout.addWidget(message_panel)
        main_layout.addWidget(right_container)

    # --------------------------------------------------------
    # Update the image toggle button icon based on visibility
    # --------------------------------------------------------
    def update_image_toggle_button_icon(self):
        if self.image_panel_visible:
            # Use a standard icon for 'close' action if the image panel is visible
            icon = self.style().standardIcon(QStyle.SP_TabCloseButton)
        else:
            # Use a play icon if the image panel is hidden
            icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.image_toggle_button.setIcon(icon)

    # --------------------------------------------------------
    # Toggle the visibility of the image panel in the GUI.
    # --------------------------------------------------------
    def toggle_image_panel(self):
        self.image_panel_visible = not self.image_panel_visible  # Flip the visibility state
        self.image_panel.setVisible(self.image_panel_visible)      # Update the actual widget visibility
        self.update_image_toggle_button_icon()                    # Refresh the button icon accordingly

    # Placeholder for moving to the previous image (not yet implemented)
    def prev_image(self):
        # TODO: Go to previously sent image
        pass

    # Placeholder for moving to the next image (not yet implemented)
    def next_image(self):
        # TODO: Go to next sent image
        pass

    # ------------------------------------------------------------------------------
    # Prepares a command based on the button click.
    # Determines if a random number should be appended to the task command.
    # ------------------------------------------------------------------------------
    def click_task(self, command):
        global _max
        # Check if the command text contains "hash" or "DifHel". If not, append a random number.
        addon = "" if command.__contains__("hash") or command.__contains__("DifHel") else str(random.randint(1, _max))
        # Set the message input with a formatted task command string.
        self.message_input.setText("task " + command + " " + addon)

    # ------------------------------------------------------------------------------
    # Handles sending the message from the input area.
    # This method processes the message, sets various crypto flags, and communicates with the server.
    # ------------------------------------------------------------------------------
    def send_message(self):
        """
        Sends the user input message to the server when 'Enter' is pressed.
        """
        
        # Get the default mode from the server interaction module.
        type = server_interaction.mode

        # Use regex to detect specific task commands (shift, vigenere, RSA tasks; hash tasks; Diffie-Hellman)
        if re.search("task ((shift|vigenere|RSA) (encode|decode) ([1-9][0-9]{0,3}|10000)|hash (hash|verify)|DifHel)", self.message_input.text()) != None:
            type = "s"  # Override to 's' mode for tasks
            # Set various flags in crypto_interaction based on the task keywords in the message
            if self.message_input.text().__contains__("shift"):
                crypto_interaction.isShifting = True
                crypto_interaction.server_msg.clear()
            elif self.message_input.text().__contains__("vigenere"):
                crypto_interaction.isVigenering = True
                crypto_interaction.server_msg.clear()
            elif self.message_input.text().__contains__("RSA"):
                crypto_interaction.isRSAing = True
                crypto_interaction.server_msg.clear()
            
            if self.message_input.text().__contains__("encode"):
                crypto_interaction.isEncoding = True
                crypto_interaction.server_msg.clear()

            if self.message_input.text().__contains__("hash"):
                crypto_interaction.isHashing = True
                crypto_interaction.server_msg.clear()

            if self.message_input.text().__contains__("verify"):
                crypto_interaction.isVerifying = True
                crypto_interaction.server_msg.clear()

            if self.message_input.text().__contains__("DifHel"):
                crypto_interaction.difHelStep = 1
                crypto_interaction.isDifHeling = True
                crypto_interaction.server_msg.clear()

        # If message starts with '/s ', remove the prefix and set type to 's'
        if self.message_input.text().startswith("/s "):
            type = "s"
            self.message_input.setText(self.message_input.text()[3:])

        # If message starts with '/crypto', pass the arguments to the crypto_interaction module
        if self.message_input.text().startswith("/crypto"):
            crypto_interaction.crypto(self.message_input.text().split(" ")[1:])
        else: 
            # Otherwise, send the message using server_interaction module.
            server_interaction.send_message(type, self.message_input.text())

        # Clear the message input field after sending the message.
        self.message_input.setText("")

    # ------------------------------------------------------------------------------
    # Appends a new message to the chat display area.
    # Also adds a title to identify the sender.
    # ------------------------------------------------------------------------------
    def add_message(self, who, text):
        """
        Appends a new message to the text area and clears the input field.
        
        :param who: The sender of the message.
        :param text: The content of the message.
        """
        self.add_title(who)  # Add the sender's title
        # Append the new message with HTML formatting (using paragraph tags)
        self.message_display.append("<p style=\"margin:0px;\">" + text + "</p>")
        return
    
    # ------------------------------------------------------------------------------
    # Adds a title (i.e., the sender's identity) above the message.
    # ------------------------------------------------------------------------------
    def add_title(self, who):
        self.message_display.append("<p style=\"margin:0px;font-weight:bold;font-style: italic;\">" + who + "</p>")
        return
    
    # ------------------------------------------------------------------------------
    # Handles adding an image to the chat display.
    # It calls add_title to note that an image is being added.
    # ------------------------------------------------------------------------------
    def add_image(self, incr):
        self.add_title("[Image]")
        # Append an HTML image element with the specified source and styling
        self.message_display.append("<img src=\"imgs/img" + str(incr) + ".png\" alt=\"Image\" style=\"margin:0px;margin-bottom:10px;\"></img>")
        return

# ------------------------------------------------------------------------------
# Initializes the application window and starts the event loop.
# ------------------------------------------------------------------------------
def load_window():
    app = QApplication(sys.argv)  # Create the application object with command-line arguments
    global _window
    _window = MainWindow()        # Instantiate the main window
    _window.show()                # Display the main window
    sys.exit(app.exec())          # Start the application event loop and exit when done
