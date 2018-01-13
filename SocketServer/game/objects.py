from .entities import *
from .entities import *
from .items import *
from pygame import Rect
from .models import *
import random
# Импорты не убирать!


class Stone(Object):
    id = '1'

    def __init__(self, field):
        width = 30
        height = 30

        super(Stone, self).__init__(field, Rect(random.randint(0, field.width),
                                                random.randint(0, field.height), width, height))


class Grass(Stone):
    id = '2'


class Brick(Stone):
    id = '3'
