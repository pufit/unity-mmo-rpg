import socket
import json
import asyncore
import commands
from config import *
from db import Db
import threading
import logging
import gzip
import traceback
import game.game


lock = threading.Lock()
db = Db(lock)


class Handler(asyncore.dispatcher_with_send):
    def __init__(self, sock):
        super(Handler, self).__init__(sock)
        self.temp = db
        self.user = None
        self.user_id = None
        self.game = None
        self.channel = self.temp.main_channel
        self.user_rights = 0
        self.addr = None
        self.typing = False
        self.logger = logger
        self.player_info = {}
        self.game = main_game
        self.me = None

    def handle_close(self):
        # commands.leave(self, None)
        self.logger.info('%s Disconnected' % (self.addr,))
        self.close()

    def get_information(self):
        return {
            'user': self.user,
            'user_id': self.user_id,
            'user_rights': self.user_rights,
            'player_info': self.player_info,
        }

    def handle_read(self):
        data = self.recv(BUFFERSIZE)
        if data == b'':
            return
        try:
            if GZIP:
                message = json.loads(gzip.decompress(data).decode('utf-8'))
            else:
                message = json.loads(data.decode('utf-8'))
        except:
            message = commands.error(self, None)
        if message.get('type') and not (message.get('data') is None):
            message_type = message['type']
            message_type = message_type.replace('__', '')
            message_type = message_type.lower()
            data = message.get('data')
            self.logger.req(self.addr, message_type, data)
            try:
                resp = getattr(commands, message_type)(self, data)
            except Exception as ex:
                resp = {'type': message_type + '_error', 'data': str(ex)}
                self.logger.log_error(self.addr, message_type, data, str(ex))
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
                self.logger.log_error(self.addr, action, data, str(ex))
                if DEBUG:
                    traceback.print_exc()
        else:
            resp = commands.error(None)
        if message.get('id'):
            resp['id'] = message['id']
        if resp:
            self.logger.resp(self.addr, resp['type'], resp['data'])
            self.send(json.dumps(resp))


class Server(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(SLOTS)
        print('Start %s:%s' % (IP, PORT))

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            return
        else:
            sock, addr = pair
            logger.info('%s Connection' % repr(addr))
            _ = Handler(sock)


class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args)
        self.start()


class Logger(logging.Logger):
    def __init__(self, debug=True):
        super(Logger, self).__init__('SocketServer')
        form = '[%(asctime)s]  %(levelname)s: %(message)s'
        logging.basicConfig(level=logging.INFO, format=form)
        log_handler = logging.FileHandler('logs/log.txt')
        log_handler.setFormatter(logging.Formatter(form))
        self.addHandler(log_handler)
        self.DEBUG = debug

    def resp(self, addr, message_type, data):
        if not self.DEBUG:
            return
        self.info('%s Response %s  %s' % (addr, message_type, data))

    def req(self, addr, message_type, data):
        if not self.DEBUG:
            return
        self.info('%s Request %s  %s' % (addr, message_type, data))

    def log_error(self, addr, message_type, data, ex):
        self.error('%s Error %s  %s  %s' % (addr, message_type, data, ex))


if __name__ == '__main__':
    logger = Logger(DEBUG)
    main_game = game.game.Game(db.main_channel)
    main_game.start()
    server = Server(IP, PORT)
    Thread(asyncore.loop())
    while True:
        try:
            out = eval(input())
            if out is not None:
                print(out)
        except KeyboardInterrupt:
            exit()
        except:
            traceback.print_exc()
