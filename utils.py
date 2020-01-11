"""This file contains some utility functions."""

import os
import re
import struct
import random
from PyQt5.QtGui import QIcon

import config


def get_icon():
    """Randomly sample an icon and return."""
    all_icon_path = os.listdir(config.ICON_PATH)
    icon_path = random.sample(all_icon_path, 1)[0]
    return QIcon(os.path.join(config.ICON_PATH, icon_path))


def is_number(text):
    pattern = r'\d{' + str(len(text)) + '}'
    if re.match(pattern, text) is not None:
        return True
    return False


def is_valid_id(user_id):
    """Judge whether the id is valid. Should be ten digits."""
    pattern = r'\d{' + str(config.ID_LEN) + '}'
    if re.match(pattern, user_id) is not None:
        return True
    return False


def is_valid_port(port):
    if port <= 1024 or port > 65535 or port in config.INVALID_PORT:
        return False
    return True


def get_filename_from_path(text):
    """Get the filename from a piece of text.
    Find the last '/' and returns the words after that.
    """
    return text[text.rindex('/') + 1:]


def get_chat_name_from_id(all_id):
    """Get a chat name 'id1-id2-id3-...' from a list of id."""
    all_id.sort()
    chat_name = '{}'.format(all_id[0])
    for i in range(1, len(all_id)):
        chat_name += '-'
        chat_name += all_id[i]
    return chat_name


def get_id_from_chat_name(chat_name):
    """Get a list of id from 'id1-id2-id3-...'."""
    all_id = []
    while True:
        idx = chat_name.find('-')
        if idx == -1:
            all_id.append(chat_name)
            break
        all_id.append(chat_name[:config.ID_LEN])
        chat_name = chat_name[config.ID_LEN + 1:]
    return all_id


def encode_message(chat_name, port, message_type, sender_id, message, length):
    """Encode message for sending. In the format of ChatName_ListenPort_type_id_content_length.
    Actually length is only useful when sending images or files.
    """
    message = '{}_{}_{}_{}_{}_{}'.format(
        chat_name, port, message_type, sender_id, message, length)
    return message.encode()


def decode_message(message):
    """Decode received message. Returns chat_name, port, type, id and content (optionally length)."""
    try:
        message = message.decode()
    except AttributeError:
        return None

    # get chat_name
    idx = message.index('_')
    chat_name = message[:idx]
    message = message[idx + 1:]

    # get port
    idx = message.index('_')
    port = message[:idx]
    if not is_number(port):
        return None
    port = int(port)
    message = message[idx + 1:]

    # get length
    idx = message.rindex('_')
    length = message[idx + 1:]
    if not is_number(length):
        return None
    length = int(length)
    message = message[:idx]

    # type, id and content
    idx = message.index('_')
    message_type = int(message[:idx])
    if message_type not in config.MESSAGE_TYPE:
        return None
    message = message[idx + 1:]
    sender_id = message[:10]
    if not is_valid_id(sender_id):
        return None
    return [chat_name, port, message_type, sender_id, message[11:], length]


# https://stackoverflow.com/questions/17667903/python-socket-receive-large-amount-of-data
def send_msg(sock, msg):
    """Prefix each message with a 4-byte length (network byte order)"""
    msg = struct.pack('>I', len(msg)) + msg
    try:
        sock.sendall(msg)
    except ConnectionResetError:
        pass


def recv_msg(sock):
    """Read message length and unpack it into an integer"""
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    try:
        return recvall(sock, msglen)
    except ConnectionResetError:
        return None


def recvall(sock, n):
    """Helper function to recv n bytes or return None if EOF is hit"""
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data
