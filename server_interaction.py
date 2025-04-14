# ==========================================================
#               IMPORTS AND GLOBAL DEFINITIONS
# ==========================================================

import socket                       # Provides functions for creating and using network sockets.
import threading                    # Enables running tasks concurrently in separate threads.
import window                       # Custom module to interact with the UI (details assumed to be in the module).
import crypto_interaction           # Custom module for cryptographic operations (e.g., encryption/decryption).

# Note: The threading module is imported twice; one of these can be removed.
import threading

from communicator import comm       # Imports the 'comm' object used for emitting chat-related signals.

from PIL import Image               # PIL (Pillow) is used here to handle image creation and saving.
import numpy as np                  # Numpy is used for efficient array operations, especially with image data.

# Server connection details:
HOST = 'vlbelintrocrypto.hevs.ch'   # The hostname of the server to connect to.
PORT = 6000                         # The port on which the server is listening.

# Default mode for messages (e.g., 't' for text).
mode = "t"

# Variables to hold image dimensions:
width = 0                           # Will later store the width of a received image.
length = 0                          # Intended for image length (or height); note that this variable is not used directly.

incr = 0                            # Image increment counter for naming saved images uniquely.

# Connection state indicators:
# -1: Not connected yet
#  0: Connection attempt failed
#  1: Successfully connected
connection_state = -1  

# Stores the last message sent by the user. This is used to filter out echo messages received from the server.
last_own_sent_message = ""

# ==========================================================
#         MESSAGE ENCODING & DECODING FUNCTIONS
# ==========================================================

def _str_encode(type, msg):
    """
    Encodes a message into the ISC format for transmission to the server.

    The format includes:
      - A header 'ISC'
      - The message type (e.g., 't' for text)
      - The message length encoded in big-endian order (after conversion to an integer)
      - The message content:
            * If the message is a string, each character is encoded in UTF-8 and padded to 4 bytes.
            * If already a byte-like object, it is appended directly.

    :param type: A string representing the type of message (e.g., 't' for text).
    :param msg: The message content to encode; either a string or bytearray.
    :return: A bytes object representing the encoded message ready for sending.
    """
    lengthMsg = 0
    if isinstance(msg, str):
        # Compute the length of the message string.
        lengthMsg = len(msg)
    else:
        # If not a string, assume each character was padded to 4 bytes.
        lengthMsg = len(msg) / 4

    # Build the ISC header:
    # b'ISC' is a fixed header.
    # Next is the message type encoded in UTF-8.
    # Followed by the message length encoded as two bytes (big-endian).
    message = b'ISC' + type.encode('utf-8') + int(lengthMsg).to_bytes(2, byteorder='big')

    if isinstance(msg, str):
        # For each character in the string, encode to UTF-8.
        # Each character is padded with null bytes so that each takes up 4 bytes.
        for s in msg:
            encoded = s.encode('utf-8')
            message += (4 - len(encoded)) * b'\x00' + encoded
    else:
        # If the message is already in bytes (or a bytearray), append it directly.
        message += msg

    return message

def _decode_message(text):
    """
    Decodes an incoming byte sequence by converting it into a string and removing padding.

    :param text: The raw message bytes received from the server.
    :return: The decoded string with null bytes removed.
    """
    # Decode using UTF-8 (ignoring errors), then remove any null (padding) characters.
    return text.decode("utf-8", errors="ignore").replace("\x00", "")

# ==========================================================
#         SERVER CONNECTION MANAGEMENT FUNCTIONS
# ==========================================================

def open_connection():
    """
    Establishes a connection to the server and launches a thread to handle incoming messages.
    """
    global connection_state
    global connection
    try:
        # Create a TCP/IP socket.
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Attempt to connect to the server using the predefined HOST and PORT.
        connection.connect((HOST, PORT))
    except (ConnectionRefusedError, socket.gaierror) as e:
        # In case of connection failure, output an error message.
        print("[ServerInteraction] The connection couldn't be established.")
        print(e)
        connection_state = 0  # Update connection state to indicate failure.
        exit(1)             # Exit the program.

    print("Connection open")    # Confirm a successful connection.
    connection_state = 1        # Set the connection state to 'connected'.

    try:
        # Create and start a new thread to continuously receive messages from the server.
        t = threading.Thread(target=handle_message_reception)
        t.start()
    except KeyboardInterrupt:
        # If the user interrupts (e.g., Ctrl+C), close the connection.
        print("Stopped by Ctrl+C")
        close_connection()

