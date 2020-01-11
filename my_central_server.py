"""This class is my implemented central server.
Every time a user log in, it needs to report the ip & port to this server.
Also user can query other user's ip & port here.
So it's more convenient for single PC debug.
"""

import socket
import time
from threading import Thread

import utils
import config


class CommandError(Exception):
    pass


class MyCentralServer(Thread):
    """
    My implemented central server.
        log in command: UserID_net2019_ListeningPort
        query command: q_UserID
        log out command: logoutUserID
    """

    def __init__(self, listen_port):
        super(MyCentralServer, self).__init__()

        self.setDaemon(True)
        self.listen_port = listen_port
        self.sock = None
        self.all_users = {}

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', self.listen_port))
        self.sock.listen(1)

        # listen to user
        while True:
            sock, address = self.sock.accept()
            t = Thread(target=self.handle_request,
                       args=(sock, address), daemon=True)
            t.start()

    def handle_request(self, sock, address):
        """Response to query."""
        ip, _ = address
        while True:
            command = sock.recv(config.MAX_PACKAGE_SIZE).decode()
            try:
                if command.startswith('20'):  # log in command
                    idx1 = command.index('_')
                    idx2 = command.rindex('_')
                    if idx1 == idx2:
                        raise CommandError
                    user_id = command[:idx1]
                    psw = command[idx1 + 1:idx2]
                    port = int(command[idx2 + 1:])
                    if psw != 'net2019' or not utils.is_valid_id(user_id) or \
                            not utils.is_valid_port(port):
                        raise CommandError
                    self.all_users[user_id] = {'ip': ip, 'port': port}
                    sock.send('lol'.encode())
                elif command.startswith('q'):  # query command
                    user_id = command[1:]
                    if not utils.is_valid_id(user_id) or user_id not in self.all_users.keys():
                        sock.send('n'.encode())
                        continue
                    sock.send('{}_{}'.format(
                        self.all_users[user_id]['ip'], self.all_users[user_id]['port']).encode())
                elif command.startswith('logout'):  # log out command
                    user_id = command[6:]
                    if not utils.is_valid_id(user_id):
                        raise CommandError
                    del self.all_users[user_id]
                    sock.send('loo'.encode())
                    return
                else:
                    raise CommandError
            except CommandError:
                self.return_error(sock)

    @staticmethod
    def return_error(sock):
        sock.send('Invalid Command!'.encode())


if __name__ == '__main__':
    server = MyCentralServer(config.MY_CENTRAL_SERVER_PORT)
    server.start()
    while True:
        time.sleep(1)
