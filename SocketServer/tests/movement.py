import unittest
from main import DefaultCase, world


class MoveTest(DefaultCase):

    def setUp(self):
        self.assertTrue(world.auth)

    def test_move_down(self):
        """Move down"""
        self.assertIsInstance(world.data, dict)
        y = world.data['players'][self.user]['y']
        self.connection.action('down')
        self.connection.action('stop', 'horizontal')
        self.assertGreater(world.data['players'][self.user]['y'], y)

    def test_move_up(self):
        """Move up"""
        self.assertIsInstance(world.data, dict)
        y = world.data['players'][self.user]['y']
        self.connection.action('up')
        self.connection.action('stop', 'horizontal')
        self.assertLess(world.data['players'][self.user]['y'], y)

    def test_move_left(self):
        """Move left"""
        self.assertIsInstance(world.data, dict)
        x = world.data['players'][self.user]['x']
        self.connection.action('left')
        self.connection.action('stop', 'horizontal')
        self.assertLess(world.data['players'][self.user]['x'], x)

    def test_move_right(self):
        """Move right"""
        self.assertIsInstance(world.data, dict)
        x = world.data['players'][self.user]['x']
        self.connection.action('right')
        self.connection.action('stop', 'horizontal')
        self.assertGreater(world.data['players'][self.user]['x'], x)


if __name__ == '__main__':
    unittest.main()
