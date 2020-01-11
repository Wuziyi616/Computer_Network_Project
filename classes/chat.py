"""This file contains classes for chats, including private, group, video chats."""

import os
import time
import socket
from numpy import array
from threading import Thread
from .camera import VideoServer, VideoClient
from .microphone import AudioServer, AudioClient

import utils
import config
from .message import TextMessage, ImageMessage, FileMessage, DisplayMessage


class Chat(Thread):
    """Basic class for private and group chat.
    Member Variables:
        me_user: me
        other_user: another user (maybe be one person or many persons)
        message_history: a list of past received or sent messages
    """

    def __init__(self, me_user, other_user, signals):
        super(Chat, self).__init__()

        self.me_user = me_user
        self.other_user = other_user
        self.name = None
        self.is_current = False
        self.is_alive = True

        self.message_history = []

        self.display_message_signal = signals[0]
        self.new_message_signal = signals[1]
        self.friend_delete_chat_signal = signals[2]
        self.friend_log_out_signal = signals[3]

    def __eq__(self, other):
        pass

    def __hash__(self):
        return hash(id(self))

    def run(self):
        """Iteratively check self.sock(s) for new message."""
        pass

    def send_message(self, message_type, new_message):
        """Send message to self.other_user"""
        pass

    def send_text_message(self, text_message, sock):
        """Send text message via client_sock."""
        utils.send_msg(sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            0, self.me_user.user_id, text_message.text, 0))
        return DisplayMessage(text_message.sender_icon, text_message.sender_id,
                              text_message.t, 0, text_message.text)

    def send_image_message(self, image_message, sock):
        """Send image message via client_sock.
        Split the image into different packages,
            first send 'type_id_filename', then send packages.
        """
        # send notification message
        utils.send_msg(sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            1, self.me_user.user_id, image_message.path,
                                            image_message.size))
        # start send image packages
        image = open(image_message.path, 'rb')
        while True:
            package = image.read(config.MAX_PACKAGE_SIZE)

            time.sleep(0.001)

            if not package:  # image send over
                break
            while True:
                try:
                    sock.send(package)
                    break
                except BlockingIOError:
                    time.sleep(0.001)
        image.close()
        return DisplayMessage(image_message.sender_icon, image_message.sender_id,
                              image_message.t, 1,
                              'Image {} send success!'.format(image_message.path),
                              img_path=image_message.path)

    def send_file_message(self, file_message, sock):
        """Send file message via client_sock.
        Split the file into different packages,
            first send 'type_id_filename', then send packages.
        """
        # send notification message
        utils.send_msg(sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            2, self.me_user.user_id, file_message.path,
                                            file_message.size))
        # start send file packages
        file = open(file_message.path, 'rb')
        while True:
            package = file.read(config.MAX_PACKAGE_SIZE)
            if not package:  # file send over
                break
            while True:
                try:
                    sock.send(package)
                    break
                except BlockingIOError:
                    time.sleep(0.001)
        file.close()
        return DisplayMessage(file_message.sender_icon, file_message.sender_id,
                              file_message.t, 2,
                              'File {} send success!'.format(file_message.path))

    def receive_message(self, decoded_message, sock, sender):
        """Receive message from someone."""
        _, _, message_type, _, receive_text, file_size = decoded_message
        receive_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        if message_type == 0:  # text
            receive_message = \
                TextMessage(sender.icon, sender.user_id, self.me_user.user_id,
                            receive_time, receive_text)
            display_message = self.receive_text_message(receive_message)
        elif message_type == 1:  # image
            receive_message = \
                ImageMessage(sender.icon, sender.user_id, self.me_user.user_id,
                             receive_time, receive_text, file_size)
            display_message = self.receive_image_message(receive_message, sock)
        elif message_type == 2:  # file
            receive_message = \
                FileMessage(sender.icon, sender.user_id, self.me_user.user_id,
                            receive_time, receive_text, file_size)
            display_message = self.receive_file_message(receive_message, sock)

        self.update_history_message(display_message)

        return display_message

    def receive_text_message(self, text_message):
        """Process received text message.
        Currently only display it.
        """
        return DisplayMessage(text_message.sender_icon, text_message.sender_id,
                              text_message.t, 0, text_message.text)

    def receive_image_message(self, image_message, sock):
        """Process received image message.
        Currently only store it in ./receive/imgs/file_name,
            may also display it on screen in the future.
        """
        # write image into file
        filename = utils.get_filename_from_path(image_message.path)
        save_path = os.path.join(config.IMAGE_SAVE_FOLDER, filename)

        # write to file
        self.write_to_file(save_path, image_message, sock)

        # display
        return DisplayMessage(image_message.sender_icon, image_message.sender_id,
                              image_message.t, 1, 'Receive image, saved to {}'.format(save_path),
                              img_path=save_path)

    def receive_file_message(self, file_message, sock):
        """Process received file message.
        Currently only store it in ./receive/files/file_name.
        """
        # write into file
        filename = utils.get_filename_from_path(file_message.path)
        save_path = os.path.join(config.FILE_SAVE_FOLDER, filename)

        # write to file
        self.write_to_file(save_path, file_message, sock)

        # display
        return DisplayMessage(file_message.sender_icon, file_message.sender_id,
                              file_message.t, 2, 'Receive file, saved to {}'.format(save_path))

    @staticmethod
    def write_to_file(save_path, info_message, sock):
        file = open(save_path, 'wb')
        received_size = 0  # count the exact size to receive
        while True:
            next_size = config.MAX_PACKAGE_SIZE if \
                received_size + config.MAX_PACKAGE_SIZE <= info_message.size else \
                info_message.size - received_size
            while True:
                try:
                    package = sock.recv(next_size)
                    break
                except BlockingIOError:
                    pass
            file.write(package)
            received_size += next_size
            if received_size >= info_message.size:
                break
        file.close()

    def check_chat_end(self, message_type):
        """If a user within the chat deletes the chat or logs out."""
        if message_type == 7:
            self.friend_delete_chat_signal.emit(self.name)
            return True
        elif message_type == 8:
            self.friend_log_out_signal.emit(self.name)
            return True
        return False

    def update_history_message(self, new_message):
        self.message_history.append(new_message)

    def select_state_change(self):
        """Change self.is_current to reverse."""
        self.is_current = not self.is_current

    def kill(self):
        """Kill the thread."""
        self.is_alive = False


