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
        self.field.add_effect(PoisonEffect(npc, 5))


class HealingSword(Sword):
    id = '50:3'
    damage_value = -1
    action_delay = 5

    def damage(self, npc):
        super(HealingSword, self).damage(npc)
        self.field.add_effect(HealingEffect(npc, 5))

    def action(self, player, *_):
        super(HealingSword, self).action(player)
        player.hp += 1


class FireStaff(Weapon):
    id = '51'
    damage_value = 5

    def action(self, player, angle):
        super(FireStaff, self).action(player)
        speed_y = FireBall.speed * math.cos(angle)
        speed_x = FireBall.speed * math.sin(angle)
        self.field.spawn_entity(FireBall(self.rect, self.field, self.owner),
                                player.rect.x, player.rect.y, speed_x, speed_y)
