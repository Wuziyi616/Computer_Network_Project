"""This file contains class for processing voice collected from PC microphone.
Part of the code adopted from https://www.cnblogs.com/lmg-jie/p/9629123.html
"""

import os
import time
import wave
import json
import base64
import struct
import socket
from pyaudio import PyAudio
from threading import Thread
from pickle import dumps, loads
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode

import config


class VoiceRecoder:

    def __init__(self):

        self.chunk = config.VOICE_CHUNK
        self.format = config.VOICE_FORMAT
        self.channels = config.VOICE_CHANNELS
        self.rate = config.VOICE_RATE
        self.max_record_seconds = config.MAX_RECORD_SECONDS * 50
        self.language = 1536

        # mark whether is still recording
        self.is_alive = False
        self.translate = False
        self.done = False
        self.last_path = None
        self.last_translate_result = None

    def record_audio(self):
        """Record audio data from microphone."""
        self.is_alive = True
        self.done = False
        current_datetime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        output_file_path = os.path.join(config.VOICE_PATH, current_datetime + '.wav')
        recoder = PyAudio()
        audio_stream = recoder.open(format=self.format, channels=self.channels, rate=self.rate,
                                    input=True, frames_per_buffer=self.chunk)
        audio_frames = []

        # begin recoding
        while self.is_alive:
            audio_data = audio_stream.read(self.chunk)
            audio_frames.append(audio_data)

        # close stream
        audio_stream.stop_stream()
        audio_stream.close()
        recoder.terminate()

        # write into file
        wave_file = wave.open(output_file_path, 'wb')
        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(recoder.get_sample_size(self.format))
        wave_file.setframerate(self.rate)
        wave_file.writeframes(b''.join(audio_frames))
        wave_file.close()

        self.last_path = output_file_path
        if self.translate:
            self.last_translate_result = self.translate_to_text(self.last_path)
            os.remove(self.last_path)  # remove wave file
            self.last_path = None
        self.done = True

    # https://github.com/Baidu-AIP/speech-demo/tree/master/rest-api-asr/python
    def translate_to_text(self, wave_file, language=1536):
        """Get the corresponding text for a given audio file.
        Input:
            wave_file: file path
            language: 1536 is Chinese, 1737 is English
        """
        file_format = wave_file[-3:]

        class DemoError(Exception):
            pass

        def fetch_token():
            params = {'grant_type': 'client_credentials',
                      'client_id': config.API_KEY,
                      'client_secret': config.SECRET_KEY}
            post_data = urlencode(params)
            post_data = post_data.encode('utf-8')
            req = Request(config.TOKEN_URL, post_data)
            try:
                f = urlopen(req)
                result_str = f.read()
            except URLError as err:
                result_str = err.read()
                raise DemoError(result_str)
            result_str = result_str.decode()
            result = json.loads(result_str)
            if 'access_token' in result.keys() and 'scope' in result.keys():
                return result['access_token']
            else:
                raise DemoError(
                    'MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response')

        try:
            token = fetch_token()
        except DemoError:
            return None

        with open(wave_file, 'rb') as speech_file:
            speech_data = speech_file.read()

        length = len(speech_data)
        if length == 0:
            return None

        speech = base64.b64encode(speech_data)
        speech = str(speech, 'utf-8')
        params = {
            'dev_pid': language,
            'format': file_format,
            'rate': self.rate,
            'token': token,
            'cuid': config.CUID,
            'channel': 1,
            'speech': speech,
            'len': length
        }
        post_data = json.dumps(params, sort_keys=False)
        req = Request(config.ASR_URL, post_data.encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        try:
            f = urlopen(req)
            result_str = f.read()
        except URLError:
            return None

        result_str = str(result_str, 'utf-8')

        # get result text from result_str
        try:
            idx_start = result_str.index('[')
            idx_end = result_str.index(']')
        except ValueError:
            return None

        return result_str[idx_start + 2:idx_end - 1]

    def kill(self):
        self.is_alive = False


class AudioClient(Thread):
    """Client class for sending audio data to server.
    Keep running as a thread until self.sock is deleted.
    """

    def __init__(self, ip, port):
        super(AudioClient, self).__init__()

        self.setDaemon(True)
        self.address = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recoder = PyAudio()
        self.audio_stream = None

        # parameters for recording
        self.chunk = config.VOICE_CHUNK
        self.format = config.VOICE_FORMAT
        self.channels = config.VOICE_CHANNELS
        self.rate = config.VOICE_RATE
        self.max_record_seconds = config.MAX_RECORD_SECONDS * 50

        self.is_alive = True

    def __del__(self):
        self.sock.close()
        if self.audio_stream is not None:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        self.recoder.terminate()

    def run(self):
        while True:
            try:
                self.sock.connect(self.address)
                break
            except ConnectionRefusedError:
                time.sleep(1)

        self.audio_stream = self.recoder.open(format=self.format, channels=self.channels, rate=self.rate,
                                              input=True, frames_per_buffer=self.chunk)
        while self.audio_stream.is_active() and self.is_alive:
            audio_frames = []

            # begin recoding
            time_count = self.max_record_seconds
            while True:
                audio_data = self.audio_stream.read(self.chunk)
                audio_frames.append(audio_data)
                time_count -= 1
                if time_count == 0:
                    break

            # send data
            audio_frames = dumps(audio_frames)
            try:
                self.sock.sendall(struct.pack('L', len(audio_frames)) + audio_frames)
            except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError):
                self.kill()
                return

    def kill(self):
        """Kill the thread."""
        self.is_alive = False


class AudioServer(Thread):
    """Server class for receiving audio data from client.
    Keep running as a thread until self.sock is deleted.
    """

    def __init__(self, port):
        super(AudioServer, self).__init__()

        self.setDaemon(True)
        self.address = ('', port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recoder = PyAudio()
        self.audio_stream = None

        # parameters for recording
        self.chunk = config.VOICE_CHUNK
        self.format = config.VOICE_FORMAT
        self.channels = config.VOICE_CHANNELS
        self.rate = config.VOICE_RATE
        self.max_record_seconds = config.MAX_RECORD_SECONDS * 50

        self.is_alive = True

    def __del__(self):
        self.sock.close()
        if self.audio_stream is not None:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        self.recoder.terminate()

    def run(self):
        self.sock.bind(self.address)
        self.sock.listen(1)
        client_sock, _ = self.sock.accept()

        payload_size = struct.calcsize('L')
        self.audio_stream = self.recoder.open(format=self.format, channels=self.channels, rate=self.rate,
                                              output=True, frames_per_buffer=self.chunk)
        audio_data = ''.encode('utf-8')
        while self.is_alive:  # get one piece and output per iteration
            packed_data = client_sock.recv(payload_size)
            msg_size = struct.unpack('L', packed_data)[0]
            while len(audio_data) < msg_size:
                next_size = config.MAX_PACKAGE_SIZE if \
                    len(audio_data) + config.MAX_PACKAGE_SIZE <= msg_size else \
                    msg_size - len(audio_data)
                next_data = client_sock.recv(next_size)
                audio_data += next_data
            audio_frames = loads(audio_data)
            for frame in audio_frames:
                self.audio_stream.write(frame, self.chunk)
            audio_data = ''.encode('utf-8')

    def kill(self):
        """Kill the thread."""
        self.is_alive = False