class PrivateChat(Chat):
    """Class for a chat between two users.
    Input:
        sock: if None, meaning I'm starter and should send request to other user.
            else I should send response to other user.

    Member Variables:
        name: chat name, which is unique among all chats.
        sock: keep checking it and sending message via it.
    """

    def __init__(self, me_user, other_user,
                 normal_chat_signals, video_chat_signals, sock=None):
        super(PrivateChat, self).__init__(me_user, other_user, normal_chat_signals)

        # signals for video chat
        self.video_request_signal = video_chat_signals[0]
        self.video_agree_signal = video_chat_signals[1]
        self.video_reject_signal = video_chat_signals[2]

        # generate name for the private chat
        # in the order of sort()
        all_id = [me_user.user_id, other_user.user_id]
        self.name = utils.get_chat_name_from_id(all_id)  # len == 21

        # setup socket
        if sock is None:  # I start the chat, should send a request
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.other_user.ip, self.other_user.port))
        else:
            self.sock = sock
        self.sock.setblocking(False)

        # if I start this chat, then I should send private chat request
        if sock is None:
            utils.send_msg(self.sock,
                           utils.encode_message(self.name, self.me_user.port,
                                                3, self.me_user.user_id, '', 0))
        # can only send one thing at one time
        self.is_sending = False

        # when receiving images or files, not check self.sock
        self.is_receiving = False

    def __del__(self):
        self.sock.close()

    def __eq__(self, other):
        return isinstance(other, PrivateChat) and self.name == other.name

    def __hash__(self):
        return hash(id(self))

    def run(self):
        """Check self.sock."""
        while self.is_alive:
            # if is receiving image or file, not check
            while self.is_receiving:
                time.sleep(0.1)
            try:
                message = utils.recv_msg(self.sock)
            except BlockingIOError:
                time.sleep(0.1)
                continue
            self.is_receiving = True
            t = Thread(target=self.handle_receive_message,
                       args=(message,), daemon=True)
            t.start()

    def handle_receive_message(self, message):
        """Handle received message, which maybe text, image or file."""
        decoded_message = utils.decode_message(message)
        if decoded_message is None:
            self.is_receiving = False
            return

        chat_name = decoded_message[0]
        message_type = decoded_message[2]

        # make sure it's for this chat
        if chat_name != self.name:
            self.is_receiving = False
            return

        # maybe that friend deletes you or logs out
        chat_end = self.check_chat_end(message_type)
        if chat_end:
            self.is_receiving = False
            return

        # maybe that friend wants to start a video chat with you
        video_chat = self.check_video_chat(message_type, decoded_message[4])
        if video_chat:
            self.is_receiving = False
            return

        display_message = self.receive_message(decoded_message, self.sock, self.other_user)

        self.is_receiving = False

        # optionally display
        if self.is_current:
            self.display_message_signal.emit(display_message)
        else:  # mark with '(new message)'
            self.new_message_signal.emit(self.name)

    def send_message(self, message_type, new_message):
        """Only need to send to one person."""
        while self.is_sending:  # send one thing at one time
            time.sleep(0.1)

        self.is_sending = True

        send_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # different types of message
        if message_type == 0:  # text
            new_text_message = \
                TextMessage(self.me_user.icon, self.me_user.user_id,
                            self.other_user.user_id, send_time, new_message)
            display_message = self.send_text_message(new_text_message, self.sock)
        elif message_type == 1:  # image
            new_image_message = \
                ImageMessage(self.me_user.icon, self.me_user.user_id,
                             self.other_user.user_id, send_time, new_message,
                             os.stat(new_message).st_size)
            display_message = self.send_image_message(new_image_message, self.sock)
        elif message_type == 2:  # file
            new_file_message = \
                FileMessage(self.me_user.icon, self.me_user.user_id,
                            self.other_user.user_id, send_time, new_message,
                            os.stat(new_message).st_size)
            display_message = self.send_file_message(new_file_message, self.sock)

        self.is_sending = False

        self.update_history_message(display_message)

        return display_message

    def send_video_chat_request(self):
        """Send a message to inform video chat request."""
        utils.send_msg(self.sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            9, self.me_user.user_id, '', 0))

    def send_video_chat_agree(self):
        """Send a message to inform video chat request."""
        utils.send_msg(self.sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            10, self.me_user.user_id, 'y', 0))

    def send_video_chat_reject(self):
        """Send a message to inform video chat request."""
        utils.send_msg(self.sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            10, self.me_user.user_id, 'n', 0))

    def send_delete_message(self):
        """Delete other user as your friend, send a message to inform."""
        utils.send_msg(self.sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            7, self.me_user.user_id, '', 0))

    def send_log_out_message(self):
        """Delete other user as your friend, send a message to inform."""
        utils.send_msg(self.sock,
                       utils.encode_message(self.name, self.me_user.port,
                                            8, self.me_user.user_id, '', 0))

    def check_video_chat(self, message_type, message_content):
        """Check whether the received message is about video chat."""
        if message_type == 9:
            self.video_request_signal.emit(self.name)
            return True
        elif message_type == 10:
            if message_content == 'y':
                self.video_agree_signal.emit(self.name)
            elif message_content == 'n':
                self.video_reject_signal.emit(self.name)
            return True
        return False


