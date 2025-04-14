from hashlib import sha256
import random
from cryptography.hazmat.primitives.asymmetric import dh
from sympy import primerange, primitive_root

import window
import server_interaction

isShifting = False
isVigenering = False
isRSAing = False
isHashing = False
isDifHeling = False

isEncoding = False
isVerifying = False

difHelStep = 0

dh_space = [0, 0, 0]

server_msg = list[str]()

def appendServerMsg(msg: str):
    """
    Append the server message to the list nad execute the linked tasks

    :params msg: The decoded message of the server
    """
    global isShifting
    global isVigenering
    global isRSAing
    global isHashing
    global isDifHeling

    global isEncoding
    global isVerifying
    global difHelStep

    server_msg.append(msg)

    # Check if the previous task was shifting and if the server sent all the necessary messages
    if isShifting == True and len(server_msg) == 2:
        # Check if the previous task was to encode or decode a message
        if (isEncoding):
            server_interaction.send_message("s", encode_shift(server_msg[1], int(server_msg[0].split(" ")[-1])))
        isShifting = False      # Reset the task, it should be done
        isEncoding = False      # Reset the task, it should be done
        server_msg.clear()      # Reset the server messages

    if isVigenering == True and len(server_msg) == 2:
        if (isEncoding):
            server_interaction.send_message("s", encode_vigenere(server_msg[1], server_msg[0].split(" ")[-1]))
        isVigenering = False
        isEncoding = False
        server_msg.clear()

    if isRSAing == True and len(server_msg) == 2:
        if (isEncoding):
            server_interaction.send_message("s", encode_rsa(server_msg[1], server_msg[0].split(", e=")[0].split("n=")[-1], server_msg[0].split(", e=")[-1]))
        isRSAing = False
        isEncoding = False
        server_msg.clear()

    if isHashing == True and len(server_msg) == 2:
        if (isVerifying == False):
            server_interaction.send_message("s", hash_hash(server_msg[1]))
            isHashing = False
            server_msg.clear()

    if isHashing == True and len(server_msg) == 3:
        if (isVerifying):
            server_interaction.send_message("s", hash_verify(server_msg[1], server_msg[2]))
            isHashing = False
            isVerifying = False
            server_msg.clear()

    if isDifHeling == True and difHelStep == 1 and len(server_msg) == 1:
        server_interaction.send_message("s", difhel(difHelStep))
        difHelStep += 1
        server_msg.clear()
        
    if isDifHeling == True and difHelStep == 2 and len(server_msg) == 2:
        server_interaction.send_message("s", difhel(difHelStep, server_msg[1]))
        difHelStep += 1
        server_msg.clear()

    if isDifHeling == True and difHelStep == 3 and len(server_msg) == 1:
        server_interaction.send_message("s", difhel(difHelStep))
        difHelStep = 0
        server_msg.clear()


# Encode the message with shift
def encode_shift(message, shift):
    """
    Encode the message by substracting the given shift key

    :params message: The message to encode 
    :params shift: The `int` shift key to use
    """
    result = bytearray()
    for c in message:
        # For every character in the message, 
        # sum the shift key with the unicode code 
        # and join it to the result as a string
        result.extend(int.to_bytes(int.from_bytes(c.encode()) + shift, 4))
    
    return result

# Decode the message with shift
def decode_shift(message, shift):
    """
    Decode the message by substracting the given shift key

    :params message: The message to decode 
    :params shift: The `int` shift key to use
    """
    result = bytearray()
    for c in message:
        # For every character in the message, 
        # subsctract the unicode code with the shift key 
        # and join it to the result as a string
        result.extend(int.to_bytes(int.from_bytes(c.encode()) - shift, 4))

    return result

def encode_vigenere(message, key):
    result = bytearray()

    for i, c in enumerate(message):
        intChar = int.from_bytes(c.encode())
        intKey = int.from_bytes(key[i % len(key)].encode())
        
        result.extend(int.to_bytes((intChar+intKey), 4))

    return result

def encode_rsa(message, key_n, key_e):
    result = bytearray()

    for c in message:
        result.extend(
            int.to_bytes(
                # Compute : c^e mod n
                pow(int.from_bytes(c.encode()), int(key_e), int(key_n))
                , 4
            )
        )

    return result

def hash_hash(message):
    result = bytearray()

    rslt = sha256(message.encode('utf-8')).hexdigest()
    for c in rslt:
        result.extend(int.to_bytes(int.from_bytes(c.encode()), 4))

    return result

def hash_verify(message, hash):
    result = bytearray()

    rslt = str(sha256(message.encode('utf-8')).hexdigest() == hash)

    for c in rslt:
        result.extend(int.to_bytes(int.from_bytes(c.encode()), 4))

    return result

def difhel(step, half_key=""):
    global dh_space
    match step:
        case 1:
            p = random.choice(list(primerange(3, 5000)))
            prim = primitive_root(int(p), False)
            dh_space = [p, prim, 0]
            return str(p) + "," + str(prim)
        case 2:
            b = random.choice(range(2, 50))
            s = pow(int(half_key), b, dh_space[0])
            dh_space[2] = s
            return str(pow(dh_space[1], b, dh_space[0]))
        case 3:
            return str(dh_space[2])

# Execute the crypto commands
def crypto(command: list[str]):
    """
    Process the crypto commands

    :params command: text commands splitted by spaces without the first cell
    """

    result = bytearray()
    # Retrieve if the operation is to encode or decode
    isEncode = command[1] == "encode"
    isVerifying = command[1] == "verify"
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
        case "vigenere":
            if isEncode:
                result = encode_vigenere(" ".join(command[2:-1]), command[-1])
        case "RSA":
            if isEncode:
                result = encode_rsa(" ".join(command[2:-1]), command[-1])
        case "hash":
            if isVerifying:
                result = hash_verify(" ".join(command[2:-1]), command[-1])
            else:
                result = hash_hash(" ".join(command[2::]))

    window.getWindow().add_message("<Crypto> " + " ".join(command))

    text = ""
    text += bytes(b for b in result if b != 0).decode('utf-8', 'replace')

    window.getWindow().add_message("<Crypto> " + text)