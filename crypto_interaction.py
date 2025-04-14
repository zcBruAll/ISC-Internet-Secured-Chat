# -------------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------------
from hashlib import sha256                   # For computing SHA-256 hashes.
import random                                # For generating random numbers (used in various crypto functions).
from cryptography.hazmat.primitives.asymmetric import dh    # For Diffie-Hellman key exchange primitives.
from sympy import primerange, primitive_root   # For generating a range of prime numbers and finding primitive roots.

from communicator import comm                # Custom communication module; used to emit signals to update the UI.

import window                                # Custom module to interact with the GUI (details within the module).
import server_interaction                    # Custom module to interact with the server for sending messages.

# -------------------------------------------------------------------
# GLOBAL FLAGS & VARIABLES
# -------------------------------------------------------------------
# Flags indicating which crypto task is active.
isShifting = False       # Flag for Shift cipher operations.
isVigenering = False     # Flag for Vigenère cipher operations.
isRSAing = False         # Flag for RSA encryption operations.
isHashing = False        # Flag for Hashing operations.
isDifHeling = False      # Flag for Diffie-Hellman operations.

# Additional flags to distinguish between encoding and verifying operations.
isEncoding = False       # Flag to indicate whether the task is to encode.
isVerifying = False      # Flag to indicate whether the task is to verify a hash.

difHelStep = 0           # Counter to track steps in the Diffie-Hellman key exchange.

# To store Diffie-Hellman parameters:
# [prime modulus (p), primitive root (g), shared secret computed later]
dh_space = [0, 0, 0]

# List to store messages received from the server.
server_msg = list[str]()   # Using type hinting to indicate a list of strings.

# -------------------------------------------------------------------
# FUNCTION: appendServerMsg
# -------------------------------------------------------------------
def appendServerMsg(msg: str):
    """
    Append the server message to the message list and execute the linked crypto tasks when enough messages are received.

    :param msg: The decoded message received from the server.
    """
    global isShifting, isVigenering, isRSAing, isHashing, isDifHeling
    global isEncoding, isVerifying, difHelStep

    # Append the received message to the global server_msg list.
    server_msg.append(msg)

    # -------------------------------------------------------------------
    # Handling Shift Cipher
    # If shifting is active and two messages have been received:
    #   - The first message likely contains a key.
    #   - The second is the actual message to encode.
    # -------------------------------------------------------------------
    if isShifting == True and len(server_msg) == 2:
        if isEncoding:
            # Extract the shift key from the first message (assumed to be the last space-separated value)
            key = int(server_msg[0].split(" ")[-1])
            # Encode the message using the shift cipher and send it to the server.
            server_interaction.send_message("s", encode_shift(server_msg[1], key))
        # Reset related flags and clear stored server messages.
        isShifting = False      
        isEncoding = False      
        server_msg.clear()

    # -------------------------------------------------------------------
    # Handling Vigenère Cipher
    # Similar to shift cipher, expecting two messages (one for key, one for message).
    # -------------------------------------------------------------------
    if isVigenering == True and len(server_msg) == 2:
        if isEncoding:
            # The key is taken from the first message (last space-separated token).
            server_interaction.send_message("s", encode_vigenere(server_msg[1], server_msg[0].split(" ")[-1]))
        isVigenering = False
        isEncoding = False
        server_msg.clear()

    # -------------------------------------------------------------------
    # Handling RSA Encryption
    # Here also two messages are expected: one with RSA parameters and one with the plain message.
    # The RSA parameters are extracted from the first message.
    # -------------------------------------------------------------------
    if isRSAing == True and len(server_msg) == 2:
        if isEncoding:
            # Expecting RSA parameters in the form "... n=<n_value>, e=<e_value>"
            n_value = server_msg[0].split(", e=")[0].split("n=")[-1]
            e_value = server_msg[0].split(", e=")[-1]
            server_interaction.send_message("s", encode_rsa(server_msg[1], n_value, e_value))
        isRSAing = False
        isEncoding = False
        server_msg.clear()

    # -------------------------------------------------------------------
    # Handling Hashing for generating a hash
    # When verifying is false: only one additional message is needed to create the hash.
    # -------------------------------------------------------------------
    if isHashing == True and len(server_msg) == 2:
        if isVerifying == False:
            server_interaction.send_message("s", hash_hash(server_msg[1]))
            isHashing = False
            server_msg.clear()

    # -------------------------------------------------------------------
    # Handling Hash Verification
    # Expecting two messages: one with the plain message and one with the expected hash.
    # -------------------------------------------------------------------
    if isHashing == True and len(server_msg) == 3:
        if isVerifying:
            server_interaction.send_message("s", hash_verify(server_msg[1], server_msg[2]))
            isHashing = False
            isVerifying = False
            server_msg.clear()

    # -------------------------------------------------------------------
    # Handling Diffie-Hellman (DifHel)
    # The process proceeds in steps:
    #   Step 1: Generate prime and primitive root.
    #   Step 2: Compute partial key.
    #   Step 3: Finalize the shared secret.
    # -------------------------------------------------------------------
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

