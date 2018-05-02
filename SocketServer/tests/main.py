import unittest
from row_client import Connection


class TestWorld:
    data = []

    auth = False

    def handler(self, data):
        if data['type'] == 'tick':
            self.data = data['data']
        elif data['type'] == 'auth_ok':
            self.auth = True


world = TestWorld()


class DefaultCase(unittest.TestCase):
    connection = Connection(handler=world.handler)
    user = 'admin'
    password = '1234'

    @classmethod
    def setUpClass(cls):
        cls.connection.send({'type': 'auth', 'data': {'user': cls.user, 'password': cls.password}})

    @classmethod
    def tearDownClass(cls):
        cls.connection.disconnect()