def close_connection():
    """
    Closes the active connection to the server and prints a confirmation message.
    """
    connection.close()
    print("Connection closed")

# ==========================================================
#             MESSAGE HANDLING FUNCTIONS
# ==========================================================

def handle_message_reception():
    """
    Listens continuously for incoming messages from the server.

    - For image messages ('i'), it receives image dimensions, collects image data,
      reconstructs and saves the image, and emits a signal to update the UI.
    - For other message types, it receives and decodes the message, then updates the UI
      if the message is new.
    """
    while True:
        try:
            # Discard the first 3 bytes (fixed ISC header 'ISC').
            connection.recv(3)

            # Receive the next byte which indicates the message type.
            type = connection.recv(1).decode("utf-8", errors="ignore")

            data = bytearray()

            global width
            global length
            global incr

            if type == "i":
                # For image messages:
                # Receive width and height (each in one byte).
                width = int.from_bytes(connection.recv(1))
                height = int.from_bytes(connection.recv(1))
                img = bytearray()
                # Calculate the total data length for an RGB image.
                datalength = width * height * 3
                # Continue receiving data until the full image is received.
                while (len(img) < datalength): 
                    img.extend(connection.recv(3))

                # Convert the collected bytes into a NumPy array.
                array = np.array(img, dtype=np.uint8)

                # Ensure the array length is a multiple of 3 (for RGB channels) by trimming if necessary.
                while (len(array) % 3 != 0):
                    array = array[:-1]
                
                # Reshape the array into a 3-dimensional array (height x width x 3).
                array = array.reshape((height, width, 3))

                # Create an image from the array using PIL.
                img = Image.fromarray(array, 'RGB')

                # Save the image to the 'imgs' directory with a filename based on the increment counter.
                img.save("imgs/img" + str(incr) + ".png")
                # Emit a signal through 'comm.chat_img' to update the UI with the new image.
                comm.chat_img.emit(incr)
                incr += 1  # Increment the image counter.
            else:
                # For non-image messages, first obtain the message length.
                # The length is sent as 2 bytes (big-endian) and each character is padded to 4 bytes.
                msgLength = int.from_bytes(connection.recv(2), byteorder='big') * 4
                # Receive the message data of the calculated length.
                data = connection.recv(msgLength)
        except ConnectionError:
            # On connection error, close the connection and attempt to reopen it in a new thread.
            close_connection()
            s = threading.Thread(target=open_connection, daemon=True)
            s.start()

        if (type != "i"):
            decoded_data = _decode_message(data)  # Decode the received message data.

            global last_own_sent_message
            # If the decoded message is non-empty and not identical to the last sent message,
            # process it to update the UI.
            if len(decoded_data) != 0 and decoded_data != last_own_sent_message:
                if type == "t":
                    # Reset last sent message tracking for text messages.
                    last_own_sent_message = ""
                # Emit a signal to update the chat UI with the message.
                # The sender label is chosen based on the type of message.
                comm.chat_msg.emit(
                    ("[User] " if type == "t" 
                     else "[Server] " if type == "s" 
                     else "[Other] "),
                    _decode_message(data))
            
            if type == "s":
                # For server messages, update the crypto interaction module with the server message.
                crypto_interaction.appendServerMsg(decoded_data)

def send_message(type, text):
    """
    Sends a message to the server and updates the chat UI accordingly.

    - It first verifies that the message is non-empty and that the type is one of the allowed types.
    - The message is encoded using the custom ISC format before sending.
    - It emits a signal so that the UI displays the message as having been sent by the user.

    :param type: A single-character string indicating the message type ('t', 's', or 'b').
    :param text: The actual message content to send.
    """
    global last_own_sent_message
    # Only send if there is text and the message type is one of the expected ones.
    if len(text) != 0 and ["t", "s", "b"].count(type) == 1:
        # Encode the message into ISC format and send it over the connection.
        connection.send(_str_encode(type, text))

        text_to_add = ""
        # If the message is a bytearray, filter out any null bytes before decoding.
        if isinstance(text, bytearray):
            text_to_add += bytes(b for b in text if b != 0).decode('utf-8', 'replace')
        else:
            text_to_add = text

        # Emit a signal to update the chat UI with the sent message.
        comm.chat_msg.emit("[You] ", text_to_add)
        # Store the sent message to avoid echoing it back upon reception.
        last_own_sent_message = text
