from .models import NPC
import math


class EnemyNPC(NPC):
    id = '200'
    hp = 50

    damage_value = 5
    damage_delay = 30
    damage_radius = 35

    speed = 3
    vision_radius = 100

    def __init__(self, rect, world):
        super(EnemyNPC, self).__init__(rect, world, self.hp)
        self.last_damage_tick = 0

    def hit(self):
        if self.world.tick - self.last_damage_tick < self.damage_delay:
            return
        for player in self.world.players:
            if (abs(player.rect.center[0] - self.rect.center[0]) < self.damage_radius) \
                    and (abs(player.rect.center[1] - self.rect.center[1]) < self.damage_radius):
                self.damage(player)
        self.last_damage_tick = self.world.tick

    def update(self):
        super(EnemyNPC, self).update()
        for player in self.world.players:
            if (abs(player.rect.center[0] - self.rect.center[0]) < self.vision_radius) \
                    and (abs(player.rect.center[1] - self.rect.center[1]) < self.vision_radius):
                angle = math.acos(
                    abs(self.rect.centery
                        - player.rect.centery)/(math.sqrt((self.rect.centerx - player.rect.centerx)**2
                                                + (self.rect.centery - player.rect.centery)**2))) * 180 / math.pi
                self.speed_y = self.speed * math.cos(angle)
                self.speed_x = self.speed * math.sin(angle)
                break
        else:
            self.speed_x, self.speed_y = 0, 0

        self.hit()

    def damage(self, npc):
        npc.hp -= self.damage_value
