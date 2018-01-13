from .models import Entity
from .effects import *


class Ball(Entity):
    id = '150'
    speed = 5

    def __init__(self, rect, field, owner):
        super(Ball, self).__init__(rect, field)

        self.damage_value = 20
        self.effect = None
        self.owner = owner

    def collide_action(self, lst):
        if len(lst) == 0:
            return
        target = lst[0]
        if (target.type == 'npc') and (target != self.owner):
            target.hp -= self.damage_value
            if self.effect:
                self.field.add_effect(FireEffect(target, 5))


class FireBall(Ball):
    id = '150:1'

    def __init__(self, rect, field, owner):
        super(FireBall, self).__init__(rect, field, owner)
