from .models import NPC
from pygame.math import Vector2


class EnemyNPC(NPC):
    id = '200'
    hp = 50

    damage_value = 5
    damage_delay = 30
    damage_radius = 35

    max_speed = 3

    def __init__(self, world):
        super(EnemyNPC, self).__init__(world)
        self.last_damage_tick = 0

    def hit(self):
        if self.world.tick - self.last_damage_tick < self.damage_delay:
            return
        for player in self.chunk.get_near('players'):
            if Vector2(abs(player.rect.centerx - self.rect.centerx),
                       abs(player.rect.centery - self.rect.centery)).as_polar()[0] < self.damage_radius:
                self.damage(player)
        self.last_damage_tick = self.world.tick

    def update(self):
        super(EnemyNPC, self).update()
        for player in self.chunk.get_near('players'):
            polar = Vector2(abs(player.rect.centerx - self.rect.centerx),
                            abs(player.rect.centery - self.rect.centery)).as_polar()
            if polar[0] <= self.vision_radius:
                self.speed.from_polar((self.max_speed, polar[1]))
                break
        else:
            self.speed.x, self.speed.y = 0, 0

        self.hit()

    def damage(self, npc):
        npc.hp -= self.damage_value
