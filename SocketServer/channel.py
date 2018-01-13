import json
import logging

logger = logging.getLogger('WSServer')


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

    def send(self, data, log=True):
        if log:
            logger.info('%s Ответ %s  %s' % (self.name, data['type'], data['data']))
        for handler in self.handlers:
            handler.send(json.dumps(data))

    def send_pm(self, data, users):
        """
        Send private message
        :param data: data to send
        :param users: list or str
        :return: None
        """
        logger.info('%s Ответ пользователям %s: %s  %s' % (self.name, users, data['type'], data['data']))
        if type(users) == list:
            for handler in self.handlers:
                if handler.user in users:
                    handler.send(json.dumps(data))
        elif type(users) == str:
            for handler in self.handlers:
                if handler.user == users:
                    handler.send(json.dumps(data))
                    break

    def leave(self, handler):
        if handler.typing:
            self.send({'type': 'user_stop_typing', 'data': {'user': handler.user, 'user_id': handler.user_id}})
        if handler in self.handlers:
            self.handlers.remove(handler)
            self.send({
                'type': 'user_disconnected',
                'data': handler.get_information()
            })
        handler.channel = None
