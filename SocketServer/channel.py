import json


class Channel:
    def __init__(self, name):
        self.name = name
        self.handlers = []

    def join(self, handler):
        if handler.channel:
            handler.channel.leave(handler)
        self.handlers.append(handler)
        handler.channel = self
        self.send({
            'type': 'user_connected',
            'data': handler.get_information()
        })

    def send(self, data):
        for handler in self.handlers:
            try:
                handler.send(data)
            except Exception as ex:
                print(ex)

    def send_pm(self, data, users):
        """
        Send private message
        :param data: data to send
        :param users: list or str
        :return: None
        """
        if type(users) == list:
            for handler in self.handlers:
                if handler.name in users:
                    handler.send(data)
        elif type(users) == str:
            for handler in self.handlers:
                if handler.name == users:
                    handler.send(data)
                    break

    def leave(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
            self.send({
                'type': 'user_disconnected',
                'data': handler.get_information()
            })
        handler.channel = None