class GroupChat(Chat):
    """Class for a group of users.
    Input:
        sock: the sock connected to me from group_leader_id user.
            If None, meaning I'm the starter and should send request to all others.
            Else I should send response to users whose user_id is
                larger (list.sort()) than me (except group_leader).

    Member Variables:
        name: the unique identity of a group chat (also unique among all chats).
            In the form of 'id1-id2-id3...', in the order of np.sort!
        socks: a dict of sockets. Keep checking them and sending message via them.
            Every time sending a message, just iterate over all of them.
    """

    def __init__(self, me_user, other_user, normal_chat_signals,
                 group_leader_id=None, sock=None):
        super(GroupChat, self).__init__(me_user, other_user, normal_chat_signals)

        # generate the name for the group chat
        # in the order of sort()
        all_id = list(self.other_user.keys()) + [self.me_user.user_id]
        self.name = utils.get_chat_name_from_id(all_id)  # len >= 33

        # setup sockets for every user
        self.socks = {user_id: None for user_id in self.other_user.keys()}

        # set up sock for leader
        if group_leader_id is not None:
            sock.setblocking(False)
            self.socks[group_leader_id] = sock

        # flags
        self.group_leader_id = group_leader_id
        self.is_sending = False
        self.is_receiving = {user_id: False for user_id in self.other_user.keys()}

    def __del__(self):
        [sock.close() for sock in self.socks.values()]

    def __eq__(self, other):
        return isinstance(other, GroupChat) and self.name == other.name

    def __hash__(self):
        return hash(id(self))

    def run(self):
        """Check every sock in self.server_socks."""
        while array([sock is None for sock in self.socks.values()]).any():  # someone haven't confirm
            time.sleep(0.1)
        while self.is_alive:
            for key, sock in self.socks.items():

                if self.is_receiving[key]:
                    continue

                try:
                    message = utils.recv_msg(sock)
                except BlockingIOError:
                    continue

                self.is_receiving[key] = True

                t = Thread(target=self.handle_receive_message,
                           args=(message, key), daemon=True)
                t.start()

    def init_socks(self):
        """Connect sockets with users whose id is less than me."""
        if self.group_leader_id is None:  # I start the chat, should send request to other users
            for user in self.other_user.values():
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((user.ip, user.port))
                self.socks[user.user_id] = sock
                sock.setblocking(False)
                utils.send_msg(sock,
                               utils.encode_message(self.name, self.me_user.port,
                                                    4, self.me_user.user_id, '', 0))
        else:  # should send response to those whose user_id is larger than me
            time.sleep(1)  # wait for everyone to first create a GroupChat and update
            for user in self.other_user.values():
                if self.me_user.user_id > user.user_id or user.user_id == self.group_leader_id:
                    continue
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((user.ip, user.port))
                self.socks[user.user_id] = sock
                sock.setblocking(False)
                utils.send_msg(sock,
                               utils.encode_message(self.name, self.me_user.port,
                                                    6, self.me_user.user_id, '', 0))

    def handle_receive_message(self, message, key):
        """Handle received message, which maybe text, image or file."""
        decoded_message = utils.decode_message(message)
        if decoded_message is None:
            self.is_receiving[key] = False
            return

        chat_name = decoded_message[0]
        message_type = decoded_message[2]

        if chat_name != self.name:
            self.is_receiving[key] = False
            return

        # maybe a user deletes the chat or logs out
        chat_end = self.check_chat_end(message_type)
        if chat_end:
            self.is_receiving[key] = False
            return

        display_message = self.receive_message(decoded_message,
                                               self.socks[key], self.other_user[key])

        self.is_receiving[key] = False

        # optionally display
        if self.is_current:
            self.display_message_signal.emit(display_message)
        else:  # mark with '(new message)'
            self.new_message_signal.emit(self.name)

    def send_message(self, message_type, new_message):
        """Needs to send to all users in self.other_user."""
        while self.is_sending:
            time.sleep(0.1)

        send_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # first pack the message in a Message class
        if message_type == 0:  # text
            new_message = \
                TextMessage(self.me_user.icon, self.me_user.user_id,
                            None, send_time, new_message)
        elif message_type == 1:  # image
            new_message = \
                ImageMessage(self.me_user.icon, self.me_user.user_id,
                             None, send_time, new_message,
                             os.stat(new_message).st_size)
        elif message_type == 2:  # file
            new_message = \
                FileMessage(self.me_user.icon, self.me_user.user_id,
                            None, send_time, new_message,
                            os.stat(new_message).st_size)

        # then iterate over all users in self.other_user to send message
        self.is_sending = True
        display_message = None
        for key, user in self.other_user.items():
            new_message.receiver_id = user.user_id

            # different types of message
            if message_type == 0:  # text
                display_message = self.send_text_message(new_message, self.socks[key])
            elif message_type == 1:  # image
                display_message = self.send_image_message(new_message, self.socks[key])
            elif message_type == 2:  # file
                display_message = self.send_file_message(new_message, self.socks[key])

        self.is_sending = False

        # finally store history message
        self.update_history_message(display_message)

        return display_message

    def send_delete_message(self):
        """Delete other user as your friend, send a message to inform."""
        for sock in self.socks.values():
            utils.send_msg(sock,
                           utils.encode_message(self.name, self.me_user.port,
                                                7, self.me_user.user_id, '', 0))

    def send_log_out_message(self):
        """Delete other user as your friend, send a message to inform."""
        for sock in self.socks.values():
            utils.send_msg(sock,
                           utils.encode_message(self.name, self.me_user.port,
                                                8, self.me_user.user_id, '', 0))

    def update_server_sock(self, sock, user_id):
        """Set self.server_socks according to id. (the socket that other user connect to me)"""
        sock.setblocking(False)
        self.socks[user_id] = sock


