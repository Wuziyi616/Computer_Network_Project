import os
import pdb
import sys
import time
import copy
import socket
from threading import Thread

from PyQt5.QtGui import QIcon, QPalette, QBrush, QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QListWidgetItem
from PyQt5.QtCore import QTimer, pyqtSignal, Qt, QSize

from sub_windows import LogInWin, AddGroupWin
from UI.chat_window import Ui_MainWindow as ChatWindow

import utils
import config
import central_server_connector
from classes.user import User
from classes.message import DisplayMessage
from classes.microphone import VoiceRecoder
from classes.chat import PrivateChat, GroupChat, VideoChat


class MainWin(QMainWindow, ChatWindow):
    # custom signal
    voice_to_text_signal = pyqtSignal(str)
    display_message_signal = pyqtSignal(DisplayMessage)
    new_message_signal = pyqtSignal(str)
    friend_delete_chat_signal = pyqtSignal(str)
    friend_log_out_signal = pyqtSignal(str)
    video_chat_request_signal = pyqtSignal(str)
    video_chat_agree_signal = pyqtSignal(str)
    video_chat_reject_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MainWin, self).__init__(parent)
        self.setupUi(self)

        # about program owner
        self.central_server_connector = None
        self.use_my_central_server = False
        self.server_sock = None
        self.update_status_timer = QTimer()
        self.update_status_timer.timeout.connect(self.update_user_status)

        # about all users
        self.me_user = None
        self.all_users = {}

        # about all chats
        self.all_chats = {}

        # about sending message
        self.current_target = None  # private chat or group chat
        self.current_message_type = 0
        self.video_chat = None

        # voice translate to text input
        self.voice_translator = VoiceRecoder()

        # sub-windows
        self.log_in_win = LogInWin()
        self.add_group_win = AddGroupWin()

        # signal and slot
        self.normal_chat_signals = (
            self.display_message_signal,
            self.new_message_signal,
            self.friend_delete_chat_signal,
            self.friend_log_out_signal
        )
        self.video_chat_signals = (
            self.video_chat_request_signal,
            self.video_chat_agree_signal,
            self.video_chat_reject_signal
        )
        self.init_signal_and_slot()

        # init controls
        self.init_controls()

        # background image
        self.init_background()

        # should log in first
        self.log_in_win.show()

    def init(self):
        """Initialize program."""
        self.titleLb.setText('Welcome, {}'.format(self.me_user.user_id))

        self.setup_server_sock()
        self.update_status_timer.start(config.UPDATE_STATUS_T)

        # create folder to save received images and files
        if not os.path.exists(config.IMAGE_SAVE_FOLDER):
            os.makedirs(config.IMAGE_SAVE_FOLDER)
        if not os.path.exists(config.FILE_SAVE_FOLDER):
            os.makedirs(config.FILE_SAVE_FOLDER)

    def init_signal_and_slot(self):
        """Call in self.__init__(), link signal and slot."""
        # Qt controls
        self.log_in_win.log_inBtn.clicked.connect(self.log_in)
        self.add_group_win.confirm_groupBtn.clicked.connect(self.add_group)

        self.log_outBtn.clicked.connect(self.log_out)
        self.add_friendBtn.clicked.connect(self.add_user)
        self.delete_friendBtn.clicked.connect(self.delete_user)
        self.friendsLW.itemClicked.connect(self.select_target_user)
        self.add_groupBtn.clicked.connect(self.show_add_group_win)
        self.delete_groupBtn.clicked.connect(self.delete_group)
        self.groupsLW.itemClicked.connect(self.select_target_group)
        self.emojiBtn.clicked.connect(self.emojiLW.show)
        self.emojiLW.itemClicked.connect(self.send_emoji)
        self.voice_to_textBtn.pressed.connect(self.voice_to_text_input)
        self.audioBtn.pressed.connect(self.send_audio)
        self.videoBtn.clicked.connect(self.start_video_chat)
        self.video_chat_request_signal.connect(self.receive_video_chat_request)
        self.video_chat_agree_signal.connect(self.receive_video_chat_agree)
        self.video_chat_reject_signal.connect(self.receive_video_chat_reject)

        self.sendBtn.clicked.connect(self.send_message)
        self.buttonGroup.buttonClicked.connect(self.select_message_type)

        # custom signal and slot
        self.display_message_signal.connect(self.display_message)
        self.new_message_signal.connect(self.mark_new_message)
        self.friend_delete_chat_signal.connect(self.friend_delete_chat)
        self.friend_log_out_signal.connect(self.friend_log_out)
        self.voice_to_text_signal.connect(self.set_messageTE)

    def init_controls(self):
        """Call in self.__init__(), set controls like icons for buttons."""
        # controls
        self.hide_message_widget()
        self.add_friendBtn.setIcon(QIcon('./src/btns/add.png'))
        self.delete_friendBtn.setIcon(QIcon('./src/btns/minus.png'))
        self.add_groupBtn.setIcon(QIcon('./src/btns/add.png'))
        self.delete_groupBtn.setIcon(QIcon('./src/btns/minus.png'))
        self.emojiBtn.setIcon(QIcon('./src/emoji/00.png'))
        self.emojiBtn.setFlat(True)
        self.voice_to_textBtn.setIcon(QIcon('./src/btns/voice_to_text.jpg'))
        self.voice_to_textBtn.setFlat(True)
        self.audioBtn.setIcon(QIcon('./src/btns/send_audio.jpg'))
        self.audioBtn.setFlat(True)
        self.videoBtn.setIcon(QIcon('./src/btns/video_chat.jpg'))
        self.videoBtn.setFlat(True)
        self.target_idLb.setText('')
        self.log_outBtn.setFlat(True)
        # self.sendBtn.setFlat(True)
        self.messagesLW.setIconSize(QSize(320, 320))

        # emoji
        all_emoji_path = os.listdir(config.EMOJI_PATH)
        all_emoji_path.sort()
        emoji_num = min(len(all_emoji_path), len(config.ALL_EMOJI))
        for emoji_path in all_emoji_path[:emoji_num]:
            self.emojiLW.addItem(
                QListWidgetItem(QIcon(os.path.join(config.EMOJI_PATH, emoji_path)), ''))
        self.emojiLW.hide()

    def init_background(self):
        """Call in self.__init__(), set the background image for MainWindow."""
        # background image
        palette = QPalette()
        palette.setBrush(self.backgroundRole(), QBrush(QPixmap(config.MAIN_WINDOW_BG)))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def setup_server_sock(self):
        """Establish self.client_server to stay listening port."""
        self.server_sock = \
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                self.server_sock.bind(('', self.me_user.port))
                break
            except OSError:
                self.me_user.port += 1
        self.server_sock.listen(1)

        # set a thread to run listening
        t = Thread(target=self.check_receive_message, daemon=True)
        t.start()

    def log_in(self):
        """User log in."""
        self.use_my_central_server = self.log_in_win.use_my_central_serverCB.isChecked()

        config.MY_IP = socket.gethostbyname(socket.gethostname())

        user_id = self.log_in_win.idLE.text()
        if not utils.is_valid_id(user_id):
            QMessageBox.information(None, 'warning', 'Invalid ID!', QMessageBox.Ok)
            return
        password = self.log_in_win.pswLE.text()

        # connect to central server
        if self.use_my_central_server:
            self.central_server_connector = \
                central_server_connector.MyCentralServerConnector(
                    config.MY_CENTRAL_SERVER_IP, config.MY_CENTRAL_SERVER_PORT)
        else:
            self.central_server_connector = \
                central_server_connector.CentralServerConnector(
                    config.CENTRAL_SERVER_IP, config.CENTRAL_SERVER_PORT)
        self.central_server_connector.connect()
        if not self.central_server_connector.is_connect:
            QMessageBox.information(None, 'warning', 'Cannot connect to central server!',
                                    QMessageBox.Ok)
            del self.central_server_connector
            self.central_server_connector = None
            return

        # user log in
        if self.use_my_central_server:
            self.central_server_connector.log_in(user_id, password, config.GENERAL_PORT)
        else:
            self.central_server_connector.log_in(user_id, password)
        if self.central_server_connector.is_log_in:
            QMessageBox.information(None, 'info', 'Log in successfully!', QMessageBox.Ok)
        else:
            QMessageBox.information(None, 'warning', 'Password error!', QMessageBox.Ok)
            del self.central_server_connector
            self.central_server_connector = None
            return

        self.log_in_win.idLE.setText('')
        self.log_in_win.pswLE.setText('')
        self.log_in_win.hide()

        # update my info
        self.me_user = User(user_id=user_id, name=None,
                            ip=config.MY_IP, port=config.GENERAL_PORT, icon=utils.get_icon())

        self.show()
        self.init()

        # update port information because default port maybe invalid
        if self.use_my_central_server:
            self.central_server_connector.log_in(user_id, password, self.me_user.port)

    def log_out(self):
        """User log out."""
        QMessageBox.information(None, 'info', 'You have logged out', QMessageBox.Ok)
        self.central_server_connector.log_out(self.me_user.user_id)
        self.central_server_connector.disconnect(self.me_user.user_id)
        self.clear_all()
        self.hide()

    def add_user(self):
        """Search new users via central server."""
        user_id = self.search_idLE.text()
        if not utils.is_valid_id(user_id):
            QMessageBox.information(None, 'warning', 'Invalid ID!', QMessageBox.Ok)
            return
        if user_id == self.me_user.user_id:
            QMessageBox.information(None, 'warning', 'Why searching for yourself?', QMessageBox.Ok)
            return
        if self.get_user_via_id(user_id) is not None:
            QMessageBox.information(None, 'info', 'User is already your friend!', QMessageBox.Ok)
            return

        # check whether online
        result = self.central_server_connector.search_user(user_id)
        if result == 'n':
            QMessageBox.information(None, 'info', 'User not online!', QMessageBox.Ok)
            return

        # update user
        if self.use_my_central_server:
            new_user = User(user_id=user_id, name=None,
                            ip=result[0], port=result[1], icon=utils.get_icon())
        else:
            new_user = User(user_id=user_id, name=None,
                            ip=result, port=config.GENERAL_PORT, icon=utils.get_icon())
        self.update_user(new_user, sock=None)
        self.search_idLE.setText('')

    def delete_user(self, passive=False):
        """Delete a user in self.
        If passive is True means it's the user that deletes me.
        """
        if not isinstance(self.current_target, PrivateChat):
            QMessageBox.information(None, 'info', 'Please select a user to delete', QMessageBox.Ok)
            return
        if not passive:
            reply = QMessageBox.question(None, 'warning',
                                         'Do you really want to delete user: {}'.
                                         format(self.current_target.other_user.user_id),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # video chat
        if self.video_chat is not None:
            self.end_video_chat()

        # delete friendsLW, all_users, all_private_chats
        del self.all_users[self.current_target.other_user.user_id]
        if not passive:
            self.current_target.send_delete_message()
        self.current_target.kill()
        del self.all_chats[self.current_target.name]
        item = self.friendsLW.currentItem()
        self.friendsLW.takeItem(self.friendsLW.row(item))
        self.clear_current_target()
        self.hide_message_widget()

    def remove_user(self, user_id):
        """When a friend deletes you or logs out,
            call this function to delete that user."""
        if isinstance(self.current_target, PrivateChat) and \
                user_id == self.current_target.other_user.user_id:
            self.delete_user(passive=True)
            return
        del self.all_users[user_id]
        private_chat_name = utils.get_chat_name_from_id([self.me_user.user_id, user_id])
        self.all_chats[private_chat_name].kill()
        del self.all_chats[private_chat_name]
        item = self.friendsLW.findItems(user_id, Qt.MatchStartsWith)[0]
        self.friendsLW.takeItem(self.friendsLW.row(item))

    def show_add_group_win(self):
        """Show self.add_group_win."""
        self.add_group_win.all_userLW.clear()
        for user in self.all_users.values():
            user_item = QListWidgetItem(user.icon, user.user_id)
            self.add_group_win.all_userLW.addItem(user_item)
        self.add_group_win.show()

    def add_group(self):
        """Add the users selected in self.add_group_win to create a GroupChat."""
        selected_items = self.add_group_win.all_userLW.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.information(None, 'info', 'Please select more than two users', QMessageBox.Ok)
            return

        # pick up selected users
        group_user = {}
        for item in selected_items:
            user_id = item.text()[:config.ID_LEN]
            user = self.get_user_via_id(user_id)
            group_user[user_id] = copy.deepcopy(user)

        # check unique
        chat_name = utils.get_chat_name_from_id(list(group_user.keys()) + [self.me_user.user_id])
        if self.get_chat_via_name(chat_name) is not None:
            QMessageBox.information(None, 'info', 'Group already exists!', QMessageBox.Ok)
            return

        # add to self.chats
        new_group_chat = GroupChat(self.me_user, group_user, self.normal_chat_signals,
                                   group_leader_id=None, sock=None)
        new_group_chat.start()
        self.update_chat(new_group_chat)

        t = Thread(target=new_group_chat.init_socks, daemon=True)
        t.start()

        self.add_group_win.hide()

    def delete_group(self, passive=False):
        """Delete a group chat in self.
        If passive is True means it's the someone in the group that deletes me.
        """
        if not isinstance(self.current_target, GroupChat):
            QMessageBox.information(None, 'info', 'Please select a group to delete', QMessageBox.Ok)
            return
        if not passive:
            reply = QMessageBox.question(None, 'warning',
                                         'Do you really want to delete group: {}'.
                                         format(self.current_target.name),
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # delete groupsLW, all_group_chats
        if not passive:
            self.current_target.send_delete_message()
        self.current_target.kill()
        del self.all_chats[self.current_target.name]
        item = self.groupsLW.currentItem()
        self.groupsLW.takeItem(self.groupsLW.row(item))
        self.clear_current_target()
        self.hide_message_widget()

    def remove_group(self, group_name):
        if isinstance(self.current_target, GroupChat) and \
                group_name == self.current_target.name:
            self.delete_group(passive=True)
            return
        self.all_chats[group_name].kill()
        del self.all_chats[group_name]
        item = self.groupsLW.findItems(group_name, Qt.MatchStartsWith)[0]
        self.groupsLW.takeItem(self.groupsLW.row(item))

    def select_target_user(self):
        """Select a user in self.friendsLW and start a private chat."""
        try:
            selected_user_id = self.friendsLW.currentItem().text()[:config.ID_LEN]
            chat_name = utils.get_chat_name_from_id([self.me_user.user_id, selected_user_id])
            # change last chat state
            if self.current_target is not None:
                if self.current_target.name == chat_name:
                    return
                self.current_target.select_state_change()

            # delete '\n (new message)' mark
            if self.friendsLW.currentItem().text().endswith('(new message)'):
                self.friendsLW.currentItem().setText(self.friendsLW.currentItem().text()[:-15])

            self.current_target = self.get_chat_via_name(chat_name)
            self.current_target.select_state_change()

            self.target_idLb.setText(self.current_target.other_user.user_id)
            self.show_message_widget()
            self.update_message_widget()
        except AttributeError:
            self.clear_current_target()

    def select_target_group(self):
        """Select a group in self.groupsLW and start a group chat."""
        try:
            selected_group_name = self.groupsLW.currentItem().text()
            # change last chat state
            if self.current_target is not None:
                if self.current_target.name == selected_group_name:
                    return
                self.current_target.select_state_change()

            # delete '\n (new message)' mark
            if self.groupsLW.currentItem().text().endswith('(new message)'):
                self.groupsLW.currentItem().setText(self.groupsLW.currentItem().text()[:-15])
            self.current_target = self.get_chat_via_name(selected_group_name)
            self.current_target.select_state_change()

            self.target_idLb.setText(self.current_target.name)
            self.show_message_widget()
            self.update_message_widget()
        except AttributeError:
            self.clear_current_target()

    def update_chat(self, new_chat):
        """Update self.all_private/group_chats."""
        self.all_chats[new_chat.name] = new_chat
        if isinstance(new_chat, GroupChat):
            new_group_item = QListWidgetItem(new_chat.name)
            self.groupsLW.addItem(new_group_item)

    def update_user(self, new_user, sock=None):
        """Add a new user item to self.friendsLW."""
        self.all_users[new_user.user_id] = copy.deepcopy(new_user)
        new_user_item = QListWidgetItem(utils.get_icon(), new_user.user_id + '  (online)')
        self.friendsLW.addItem(new_user_item)

        # update private chat
        new_private_chat = PrivateChat(self.me_user, copy.deepcopy(new_user),
                                       self.normal_chat_signals, self.video_chat_signals,
                                       sock=sock)
        new_private_chat.start()
        self.update_chat(new_private_chat)

    def update_user_status(self):
        """Check online/offline of self.all_users, update their ip."""
        all_users_key = list(self.all_users.keys())
        for i in range(len(all_users_key)):
            key = all_users_key[i]
            result = self.central_server_connector.search_user(self.all_users[key].user_id)
            if result == 'n' and 'online' in self.friendsLW.item(i).text():
                self.friendsLW.item(i).setText(
                    self.friendsLW.item(i).text().replace('online', 'offline'))
            elif result != 'n' and 'offline' in self.friendsLW.item(i).text():
                self.friendsLW.item(i).setText(
                    self.friendsLW.item(i).text().replace('offline', 'online'))

    def send_message(self):
        """Send message to self.current_target."""
        new_message = self.messageTE.toPlainText()
        if not new_message:
            QMessageBox.information(None, 'info', 'Cannot send empty message!', QMessageBox.Ok)
            return
        if self.current_message_type in (1, 2):
            if not os.path.isfile(new_message):
                QMessageBox.information(None, 'warning', 'File not exist!', QMessageBox.Ok)
                return

        self.messageTE.clear()

        t = Thread(target=self.handle_send_message,
                   args=(new_message,), daemon=True)
        t.start()

    def handle_send_message(self, new_message):
        """Handle sending message, which maybe text, image or file.
        This function will be called in multi-threading!
        """
        # send to private chat or group chat
        display_message = self.current_target.send_message(self.current_message_type, new_message)

        # display finish message
        self.display_message_signal.emit(display_message)

    def check_receive_message(self):
        """Check if there are any messages sent to the program."""
        while True:
            sock, address = self.server_sock.accept()
            t = Thread(target=self.handle_receive_message,
                       args=(sock, address), daemon=True)
            t.start()

    def handle_receive_message(self, sock, address):
        """Handle received message, which maybe text, image or file.
        This function will be called in multi-threading!
        """
        ip, _ = address
        decoded_message = utils.decode_message(utils.recv_msg(sock))
        if decoded_message is None:
            return

        chat_name, port, message_type, sender_id, _, _ = decoded_message

        # should only receive chat request or response in this function!
        try:
            assert message_type in [3, 4, 5, 6]
        except AssertionError:
            return

        if message_type == 3:  # private chat request
            sender = self.get_user_via_id(sender_id)
            if sender is None:
                # other wants to start a private chat with me
                sender = User(user_id=sender_id, name=None,
                              ip=ip, port=port, icon=utils.get_icon())
                self.update_user(sender, sock=sock)
            else:
                # the user exists but still want a new chat
                # may because other deletes me and then add me back
                pass
        elif message_type == 4:  # group chat request
            chat = self.get_chat_via_name(chat_name)
            if chat is None:
                # other wants to start a group chat with me
                user_ids = utils.get_id_from_chat_name(chat_name)
                group_users = {}
                for user_id in user_ids:
                    if user_id == self.me_user.user_id:
                        continue
                    exist_user = self.get_user_via_id(user_id)
                    if exist_user is None:
                        result = self.central_server_connector.search_user(user_id)
                        if self.use_my_central_server:
                            exist_user = User(user_id=user_id, name=None, ip=result[0],
                                              port=result[1], icon=utils.get_icon())
                        else:
                            exist_user = User(user_id=user_id, name=None, ip=result,
                                              port=config.GENERAL_PORT, icon=utils.get_icon())
                    else:
                        exist_user = copy.deepcopy(exist_user)
                    group_users[user_id] = exist_user
                chat = GroupChat(self.me_user, group_users, self.normal_chat_signals,
                                 group_leader_id=sender_id, sock=sock)
                chat.start()
                self.update_chat(chat)

                t = Thread(target=chat.init_socks, daemon=True)
                t.start()

            else:
                # group chat exists
                pass
        elif message_type == 5:  # private chat response
            # actually useless
            pass
        elif message_type == 6:  # group chat response
            # just update this sock to this group chat
            chat = self.get_chat_via_name(chat_name)
            if chat is None:
                return
            chat.update_server_sock(sock, sender_id)

    def select_message_type(self, btn):
        """Specify the type of next sending message."""
        if btn.text() == 'Text':
            self.current_message_type = 0
        elif btn.text() == 'Image':
            self.current_message_type = 1
        elif btn.text() == 'File':
            self.current_message_type = 2

    def update_message_widget(self):
        """When select a new chat, we should clear self.messagesLW and
            display self.current_target.message_history on it.
        """
        self.messagesLW.clear()
        for message in self.current_target.message_history:
            if isinstance(message, DisplayMessage):
                self.display_message(message)

    def send_emoji(self):
        """Send emoji."""
        idx = self.emojiLW.currentRow()
        self.messageTE.setPlainText(self.messageTE.toPlainText() + config.ALL_EMOJI[idx])
        self.emojiLW.hide()

    def start_video_chat(self):
        """Send video chat request to start a video chat."""
        if self.video_chat is not None:
            self.end_video_chat()
            return

        self.video_chat = VideoChat(self.me_user,
                                    copy.deepcopy(self.current_target.other_user))
        self.current_target.send_video_chat_request()

    def end_video_chat(self):
        """End a video chat."""
        self.video_chat.kill()
        del self.video_chat
        self.video_chat = None

    def voice_to_text_input(self):
        """Slot for translating input."""
        t = Thread(target=self.translate_voice, daemon=True)
        t.start()

    def translate_voice(self):
        """Translate voice to text into self.messageTE."""
        self.voice_translator.translate = True
        t = Thread(target=self.voice_translator.record_audio,
                   daemon=True)
        t.start()
        start_time = time.time()
        while self.voice_to_textBtn.isDown():  # keep recording when pressing button
            time.sleep(0.1)

        self.voice_translator.kill()
        if time.time() - start_time < 0.5:
            QMessageBox.information(None, 'warning', 'Speaking time too short!', QMessageBox.Ok)
            return
        while not self.voice_translator.done:  # wait for saving and translating
            time.sleep(0.1)
        if self.voice_translator.last_translate_result is None:
            return

        # change to sending translated text
        self.voice_to_text_signal.emit(self.voice_translator.last_translate_result)
        self.is_textRBtn.setChecked(True)
        self.current_message_type = 0

    def send_audio(self):
        """Slot for sending audio file."""
        t = Thread(target=self.record_audio, daemon=True)
        t.start()

    def record_audio(self):
        """Translate voice to text into self.messageTE."""
        self.voice_translator.translate = False
        t = Thread(target=self.voice_translator.record_audio,
                   daemon=True)
        t.start()
        start_time = time.time()
        while self.audioBtn.isDown():  # keep recording when pressing button
            time.sleep(0.1)

        self.voice_translator.kill()
        if time.time() - start_time < 0.5:
            QMessageBox.information(None, 'warning', 'Speaking time too short!', QMessageBox.Ok)
            return
        while not self.voice_translator.done:  # wait for saving and translating
            time.sleep(0.1)

        # change to sending wave file
        self.voice_to_text_signal.emit(self.voice_translator.last_path)
        self.is_fileRBtn.setChecked(True)
        self.current_message_type = 2

    def display_message(self, display_message):
        """Display DisplayMessage in self.messagesLW."""
        message_info = \
            QListWidgetItem(
                display_message.sender_icon,
                display_message.sender_id + '  ' + display_message.t)

        # display image rather than text for ImageMessage
        if display_message.message_type == 1:
            message_content = QListWidgetItem(QIcon(display_message.img_path), '')
        else:
            message_content = QListWidgetItem(display_message.text)
        if display_message.sender_id == self.me_user.user_id:
            message_content.setBackground(QColor(0, 255, 0, 127))
        self.messagesLW.addItem(message_info)
        self.messagesLW.addItem(message_content)
        self.messagesLW.verticalScrollBar().setValue(
            self.messagesLW.verticalScrollBar().maximum())

    def friend_delete_chat(self, chat_name):
        """When a friend of you deletes you, should also delete that friend."""
        chat = self.get_chat_via_name(chat_name)
        if chat is None:
            return
        if isinstance(chat, PrivateChat):
            sender_id = chat.other_user.user_id
            self.remove_user(sender_id)
            QMessageBox.information(None, 'info', 'User {} deleted you!'.format(sender_id), QMessageBox.Ok)
        else:
            self.remove_group(chat_name)
            QMessageBox.information(None, 'info', 'Group chat {} ends!'.format(chat_name), QMessageBox.Ok)

    def friend_log_out(self, chat_name):
        """When a friend of you logs out, should also remove that friend."""
        chat = self.get_chat_via_name(chat_name)
        if chat is None:
            return
        if isinstance(chat, PrivateChat):
            sender_id = chat.other_user.user_id
            self.remove_user(sender_id)
            QMessageBox.information(None, 'info', 'User {} logged out!'.format(sender_id), QMessageBox.Ok)
        else:
            self.remove_group(chat_name)
            QMessageBox.information(None, 'info', 'Group chat {} ends!'.format(chat_name), QMessageBox.Ok)

    def receive_video_chat_request(self, chat_name):
        """Someone wants to start a video chat, send response."""
        chat = self.get_chat_via_name(chat_name)
        if chat is None:
            return
        if self.video_chat is not None:  # can't do two video chats at once
            if self.video_chat.is_alive:
                chat.send_video_chat_reject()
                return
            else:
                self.video_chat.kill()
                del self.video_chat
                self.video_chat = None
        reply = QMessageBox.question(None, 'info',
                                     '{} wants to start video chat with you, do you agree?'.
                                     format(chat.other_user.user_id),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        # reject
        if reply == QMessageBox.No:
            chat.send_video_chat_reject()
            return

        # agree
        chat.send_video_chat_agree()
        self.video_chat = VideoChat(self.me_user,
                                    copy.deepcopy(chat.other_user))
        self.video_chat.start()

    def receive_video_chat_agree(self, chat_name):
        """Your friend agrees your video chat request."""
        if self.video_chat is None:
            return
        chat = self.get_chat_via_name(chat_name)
        if chat is None:
            return
        if not chat.other_user == self.video_chat.other_user:
            return

        self.video_chat.start()

    def receive_video_chat_reject(self, chat_name):
        """Your friend agrees your video chat request."""
        if self.video_chat is None:
            return
        chat = self.get_chat_via_name(chat_name)
        if chat is None:
            return
        if not chat.other_user == self.video_chat.other_user:
            return
        del self.video_chat
        self.video_chat = None

    def get_user_via_id(self, user_id):
        """Returns the user in self.all_users."""
        try:
            return self.all_users[user_id]
        except KeyError:
            return None

    def get_chat_via_name(self, chat_name):
        """Returns the chat in self.all_private/group_chats"""
        try:
            return self.all_chats[chat_name]
        except KeyError:
            return None

    def mark_new_message(self, chat_name):
        """Mark with suffix '\n (new message)'."""
        if len(chat_name) < 30:  # private chat
            # match from start since there maybe '(online)' in the end
            try:
                item = self.friendsLW.findItems(chat_name[config.ID_LEN + 1:], Qt.MatchStartsWith)[0]
            except IndexError:
                item = self.friendsLW.findItems(chat_name[:config.ID_LEN], Qt.MatchStartsWith)[0]
        else:
            # match exactly because there won't any prefix/suffix in group chat name
            try:
                item = self.groupsLW.findItems(chat_name, Qt.MatchStartsWith)[0]
            except IndexError:
                return

        if not item.text().endswith('(new message)'):
            item.setText(item.text() + '\n (new message)')

    def set_messageTE(self, text):
        self.messageTE.setPlainText(text)

    def clear_all(self):
        self.hide_message_widget()
        self.stop_all_timer()
        self.friendsLW.clear()
        self.messagesLW.clear()
        self.all_users.clear()
        for chat in self.all_chats.values():
            chat.send_log_out_message()
            chat.kill()
        self.all_chats.clear()
        self.server_sock.close()
        self.log_in_win.show()

    def clear_current_target(self):
        """Set self.current_target to None and clear id label."""
        self.current_target = None
        self.target_idLb.setText('')

    def stop_all_timer(self):
        self.update_status_timer.stop()

    def hide_message_widget(self):
        """Hide the controls about message part when we're not chatting with anyone."""
        self.messagesLW.hide()
        self.messageTE.hide()
        self.is_textRBtn.hide()
        self.is_imageRBtn.hide()
        self.is_fileRBtn.hide()
        self.sendBtn.hide()
        self.emojiBtn.hide()
        self.videoBtn.hide()
        self.audioBtn.hide()
        self.voice_to_textBtn.hide()
        self.messagesLW.clear()
        self.messageTE.clear()

    def show_message_widget(self):
        """Show the controls about message part when we begin to chat with someone."""
        self.messagesLW.show()
        self.messageTE.show()
        self.is_textRBtn.show()
        self.is_imageRBtn.show()
        self.is_fileRBtn.show()
        self.sendBtn.show()
        self.emojiBtn.show()

        # some functions only implemented in private chat mode
        if isinstance(self.current_target, PrivateChat):
            self.videoBtn.show()
            self.audioBtn.show()
            self.voice_to_textBtn.show()
        else:
            self.videoBtn.hide()
            self.audioBtn.hide()
            self.voice_to_textBtn.hide()

    def show_(self):
        """I want to show the log in dialog first, but pyqt requires to show the main window first."""
        self.show()
        self.hide()

    def closeEvent(self, event):
        """Kill all the threads."""
        self.log_out()
        os._exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = MainWin()
    main_win.show_()
    sys.exit(app.exec_())
