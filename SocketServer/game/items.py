from .models import *
from .entities import *
import math


class Sword(Weapon):
    id = '50'
    damage_value = 10


class UltimateSword(Sword):
    id = '50:1'
    damage_value = 50


class PoisonSword(Sword):
    id = '50:2'
    damage_value = 20

    def damage(self, npc):
        super(PoisonSword, self).damage(npc)
        effect = PoisonEffect(npc)
        effect.ticks = 5


class HealingSword(Sword):
    id = '50:3'
    damage_value = -1
    action_delay = 5

    def damage(self, npc):
        super(HealingSword, self).damage(npc)
        effect = HealingEffect(npc)
        effect.ticks = 5

    def action(self, *_):
        super(HealingSword, self).action()
        self.owner.hp += 1


class FireStaff(Weapon):
    id = '51'
    damage_value = 5

    def action(self, angle):
        super().action()
        speed_y = FireBall.speed * math.cos(angle)
        speed_x = FireBall.speed * math.sin(angle)
        fireball = FireBall(self.world, self.owner)
        fireball.spawn(self.owner.x, self.owner.y, speed_x, speed_y)