# -------------------------------------------------------------------
# FUNCTION: encode_shift
# -------------------------------------------------------------------
def encode_shift(message, shift):
    """
    Encode the message using a shift cipher where each character's Unicode code is increased by the given shift.

    :param message: The string message to encode.
    :param shift: An integer representing the shift key.
    :return: A bytearray containing the encoded message, where each character is stored in 4 bytes.
    """
    result = bytearray()
    # For each character in the message, convert to its integer code value, add the shift, and convert back to bytes.
    for c in message:
        # Convert the character to bytes, add the shift, then convert back to a 4-byte representation.
        result.extend(int.to_bytes(int.from_bytes(c.encode()), 4))
        # Note: The example adds the shift value inside int.from_bytes conversion.
        # Ensure that the shift is correctly applied in your implementation.
        # (The current implementation sums the shift to the byte conversion.)
        result[-4:] = int.to_bytes(int.from_bytes(c.encode()) + shift, 4)
    return result

# -------------------------------------------------------------------
# FUNCTION: decode_shift
# -------------------------------------------------------------------
def decode_shift(message, shift):
    """
    Decode the message previously encoded with a shift cipher.

    :param message: The string message to decode.
    :param shift: An integer representing the shift key.
    :return: A bytearray containing the decoded message.
    """
    result = bytearray()
    # Reverse the encoding by subtracting the shift from each character's code.
    for c in message:
        result.extend(int.to_bytes(int.from_bytes(c.encode()) - shift, 4))
    return result

# -------------------------------------------------------------------
# FUNCTION: encode_vigenere
# -------------------------------------------------------------------
def encode_vigenere(message, key):
    """
    Encode the message using the Vigenère cipher.

    :param message: The string message to encode.
    :param key: The key string used in the Vigenère cipher.
    :return: A bytearray containing the encoded message.
    """
    result = bytearray()
    # For each character in the message, add the Unicode value of the corresponding key character.
    for i, c in enumerate(message):
        intChar = int.from_bytes(c.encode())
        intKey = int.from_bytes(key[i % len(key)].encode())
        result.extend(int.to_bytes((intChar + intKey), 4))
    return result

# -------------------------------------------------------------------
# FUNCTION: encode_rsa
# -------------------------------------------------------------------
def encode_rsa(message, key_n, key_e):
    """
    Encode the message using RSA encryption.

    For each character, compute c^e mod n (where c is the Unicode integer of the character).

    :param message: The string message to encode.
    :param key_n: The RSA modulus (n) as a string.
    :param key_e: The RSA public exponent (e) as a string.
    :return: A bytearray containing the RSA encrypted message.
    """
    result = bytearray()
    for c in message:
        # Compute RSA encryption for each character.
        encrypted = pow(int.from_bytes(c.encode()), int(key_e), int(key_n))
        result.extend(int.to_bytes(encrypted, 4))
    return result

# -------------------------------------------------------------------
# FUNCTION: hash_hash
# -------------------------------------------------------------------
def hash_hash(message):
    """
    Compute the SHA-256 hash of a message and encode it into a bytearray.

    :param message: The string message to hash.
    :return: A bytearray with the hexadecimal hash, where each character occupies 4 bytes.
    """
    result = bytearray()
    rslt = sha256(message.encode('utf-8')).hexdigest()
    # Convert each character of the hexadecimal hash to a 4-byte representation.
    for c in rslt:
        result.extend(int.to_bytes(int.from_bytes(c.encode()), 4))
    return result

