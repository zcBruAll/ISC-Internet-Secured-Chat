import random
import re
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QTextEdit, QPushButton, QStyle, QSizePolicy, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

import crypto_interaction
import server_interaction

_window = None
_max = 20

class ToggleButton(QPushButton):
    def __init__(self, text, toggle_mapping, parent=None):
        """
        toggle_mapping: dict mapping current mode to toggled mode, e.g.
            {"encode": "decode", "decode": "encode"}
        """
        super().__init__(text, parent)
        self.toggle_mapping = toggle_mapping

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Split the button text into label and mode (assumes format "Label mode")
            parts = self.text().rsplit(' ', 1)
            if len(parts) == 2:
                label, mode = parts
                # Toggle mode if available in mapping
                toggled_mode = self.toggle_mapping.get(mode, mode)
                self.setText(f"{label} {toggled_mode}")
        else:
            # For left click, call the standard behavior (which emits clicked signal)
            super().mousePressEvent(event)

def getWindow():
    return _window

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ISC - Internet Secured Chat")
        self.setWindowIcon(QIcon("ISC-logo.png"))
        self.setFixedSize(650, 300)

        # Main container with horizontal layout:
        # Left: Messages and input; Right: Command panel, image toggle, and image panel.
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # ---------------------
        # Left Panel: Message Area
        # ---------------------
        message_panel = QWidget()
        message_panel.setFixedWidth(450)
        message_layout = QVBoxLayout(message_panel)

        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        self.message_display.setPlaceholderText("Waiting for messages...")
        message_layout.addWidget(self.message_display)

        # Input area for messages/commands
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter message or command...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        message_layout.addLayout(input_layout)

        # ---------------------
        # Right Container: Command Panel, Image Toggle Button, and Image Panel
        # ---------------------
        right_container = QWidget()
        right_container_layout = QHBoxLayout(right_container)

        # Command Panel
        command_panel = QWidget()
        command_panel.setFixedWidth(160)
        command_layout = QVBoxLayout(command_panel)

        encode_toggle = {"encode": "decode", "decode": "encode"}
        hash_toggle = {"hash": "verify", "verify": "hash"}
        
        btn_shift = ToggleButton("Shift encode", encode_toggle)
        btn_shift.setFixedSize(150, 30)
        btn_shift.clicked.connect(lambda: self.click_task(btn_shift.text().lower()))
        command_layout.addWidget(btn_shift)
        
        btn_vigenere = ToggleButton("Vigenere encode", encode_toggle)
        btn_vigenere.setFixedSize(150, 30)
        btn_vigenere.clicked.connect(lambda: self.click_task(btn_vigenere.text().lower()))
        command_layout.addWidget(btn_vigenere)
        
        btn_rsa = ToggleButton("RSA encode", encode_toggle)
        btn_rsa.setFixedSize(150, 30)
        btn_rsa.clicked.connect(lambda: self.click_task("RSA encode"))
        command_layout.addWidget(btn_rsa)

        btn_hash = ToggleButton("Hash hash", hash_toggle)
        btn_hash.setFixedSize(150, 30)
        btn_hash.clicked.connect(lambda: self.click_task(btn_hash.text().lower()))
        command_layout.addWidget(btn_hash)

        btn_dh = QPushButton("Diffie-Hellman encode")
        btn_dh.setFixedSize(150, 30)
        btn_dh.clicked.connect(lambda: self.click_task("DH encode"))
        command_layout.addWidget(btn_dh)

        right_container_layout.addWidget(command_panel)

        """
        # Image Toggle Button
        self.image_panel_visible = False
        self.image_toggle_button = QPushButton()
        self.image_toggle_button.setFixedSize(30, 100)
        self.image_toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.update_image_toggle_button_icon()
        self.image_toggle_button.clicked.connect(self.toggle_image_panel)
        right_container_layout.addWidget(self.image_toggle_button)

        # Image Panel
        self.image_panel = QWidget()
        image_panel_layout = QVBoxLayout(self.image_panel)
        self.image_panel.setVisible(self.image_panel_visible)

        # Image label on top
        self.image_label = QLabel("Image will be displayed here")
        self.image_label.setFixedSize(300, 225)
        self.image_label.setStyleSheet("border: 1px solid black;")
        self.image_label.setScaledContents(True)
        image_panel_layout.addWidget(self.image_label)

        # Carousel buttons under the image box in a horizontal layout
        carousel_buttons_layout = QHBoxLayout()
        self.prev_image_button = QPushButton("<")
        self.prev_image_button.clicked.connect(self.prev_image)
        carousel_buttons_layout.addWidget(self.prev_image_button)

        self.next_image_button = QPushButton(">")
        self.next_image_button.clicked.connect(self.next_image)
        carousel_buttons_layout.addWidget(self.next_image_button)
        image_panel_layout.addLayout(carousel_buttons_layout)

        right_container_layout.addWidget(self.image_panel)
        """

        main_layout.addWidget(message_panel)
        main_layout.addWidget(right_container)

    def update_image_toggle_button_icon(self):
        if self.image_panel_visible:
            icon = self.style().standardIcon(QStyle.SP_TabCloseButton)
        else:
            icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        self.image_toggle_button.setIcon(icon)

    def toggle_image_panel(self):
        self.image_panel_visible = not self.image_panel_visible
        self.image_panel.setVisible(self.image_panel_visible)
        self.update_image_toggle_button_icon()

    def prev_image(self):
        # TODO: Go to previously sent image
        pass

    def next_image(self):
        # TODO: go to next sent image
        pass

    def click_task(self, command):
        global _max
        addon = "" if command.__contains__("hash") else str(random.randint(1, _max))
        self.message_input.setText("task " + command + " " + addon)

    def send_message(self):
        """
        Sends the user input message to the server when 'Enter' is pressed.
        """
        
        type = server_interaction.mode

        if re.search("task ((shift|vigenere|RSA) (encode|decode) ([1-9][0-9]{0,3}|10000)|hash (hash|verify))", self.message_input.text()) != None:
            type = "s"
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

        if self.message_input.text().startswith("/s "):
            type = "s"
            self.message_input.setText(self.message_input.text()[3:])

        if self.message_input.text().startswith( "/crypto"):
            crypto_interaction.crypto(self.message_input.text().split(" ")[1:])
        else: 
            server_interaction.send_message(type, self.message_input.text())

        self.message_input.setText("")

    def add_message(self, text):
        """
        Appends a new message to the text area and clears the input field.
        :param text: The message to add to the chat history.
        """
        newline = "\n"
        self.message_display.insertPlainText(text + newline)     # Append the new message to the text area
        return

def load_window():
    app = QApplication(sys.argv)
    global _window
    _window = MainWindow()
    _window.show()
    sys.exit(app.exec())