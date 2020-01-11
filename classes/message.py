"""This file contains definition for different kinds of messages."""


class Message:
    """
    Class for a piece of message. Can be all types like str, img or file, etc.
    Member Variables:
        sender_icon: the icon of the sender
        sender_id: the user who sends this message
        receiver_id: the user who receives this message
        t: time of sending or receiving
        message_type: 0 means str, 1 means img, 2 means file
    """

    def __init__(self, sender_icon, sender_id, receiver_id, t, message_type):
        self.sender_icon = sender_icon
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.t = t
        self.message_type = message_type


class DisplayMessage(Message):
    """
    Class for text that will be displayed in messagesLW.
    Also store this in Chat.history_message
    Member Variables:
        text: str content of the message
        img_path: if self is for displaying ImageMessage,
            then we should display the image in messagesLW.
    """

    def __init__(self, sender_icon, sender_id, t, message_type, text, img_path=None):
        # we don't need receiver_id
        super(DisplayMessage, self).__init__(sender_icon, sender_id, None, t, message_type)

        self.text = text
        self.img_path = img_path


class TextMessage(Message):
    """
    Class for a single text.
    Member Variables:
        text: str content of the message
    """

    def __init__(self, sender_icon, sender_id, receiver_id, t, text):
        super(TextMessage, self).__init__(sender_icon, sender_id, receiver_id, t, message_type=0)

        self.text = text


class ImageMessage(Message):
    """
    Class for a single image.
    Member Variables:
        path: str path that you save the image
        size: image size (in bytes)
    """

    def __init__(self, sender_icon, sender_id, receiver_id, t, path, size):
        super(ImageMessage, self).__init__(sender_icon, sender_id, receiver_id, t, message_type=1)

        self.path = path
        self.size = size


class FileMessage(Message):
    """
    Class for a single file.
    Member Variables:
        path: str path that you save the file
        size: file size (in bytes)
    """

    def __init__(self, sender_icon, sender_id, receiver_id, t, path, size):
        super(FileMessage, self).__init__(sender_icon, sender_id, receiver_id, t, message_type=2)

        self.path = path
        self.size = size
