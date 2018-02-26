from .models import Entity
from .effects import *


class Ball(Entity):
    id = '150'
    speed = 5
    damage_value = 20
    effect = None

    def __init__(self, world, owner):
        super(Ball, self).__init__(world)

        self.owner = owner

    def collide_action(self, lst):
        if len(lst) == 0:
            return
        target = lst[0]
        if (target.type == 'npc') and (target != self.owner):
            target.hp -= self.damage_value
            if self.effect:
                self.world.add_effect(self.effect(target, 5))


class FireBall(Ball):
    id = '150:1'
    effect = FireEffect

    def __init__(self, world, owner):
        super(FireBall, self).__init__(world, owner)
