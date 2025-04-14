# Import necessary modules
import socket                       # For network communication
import threading                    # For handling concurrent tasks
import window                       # Custom module to interact with the UI
import crypto_interaction           # Custom module to interact with the crypto tools

import threading

from PIL import Image
import numpy as np

# Server details
HOST = 'vlbelintrocrypto.hevs.ch'   # Server hostname
PORT = 6000                         # Server port

mode = "t"

width = 0
length = 0

incr = 0

# Connection state:
# -1: Not connected yet
#  0: Connection failed
#  1: Connected
connection_state = -1  
last_own_sent_message = ""  # Stores the last message sent by the user

# ==========================================================
#               MESSAGE ENCODING & DECODING
# ==========================================================

def _str_encode(type, msg):
    """
    Encodes a message to send to the server in ISC format.

    :param type: A string representing the type of message (e.g., 't' for text).
    :param string: The message content to encode.
    :return: The encoded byte sequence.
    """

    lengthMsg = 0
    if isinstance(msg, str):
        lengthMsg = len(msg)
    else:
        lengthMsg = len(msg) / 4

    # ISC Header + message type + message length encoded in big-endian format
    message = b'ISC' + type.encode('utf-8') + int(lengthMsg).to_bytes(2, byteorder='big')

    if isinstance(msg, str):
        # Encode characters as Unicode (up to 4 bytes per character)
        for s in msg:
            encoded = s.encode('utf-8')
            message += (4 - len(encoded)) * b'\x00' + encoded   # Pad with null bytes if needed
    else:
        message += msg

    return message

def _decode_message(text):
    """
    Decodes an incoming message from the server, removing unnecessary padding.

    :param text: The raw message received from the server (bytes).
    :return: The decoded string without padding.
    """
    return text.decode("utf-8", errors="ignore").replace("\x00", "")            # Skip the first 6 bytes (ISC header + type + length)

# ==========================================================
#               SERVER CONNECTION MANAGEMENT
# ==========================================================

def open_connection():
    """
    Establishes a connection to the server.
    Starts a separate thread to handle incoming messages.
    """
    global connection_state
    global connection
    try:
        # Initialize the socket for TCP communication
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Attempt to connect to the server
        connection.connect((HOST, PORT))
    except (ConnectionRefusedError, socket.gaierror) as e:
        # If the connection fails, print an error message and exit
        print("[ServerInteraction] The connection couldn't be established.")
        print(e)
        connection_state = 0
        exit(1)

    print("Connection open")    # Success message
    connection_state = 1        # Update connection state to 'connected'

    try:
        # Start a new thread to handle incoming messages from the server
        t = threading.Thread(target=handle_message_reception)
        t.start()
    except KeyboardInterrupt:
        # Handle manual interruption (Ctrl+C)
        print("Stopped by Ctrl+C")
        close_connection()

def close_connection():
    """
    Closes the connection to the server.
    """
    connection.close()
    print("Connection closed")

# ==========================================================
#               MESSAGE HANDLING
# ==========================================================

def handle_message_reception():
    """
    Continuously listens for incoming messages from the server.
    Decodes them and updates the chat window.
    """
    while True:
        try:
            # Receive 'ISC' and don't care of it
            connection.recv(3)

            # Receive the type of the message
            type = connection.recv(1).decode("utf-8", errors="ignore")

            data = bytearray()

            global width
            global length
            global incr

            # Receive the length of the message
            if type == "i":
                width = int.from_bytes(connection.recv(1))
                height = int.from_bytes(connection.recv(1))
                img = bytearray()
                datalength = width * height * 3
                while (len(img) < datalength): 
                    img.extend(connection.recv(3))

                array = np.array(img, dtype=np.uint8)

                while (len(array) % 3 != 0):
                    array = array[:-1]
                
                array = array.reshape((height, width, 3))

                img = Image.fromarray(array, 'RGB')

                img.save("imgs/img" + str(incr) + ".png")
                window.getWindow().add_image(incr)
                incr += 1
            else:
                msgLength = int.from_bytes(connection.recv(2), byteorder='big') * 4

                # Receive the message
                data = connection.recv(msgLength)
        except ConnectionError:
            close_connection()
            s = threading.Thread(target=open_connection, daemon=True)
            s.start()

        if (type != "i"):
            decoded_data = ""
            decoded_data = _decode_message(data)            # Decode received data

            global last_own_sent_message
            # If the message is not empty and is not the last message we sent
            if len(decoded_data) != 0  and decoded_data != last_own_sent_message:
                if type == "t":
                    last_own_sent_message = ""                  # Reset last sent message tracking
                
                window.getWindow().add_message(
                    ("[User] " if type == "t" 
                    else 
                    "[Server] " if type == "s" 
                    else
                    "[Other] ")
                    , _decode_message(data))   # Display message in the UI
            
            if type == "s":
                crypto_interaction.appendServerMsg(decoded_data)

def send_message(type, text):
    """
    Sends a message to the server and updates the chat window.

    :param text: The message to be sent.
    """
    global last_own_sent_message
    if len(text) != 0 and ["t", "s", "b"].count(type) == 1 :
        connection.send(_str_encode(type, text))                # Send encoded message to server

        text_to_add = ""
        if isinstance(text, bytearray):
            text_to_add += bytes(b for b in text if b != 0).decode('utf-8', 'replace')
        else:
            text_to_add = text

        window.getWindow().add_message("[You] ", text_to_add)  # Display message in UI
        last_own_sent_message = text                            # Store last sent message to avoid duplication