class VideoChat(Thread):
    """Class for a video chat.
    Inherit from thread because we can do other things when having video chat.
    We need to have four sockets:
        send video, send audio, receive video, receive audio
    """

    def __init__(self, me_user, other_user):
        super(VideoChat, self).__init__()

        self.me_user = me_user
        self.other_user = other_user

        # camera reader and voice recoder
        self.video_sender = VideoClient(self.other_user.ip, config.VIDEO_PORT)
        self.video_receiver = VideoServer(config.VIDEO_PORT, self.other_user.name)
        self.audio_sender = AudioClient(self.other_user.ip, config.VOICE_PORT)
        self.audio_receiver = AudioServer(config.VOICE_PORT)

        # mark whether it's still talking
        self.is_alive = False

    def __del__(self):
        del self.video_sender, self.audio_sender, self.video_receiver, self.audio_receiver

    def run(self):
        """Get video and audio piece then send."""
        self.is_alive = True
        self.video_sender.start()
        self.audio_sender.start()
        time.sleep(1)
        self.video_receiver.start()
        self.audio_receiver.start()

        while self.audio_sender.is_alive and self.video_sender.is_alive \
                and self.audio_receiver.is_alive and self.video_receiver.is_alive and \
                self.is_alive:
            time.sleep(1)
        self.kill()

    def kill(self):
        """Kill the thread."""
        self.video_sender.kill()
        self.audio_sender.kill()
        self.video_receiver.kill()
        self.audio_receiver.kill()
        self.is_alive = False
