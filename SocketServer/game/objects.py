from .entities import *
from .entities import *
from .items import *
from pygame import Rect
from .models import *
# Импорты не убирать!


class Stone(Object):
    id = '1'
    width = 30
    height = 30

    def __init__(self, field, x, y):

        super(Stone, self).__init__(field, Rect(x, y, self.width, self.height))


class Grass(Stone):
    id = '2'


class Brick(Stone):
    id = '3'
