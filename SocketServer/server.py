from twisted.internet.protocol import DatagramProtocol
from twisted.python import failure
from twisted.internet import error, task, reactor
from threading import Thread, Lock
import time
import json
import commands
from config import *
import logging
import traceback
from db import Db
import game.game

connectionDone = failure.Failure(error.ConnectionDone())

lock = Lock()
db = Db(lock)


class UDProtocol(DatagramProtocol):
    requests = ['connect', 'disconnect', 'ping']
    errors = {'001': 'Bad request', '002': 'Wrong request', '003': 'Connection first'}

    timeout = 5
    update = 1 / 2

    def __init__(self, ip, port, r, server):
        self.ip = ip
        self.port = port
        self.reactor = r
        self.server = server
        self.loop = task.LoopingCall(self.run)
        self.loop.start(self.update)

    def datagramReceived(self, datagram, address):
        if DEBUG and not datagram.count(b'ping'):
            self.server.logger.info("Datagram %s received from %s" % (repr(datagram), repr(address)))

        try:
            message = json.loads(datagram.decode('utf-8'))
            request = message.get('request')
            data = message.get('data')
            callback = message.get('callback')
            handler = self.server.connections.get(address)
        except (UnicodeDecodeError, json.decoder.JSONDecodeError):
            self.send(self.get_error_message('001'), address)
            return

        if not handler and request != 'connect':
            self.send(self.get_error_message('003'), address, callback)
            return

        if request:
            try:
                if request not in self.requests:
                    raise Exception('002')
                response = getattr(self, request)(data, address)
            except Exception as ex:
                response = self.get_error_message(ex.args[0])
        else:
            response = handler['user'].on_message(message)
        self.send(response, address, callback)

    def get_error_message(self, error_id):
        return {'type': 'error', 'data': {'code': error_id, 'message': self.errors[error_id]}}

    def send(self, data, address, callback=None):
        if not data:
            return
        if callback:
            data['callback'] = callback
        if type(address) == list:
            for addr in address:
                self.transport.write(json.dumps(data).encode('utf-8'), addr)
            return
        self.transport.write(json.dumps(data).encode('utf-8'), address)

    def connect(self, _, address):
        if self.server.connections.get(address):
            self.disconnect(None, address)
        user = User(address, self, self.server.main_game, self.server.secret_key)
        user.on_open()
        self.server.connections[address] = {'time': time.time(), 'user': user}

    def disconnect(self, _, address):
        if not self.server.connections.get(address):
            return
        handler = self.server.connections.pop(address)
        handler['user'].on_close()

    def ping(self, _, address):
        if not self.server.connections.get(address):
            raise Exception('003')
        self.server.connections[address]['time'] = time.time()

    def run(self):
        t = time.time()
        for handler in self.server.connections.copy().values():
            if t - handler['time'] > self.timeout:
                self.disconnect(None, handler['user'].addr)


class User:
    secret_key = ''

    def __init__(self, addr, udp, main_game, secret_key):
        self.udp = udp
        self.secret_key = secret_key
        self.temp = db
        self.name = None
        self.id = None
        self.channel = self.temp.main_channel
        self.rights = 0
        self.addr = addr
        self.logger = logging.getLogger('Server')
        self.player_info = {}
        self.game = main_game
        self.me = None

    def get_information(self):
        return {
            'user': self.name,
            'user_id': self.id,
            'user_rights': self.rights,
            'player_info': self.player_info,
        }

    def on_open(self):
        self.temp.handlers.append(self)
        self.logger.info('%s Connection' % repr(self.addr))
        self.send({
            'type': 'welcome',
            'data': {
                'message': 'udp server WELCOME!',
                'version': VERSION
            }
        })

    def on_message(self, message):
        if message.get('type'):
            message_type = message['type']
            message_type = message_type.replace('__', '')
            message_type = message_type.lower()
            data = message.get('data')
            try:
                resp = getattr(commands, message_type)(self, data)
            except Exception as ex:
                resp = {'type': message_type + '_error', 'data': str(ex)}
                self.logger.error('%s Error %s %s %s' % (self.addr, message_type, data, str(ex)))
                if DEBUG:
                    traceback.print_exc()
        elif message.get('action'):
            action = message['action']
            action = action.replace('__', '')
            action = action.lower()
            data = message.get('data')
            try:
                resp = self.me.action(action, data)
            except Exception as ex:
                resp = {'type': action + '_error', 'data': str(ex)}
                self.logger.error('%s Error %s %s %s' % (self.addr, action, data, str(ex)))
                if DEBUG:
                    traceback.print_exc()
        else:
            resp = commands.error(None)
        if message.get('id'):
            resp['id'] = message['id']
        if resp:
            self.send(resp)

    def on_close(self):
        commands.leave(self, None)
        if self.channel:
            self.channel.leave(self)
        self.temp.handlers.remove(self)
        self.logger.info('%s Disconnect' % (self.addr,))

    def send(self, data):
        self.udp.send(data, self.addr)


class Server:
    secret_key = 'shouldintermittentvengeancearmagainhisredrighthandtoplagueus'

    def __init__(self, ip='0.0.0.0', port=8956):

        form = '[%(asctime)s]  %(levelname)s: %(message)s'
        self.logger = logging.getLogger("Server")
        logging.basicConfig(level=logging.INFO, format=form)
        log_handler = logging.FileHandler('logs/log.txt')
        log_handler.setFormatter(logging.Formatter(form))
        self.logger.addHandler(log_handler)

        self.main_game = game.game.Game(db.main_channel)

        self.ip = ip
        self.port = port

        self.connections = {}

        self.reactor = reactor
        self.udp = UDProtocol(ip, port, reactor, self)
        reactor.listenUDP(port, self.udp)

    def run(self):
        self.logger.info('Start %s:%s' % (IP, PORT))
        self.main_game.start()
        Console()
        self.reactor.run()


class Console(Thread):
    def __init__(self):
        super().__init__(target=self.run)
        self.start()

    def run(self):
        while True:
            try:
                out = eval(input())
                if out is not None:
                    print(out)
            except KeyboardInterrupt:
                exit()
            except:
                traceback.print_exc()


if __name__ == '__main__':
    s = Server()
    s.run()
