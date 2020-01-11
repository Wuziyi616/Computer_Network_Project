"""This file contains class for a single user."""


class User:
    """
    Class for a user.
    Member Variables:
        user_id: id of the user
        name: the nickname (if exists) of the user, could be assigned by the user
        ip: ip address of the user
        port: port of the user
        icon: icon to be displayed
        message_history: all history-received/sent messages
    """

    def __init__(self, user_id, name=None, ip=None, port=None, icon=None):
        self.user_id = user_id
        self.name = name if name is not None else user_id
        self.ip = ip
        self.port = port
        self.icon = icon

    def __eq__(self, other):
        return self.user_id == other.user_id

    def __deepcopy__(self, memo):
        return User(self.user_id, self.name, self.ip, self.port, self.icon)
