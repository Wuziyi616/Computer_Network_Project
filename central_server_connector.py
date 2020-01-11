"""This file contains code for interact with the central server."""

import socket

import config


class CentralServerConnector:

    def __init__(self, ip, port):
        assert type(ip) is str
        assert type(port) is int

        self.central_server_ip = ip
        self.central_server_port = port

        self.central_server_sock = None
        self.is_connect = False
        self.is_log_in = False

    def connect(self):
        if self.is_connect:
            return
        self.central_server_sock = \
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.central_server_sock. \
                connect((self.central_server_ip, self.central_server_port))
        except ConnectionRefusedError:
            return
        self.is_connect = True

    def log_in(self, user_id, password):
        if not self.is_connect:
            self.connect()
        if self.is_log_in:
            return
        command = '{}_{}'.format(user_id, password)
        self.central_server_sock.send(command.encode())
        reply = self.central_server_sock.recv(config.MAX_PACKAGE_SIZE).decode()
        if reply == 'lol':
            self.is_log_in = True

    def log_out(self, user_id):
        if not self.is_log_in:
            return
        command = 'logout{}'.format(user_id)
        self.central_server_sock.send(command.encode())
        reply = self.central_server_sock.recv(config.MAX_PACKAGE_SIZE).decode()
        if reply == 'loo':
            self.is_log_in = False

    def disconnect(self, user_id):
        if not self.is_connect:
            return
        if self.is_log_in:
            self.log_out(user_id)
        self.central_server_sock.close()
        self.central_server_sock = None
        self.is_connect = False

    def search_user(self, user_id):
        """Search for a user using his/her id.
        If exists, return IP. Otherwise return 'n'.
        """
        command = 'q{}'.format(user_id)
        self.central_server_sock.send(command.encode())
        reply = self.central_server_sock.recv(config.MAX_PACKAGE_SIZE).decode()
        return reply


class MyCentralServerConnector:

    def __init__(self, ip, port):
        assert type(ip) is str
        assert type(port) is int

        self.central_server_ip = ip
        self.central_server_port = port

        self.central_server_sock = None
        self.is_connect = False
        self.is_log_in = False

    def connect(self):
        if self.is_connect:
            return
        self.central_server_sock = \
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.central_server_sock. \
                connect((self.central_server_ip, self.central_server_port))
        except ConnectionRefusedError:
            return
        self.is_connect = True

    def log_in(self, user_id, password, port):
        if not self.is_connect:
            self.connect()
        command = '{}_{}_{}'.format(user_id, password, port)
        self.central_server_sock.send(command.encode())
        reply = self.central_server_sock.recv(config.MAX_PACKAGE_SIZE).decode()

        if reply == 'lol':
            self.is_log_in = True

    def log_out(self, user_id):
        if not self.is_log_in:
            return
        command = 'logout{}'.format(user_id)
        self.central_server_sock.send(command.encode())
        reply = self.central_server_sock.recv(config.MAX_PACKAGE_SIZE).decode()
        if reply == 'loo':
            self.is_log_in = False

    def disconnect(self, user_id):
        if not self.is_connect:
            return
        if self.is_log_in:
            self.log_out(user_id)
        self.central_server_sock.close()
        self.central_server_sock = None
        self.is_connect = False

    def search_user(self, user_id):
        """Search for a user using his/her id.
        If exists, return IP and PORT. Otherwise return 'n'.
        """
        command = 'q{}'.format(user_id)
        self.central_server_sock.send(command.encode())
        reply = self.central_server_sock.recv(config.MAX_PACKAGE_SIZE).decode()
        if reply == 'n':
            return reply
        idx = reply.index('_')
        return reply[:idx], int(reply[idx + 1:])
