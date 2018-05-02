import time
import json
from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread


class Pinger(Thread):
    def __init__(self, connection):
        self.connection = connection

        super().__init__(target=self.run)

    def run(self):
        while True:
            self.connection.send({"request": "ping", "data": {}})
            time.sleep(2)


class Connection(Thread):
    def __init__(self, address=('localhost', 8956), handler=None):
        self.address = address
        self.socket = socket(AF_INET, SOCK_DGRAM)

        self.handler = handler

        self.send({"request": "connect"})

        self.pinger = Pinger(self)
        self.pinger.start()

        super().__init__(target=self.run)
        if self.handler:
            self.start()

    def send(self, data):
        self.socket.sendto(json.dumps(data).encode('utf-8'), self.address)
        time.sleep(0.3)

    def action(self, action, data=None):
        self.send({'action': action, 'data': data})

    def eval(self, command):
        self.send({'type': 'get_eval', 'data': command})
        while True:
            r = self.recv()
            print(r)
            if r['type'] == 'eval':
                return r['data']
            self.handler(r)

    def recv(self):
        return json.loads(self.socket.recvfrom(8024)[0].decode('utf-8'))

    def disconnect(self):
        self.send({"request": "disconnect"})

    def run(self):
        if not self.handler:
            raise NotImplementedError('handler must be function')
        while True:
            self.handler(self.recv())
