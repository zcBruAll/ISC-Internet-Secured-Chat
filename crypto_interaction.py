import window_interaction
import server_interaction

isShifting = False
isEncoding = False
server_msg = list[str]()

def appendServerMsg(msg: str):
    """
    Append the server message to the list nad execute the linked tasks

    :params msg: The decoded message of the server
    """
    global isShifting
    global isEncoding

    server_msg.append(msg)

    # Check if the previous task was shifting and if the server sent all the necessary messages
    if isShifting == True and len(server_msg) == 2:
        # Check if the previous task was to encode or decode a message
        if (isEncoding):
            server_interaction.send_message("s", encode_shift(server_msg[1], int(server_msg[0].split(" ")[-1])))
        isShifting = False      # Reset the task, it should be done
        isEncoding = False      # Reset the task, it should be done
        server_msg.clear()      # Reset the server messages

# Encode the message with shift
def encode_shift(message, shift):
    """
    Encode the message by substracting the given shift key

    :params message: The message to encode 
    :params shift: The `int` shift key to use
    """
    result = ""
    for c in message:
        # For every character in the message, 
        # sum the shift key with the unicode code 
        # and join it to the result as a string
        result += chr(ord(c) + shift)
    
    return result

# Decode the message with shift
def decode_shift(message, shift):
    """
    Decode the message by substracting the given shift key

    :params message: The message to decode 
    :params shift: The `int` shift key to use
    """
    result = ""
    for c in message:
        # For every character in the message, 
        # subsctract the unicode code with the shift key 
        # and join it to the result as a string
        result += chr(ord(c) - shift)

    return result

# Execute the crypto commands
def crypto(command: list[str]):
    """
    Process the crypto commands

    :params command: text commands splitted by spaces without the first cell
    """

    result = ""
    # Reitreve if the operation is to encode or decode
    isEncode = command[1] == "encode"
    match command[0]:
        case "shift":
            if isEncode:
                # Concatenate the command message contained in the third to the last-1 cell
                # Retrieve the shift key in the last cell of the command
                result = encode_shift(" ".join(command[2:-1]), int(command[-1]))
            else :
                # Concatenate the command message contained in the third to the last-1 cell
                # Retrieve the shift key in the last cell of the command
                result = decode_shift(" ".join(command[2:-1]), int(command[-1]))

    window_interaction.add_message("<Crypto> " + " ".join(command))
    window_interaction.add_message("<Crypto> " + result)