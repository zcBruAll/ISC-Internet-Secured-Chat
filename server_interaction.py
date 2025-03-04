# Import necessary modules
import socket                       # For network communication
import threading                    # For handling concurrent tasks
import window_interaction           # Custom module to interact with the UI
import crypto_interaction           # Custom module to interact with the crypto tools

# Server details
HOST = 'vlbelintrocrypto.hevs.ch'   # Server hostname
PORT = 6000                         # Server port

mode = "t"

# Initialize the socket for TCP communication
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connection state:
# -1: Not connected yet
#  0: Connection failed
#  1: Connected
connection_state = -1  
last_own_sent_message = ""  # Stores the last message sent by the user

# ==========================================================
#               MESSAGE ENCODING & DECODING
# ==========================================================

def _str_encode(type, string):
    """
    Encodes a message to send to the server in ISC format.

    :param type: A string representing the type of message (e.g., 't' for text).
    :param string: The message content to encode.
    :return: The encoded byte sequence.
    """
    # ISC Header + message type + message length encoded in big-endian format
    msg = b'ISC' + type.encode('utf-8') + len(string).to_bytes(2, byteorder='big')

    # Encode characters as Unicode (up to 4 bytes per character)
    for s in string:
        encoded = s.encode('utf-8')
        msg += (4 - len(encoded)) * b'\x00' + encoded   # Pad with null bytes if needed

    return msg

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

            # Receive the length of the message
            msgLength = int.from_bytes(connection.recv(2), byteorder='big') * 4

            # Receive the message
            data = connection.recv(msgLength)
        except ConnectionAbortedError:
            print("[ServerInteraction] Connection aborted")
            exit(1)                                         # If the connection is aborted, exit the thread

        
        decoded_data = _decode_message(data)                # Decode received data

        global last_own_sent_message
        # If the message is not empty and is not the last message we sent
        if len(decoded_data) != 0  and decoded_data != last_own_sent_message:
            if type == "t":
                last_own_sent_message = ""                  # Reset last sent message tracking
            
            window_interaction.add_message(
                ("<User> " if type == "t" 
                 else 
                 "<Server> " if type == "s" 
                 else 
                 "<Other> ") 
                 + _decode_message(data))   # Display message in the UI
        
        if type == "s":
            crypto_interaction.appendServerMsg(decoded_data)

def send_message(type, text):
    """
    Sends a message to the server and updates the chat window.

    :param text: The message to be sent.
    """
    global last_own_sent_message
    if len(text) != 0 and ["t", "s", "b"].count(type) == 1 :
        connection.send(_str_encode(type, text))            # Send encoded message to server
        window_interaction.add_message("<You> " + text)     # Display message in UI
        last_own_sent_message = text                        # Store last sent message to avoid duplication

# ==========================================================
#               SERVER COMMAND HANDLING
# ==========================================================

def server_command_task(text_array):
    """
    Processes "task" commands.

    :param text_array: A list of command arguments (e.g., ['shift', 'encode', '2000']).
    """
    split_text = text_array
    if split_text[0] == "task":
        del split_text[0]   # Remove "task" if it's still present

    # Determine if the command is an encode or decode task
    type_code = split_text[1]

    match type_code:        # Handle different cryptographic tasks
        case "shift":
            pass            # Placeholder for shift cipher implementation
        case "vigenere":
            pass            # Placeholder for Vigenère cipher implementation
        case "RSA":
            pass            # Placeholder for RSA encryption implementation
        case _:
            pass            # Catch-all case for unknown commands

def server_command_hash(text_array):
    """
    Processes "hash" commands.

    :param text_array: A list of command arguments (e.g., ['verify', 'hash']).
    """
    match text_array[0]:    # Check the first argument of the command
        case "verify":
            pass            # Placeholder for hash verification implementation
        case "hash":
            pass            # Placeholder for hash generation implementation
