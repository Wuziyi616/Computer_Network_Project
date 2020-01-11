"""This file contains class for capturing and receive videos from PC camera.
Part of the code adopted from https://www.cnblogs.com/lmg-jie/p/9629123.html
"""

import os
import time
import struct
import socket
from threading import Thread
from pickle import dumps, loads
from zlib import compress, decompress, Z_BEST_COMPRESSION
from cv2 import VideoCapture, resize, INTER_CUBIC, destroyAllWindows, \
    namedWindow, imshow, waitKey, WINDOW_NORMAL

import config


class CameraReader:
    """Class for read image from PC camera, process it and receive.
    Every time I call encode_image(), will return a np.array image captured by PC camera.
    Will count the times that encode_image() is called, then I can adjust image quality
        according to the frequency.
    """

    def __init__(self):

        self.start_time = time.time()
        self.times = 0
        self.frequency = 0.
        self.cap = VideoCapture(0)
        self.resize_ratio = 1.

    def encode_frame(self):
        if not self.cap.isOpened():
            return None
        _, frame = self.cap.read()

        # count frequency
        self.times += 1
        self.frequency = self.times / (time.time() - self.start_time)

        # adjust image size dynamically
        if self.times % config.UPDATE_VIDEO_INTERVAL == 0:
            self.times = 0
            if self.frequency > config.IDEAL_VIDEO_FREQUENCY / 0.9:
                self.resize_ratio = min(self.resize_ratio / 0.9, config.IDEAL_VIDEO_FREQUENCY)
            elif self.frequency < config.IDEAL_VIDEO_FREQUENCY * 0.9:
                self.resize_ratio = max(self.resize_ratio * 0.9, config.WORST_RESIZE_RATIO)

        # resize image
        frame = resize(frame, (0, 0), fx=self.resize_ratio, fy=self.resize_ratio,
                       interpolation=INTER_CUBIC)

        # compress the data
        data = dumps(frame)
        compressed_data = compress(data, Z_BEST_COMPRESSION)

        return compressed_data

    @staticmethod
    def decode_frame(compressed_data):
        """Uncompress and return."""
        data = decompress(compressed_data)
        frame = loads(data)
        return frame

    def __del__(self):
        self.cap.release()


class VideoClient(Thread):
    """Client class for sending video data to server.
    Keep running as a thread until self.sock is deleted.
    """

    def __init__(self, ip, port):
        super(VideoClient, self).__init__()

        self.setDaemon(True)
        self.address = (ip, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.camera_reader = CameraReader()

        self.is_alive = True

    def __del__(self):
        self.sock.close()
        del self.camera_reader

    def run(self):
        while True:
            try:
                self.sock.connect(self.address)
                break
            except ConnectionRefusedError:
                time.sleep(1)

        while self.is_alive:
            video_data = self.camera_reader.encode_frame()

            time.sleep(0.05)

            try:
                self.sock.sendall(struct.pack('L', len(video_data)) + video_data)
            except (ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError):
                self.kill()
                return

    def kill(self):
        """Kill the thread."""
        self.is_alive = False


class VideoServer(Thread):
    """Server class for receiving video data from client.
    Keep running as a thread until self.sock is deleted.
    """

    def __init__(self, port, client_name):
        super(VideoServer, self).__init__()

        self.setDaemon(True)
        self.address = ('', port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_name = client_name

        self.is_alive = True

    def __del__(self):
        self.sock.close()
        try:
            destroyAllWindows()
        except WindowsError:
            pass

    def run(self):
        self.sock.bind(self.address)
        self.sock.listen(1)
        client_sock, _ = self.sock.accept()

        video_data = ''.encode('utf-8')
        payload_size = struct.calcsize('L')
        namedWindow(self.client_name, WINDOW_NORMAL)

        while self.is_alive:  # get one piece and output per iteration
            packed_data = client_sock.recv(payload_size)
            msg_size = struct.unpack('L', packed_data)[0]
            while len(video_data) < msg_size:
                next_size = config.MAX_PACKAGE_SIZE if \
                    len(video_data) + config.MAX_PACKAGE_SIZE <= msg_size else \
                    msg_size - len(video_data)
                next_data = client_sock.recv(next_size)
                video_data += next_data
            video_frame = CameraReader.decode_frame(video_data)
            imshow(self.client_name, video_frame)

            if waitKey(1) & 0xFF == ord('q'):
                self.kill()
                return

            video_data = ''.encode('utf-8')

    def kill(self):
        """Kill the thread."""
        self.is_alive = False
