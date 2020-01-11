"""This file contains some common settings for the project."""

import socket
from pyaudio import paInt16

# central server
CENTRAL_SERVER_IP = '166.111.140.57'
CENTRAL_SERVER_PORT = 8000

# my info
MY_ID = None  # '2017011527'
MY_IP = None
MY_CENTRAL_SERVER_IP = socket.gethostbyname(socket.gethostname())
MY_CENTRAL_SERVER_PORT = 10000

# hyper-parameters for the program
GENERAL_PORT = 2333
MAX_PACKAGE_SIZE = 1024
UPDATE_STATUS_T = 5000  # T for update status timer
INVALID_PORT = [3306, 5432, 6379, 8080, 8888, 9200, 27017, 22122]  # invalid port
ID_LEN = 10
ALL_EMOJI = [
    '😀', '😁', '😂', '🤣', '😃', '😅', '😉',
    '😎', '😍', '😘', '🤔', '🤐', '😶', '🙄',
    '😥', '😪', '😣', '😴', '😒', '🙃', '😤',
    '😭', '😨', '😱', '😡', '😷', '👻', '💩'
]

# about voice recoder
VOICE_PORT = 2334
VOICE_CHUNK = 256
VOICE_FORMAT = paInt16
VOICE_CHANNELS = 1
VOICE_RATE = 16000
MAX_RECORD_SECONDS = 1

# baidu audio translation API
API_KEY = 'kVcnfD9iW2XVZSMaLMrtLYIz'
SECRET_KEY = 'O9o1O213UgG5LFn0bDGNtoRN3VWl2du6'
CUID = '123456PYTHON'
ASR_URL = 'http://vop.baidu.com/server_api'
SCOPE = 'audio_voice_assistant_get'
TOKEN_URL = 'http://openapi.baidu.com/oauth/2.0/token'

# about video capturing
VIDEO_PORT = 2335
UPDATE_VIDEO_INTERVAL = 1000
IDEAL_VIDEO_FREQUENCY = 10  # try to send video images in this frequency
WORST_RESIZE_RATIO = 0.5

# about path
IMAGE_SAVE_FOLDER = './receive/imgs/'
FILE_SAVE_FOLDER = './receive/files/'
LOG_IN_WINDOW_BG = './src/btns/BGI_IT.jpg'
MAIN_WINDOW_BG = './src/btns/BGI7.jpg'
ICON_PATH = './src/icons/'
EMOJI_PATH = './src/emoji/'
VOICE_PATH = './src/voice/'
VIDEO_PATH = './src/video/'

# communication protocol
"""
For text, it's 'ChatName_ListeningPort_type_id_content_0_length'
There are totally 9 types of message:
    0: text, 1: image, 2: file,
    3: private_chat_request, 4: group_chat_request,
    5: private_chat_response, 6: group_chat_response,
    7: friend_delete_chat, 8: friend_log_out
    9: video_chat_request, 10: video_chat_response
For text message: directly display them in messagesLW
For image and file, they maybe quite large and can't be sent once.
So we manually split it to several config.MAX_PACKAGE_SIZE bits packages and send them by:
    1. send 'ChatName_ListeningPort_type_id_filename_FileSize'
    2. iteratively send the split packages
For chat request & response:
    Once a request is required, everyone involved in the chat will
        have a socket with other user(s).
    Then, they keep those sockets in chat class and keep listening & sending
        via them, which means I will only socket.connect() once!
"""
MESSAGE_TYPE = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
