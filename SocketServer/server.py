from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory, \
    listenWS

from autobahn.websocket.compress import PerMessageDeflateOffer, \
    PerMessageDeflateOfferAccept

import json
import commands
from config import *
import logging
import threading
import traceback
import gzip
from db import Db
import game.game

lock = threading.Lock()
db = Db(lock)


class Handler(WebSocketServerProtocol):
    def __init__(self):
        WebSocketServerProtocol.__init__(self)
        self.secret_key = ''
        self.temp = db
        self.user = None
        self.user_id = None
        self.game = None
        self.channel = self.temp.main_channel
        self.user_rights = 0
        self.addr = None
        self.typing = False
        self.logger = logging.getLogger('WSServer')
        self.player_info = {}
        self.game = main_game
        self.me = None

    def ws_send(self, message):
        if GZIP:
            data = gzip.compress(message.encode('utf-8'))
            self.sendMessage(data, isBinary=True)
        else:
            data = message.encode('utf-8')
            self.sendMessage(data)

    def get_information(self):
        return {
            'user': self.user,
            'user_id': self.user_id,
            'user_rights': self.user_rights,
            'player_info': self.player_info,
        }

    def onConnect(self, request):
        self.temp.handlers.append(self)
        self.addr = request.peer[4:]
        self.logger.info('%s Connection' % self.addr)

    def onOpen(self):
        self.ws_send(json.dumps({
            'type': 'welcome',
            'data': {
                'message': 'online-games websocket server WELCOME!',
                'version': VERSION
            }
        }))
        self.channel.join(self)

    def onMessage(self, payload, is_binary):
        try:
            if GZIP:
                message = json.loads(gzip.decompress(payload).decode('utf-8'))
            else:
                message = json.loads(payload).decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            message = commands.error(self, None)
        if message.get('type') and not (message.get('data') is None):
            message_type = message['type']
            message_type = message_type.replace('__', '')
            message_type = message_type.lower()
            data = message.get('data')
            try:
                resp = getattr(commands, message_type)(self, data)
            except Exception as ex:
                resp = {'type': message_type + '_error', 'data': str(ex)}
                self.logger.error('%s Error %s %s %s' % (self.addr, message_type, data, str(ex)))
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
                traceback.print_exc()
        else:
            resp = commands.error(None)
        if message.get('id'):
            resp['id'] = message['id']
        if resp:
            self.ws_send(json.dumps(resp))

    def onClose(self, *args):
        commands.leave(self, None)
        if self.channel:
            self.channel.leave(self)
        self.temp.handlers.remove(self)
        self.logger.info('%s Disconnect' % (self.addr,))


def run(secret_key):
    form = '[%(asctime)s]  %(levelname)s: %(message)s'
    logger = logging.getLogger("WSServer")
    logging.basicConfig(level=logging.INFO, format=form)
    log_handler = logging.FileHandler('logs/log.txt')
    log_handler.setFormatter(logging.Formatter(form))
    logger.addHandler(log_handler)
    logger.info('Start %s:%s' % (IP, PORT))

    factory = WebSocketServerFactory(u"ws://%s:%s" % (IP, PORT))
    Handler.secret_key = secret_key
    factory.protocol = Handler

    def accept(offers):
        for offer in offers:
            if isinstance(offer, PerMessageDeflateOffer):
                return PerMessageDeflateOfferAccept(offer)

    factory.setProtocolOptions(perMessageCompressionAccept=accept)
    listenWS(factory)


if __name__ == '__main__':
    sk = 'shouldintermittentvengeancearmagainhisredrighthandtoplagueus'
    main_game = game.game.Game(db.main_channel)
    main_game.start()
    run(sk)
    while True:
        try:
            out = eval(input())
            if out is not None:
                print(out)
        except KeyboardInterrupt:
            exit()
        except:
            traceback.print_exc()