# -------------------------------------------------------------------
# FUNCTION: hash_verify
# -------------------------------------------------------------------
def hash_verify(message, hash):
    """
    Verify if the SHA-256 hash of the message matches the provided hash.
    
    :param message: The string message to be hashed and verified.
    :param hash: The expected hash value as a string.
    :return: A bytearray indicating whether the computed hash equals the provided hash,
             encoded as "True" or "False" (each character in 4 bytes).
    """
    result = bytearray()
    # Compare the computed hash with the provided hash and convert the result to string.
    rslt = str(sha256(message.encode('utf-8')).hexdigest() == hash)
    for c in rslt:
        result.extend(int.to_bytes(int.from_bytes(c.encode()), 4))
    return result

# -------------------------------------------------------------------
# FUNCTION: difhel
# -------------------------------------------------------------------
def difhel(step, half_key=""):
    """
    Perform a step in the Diffie-Hellman key exchange process.

    :param step: An integer indicating the current step (1, 2, or 3).
    :param half_key: (Optional) In step 2, the partial key received from the other party.
    :return: A string representing the parameters or the computed value for the current step.
    """
    global dh_space
    # Use Python 3.10 structural pattern matching to decide the operation based on the step.
    match step:
        case 1:
            # Step 1: Choose a random prime and its primitive root.
            p = random.choice(list(primerange(3, 5000)))  # Select a random prime between 3 and 5000.
            prim = primitive_root(int(p), False)          # Find a primitive root for p.
            dh_space = [p, prim, 0]                         # Store the prime and primitive root.
            return str(p) + "," + str(prim)                 # Return the prime and primitive root as a comma-separated string.
        case 2:
            # Step 2: Choose a random private key 'b', compute the partial key and the shared secret.
            b = random.choice(range(2, 50))
            s = pow(int(half_key), b, dh_space[0])          # Compute shared secret using the received half_key.
            dh_space[2] = s                                 # Store the shared secret.
            return str(pow(dh_space[1], b, dh_space[0]))    # Return the computed partial key.
        case 3:
            # Step 3: Return the shared secret.
            return str(dh_space[2])

# -------------------------------------------------------------------
# FUNCTION: crypto
# -------------------------------------------------------------------
def crypto(command: list[str]):
    """
    Execute cryptographic commands based on the parsed input command list.
    
    The command list is expected to include:
      - The cipher type (e.g., "shift", "vigenere", "RSA", "hash")
      - The operation (e.g., "encode", "decode", "verify")
      - The message and associated keys.

    :param command: List of string tokens from the command (without the initial identifier).
    """
    result = bytearray()
    # Determine if we are encoding or verifying based on the command.
    isEncode = command[1] == "encode"
    isVerifying = command[1] == "verify"
    
    # Use structural pattern matching on the cipher type.
    match command[0]:
        case "shift":
            if isEncode:
                # For shift encoding, join the message tokens (from 3rd to second-last) and retrieve the shift key.
                result = encode_shift(" ".join(command[2:-1]), int(command[-1]))
            else:
                # For shift decoding, perform the reverse operation.
                result = decode_shift(" ".join(command[2:-1]), int(command[-1]))
        case "vigenere":
            if isEncode:
                result = encode_vigenere(" ".join(command[2:-1]), command[-1])
        case "RSA":
            if isEncode:
                # For RSA, expects the key as the last token; the message is the concatenation of tokens in between.
                result = encode_rsa(" ".join(command[2:-1]), command[-1])
        case "hash":
            if isVerifying:
                result = hash_verify(" ".join(command[2:-1]), command[-1])
            else:
                result = hash_hash(" ".join(command[2::]))

    # Emit the original crypto command to the UI.
    comm.chat_msg.emit("<Crypto>", " ".join(command))

    text = ""
    # Convert the bytearray result into a string, filtering out null bytes.
    text += bytes(b for b in result if b != 0).decode('utf-8', 'replace')

    # Emit the resulting text back to the UI.
    comm.chat_msg.emit("<Crypto>", text)
