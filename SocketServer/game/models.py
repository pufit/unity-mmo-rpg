from pygame import Rect
from .config import *


class Object:
    id = '0'
    type = 'object'

    def __init__(self, rect, field):
        self.rect = rect
        self.field = field
        self.collide = True

        self.direction = 0
        self.speed_x, self.speed_y = 0, 0
        self.moving = False

    def update(self):
        if not (self.speed_x or self.speed_y):
            return

        self.moving = True

        move_x = self.rect.move(int(self.speed_x), 0)
        if not self.check_collide(move_x):
            self.rect = move_x

        move_y = self.rect.move(0, int(self.speed_y))
        if not self.check_collide(move_y):
            self.rect = move_y

    def check_collide(self, rect):
        objects = self.field.objects + self.field.players + self.field.npc + self.field.entities
        objects.remove(self)
        if self.field.rect.contains(rect) \
                and((rect.collidelist((list(map(lambda x: x.rect,
                                                filter(lambda x: x.collide, objects)))))) or not self.collide):
            return False
        return True

    @staticmethod
    def canon_id(i):
        if type(i) == int:
            return str(i)
        if i.count(':') != -1:
            main_id, sub_id = i.split(':')
            if sub_id == 0:
                return main_id
        return i


class Entity(Object):
    type = 'entity'

    def __init__(self, rect, field):
        super(Entity, self).__init__(rect, field)
        self.collide = False
        self.touchable = True

    def update(self):
        super(Entity, self).update()
        if self.touchable:
            objects = self.field.objects + self.field.players + self.field.npc + self.field.entities
            objects.remove(self)
            self.collide_action([objects[i] for i in self.rect.collidelistall(list(map(lambda x: x.rect,
                                                                                       filter(lambda x: x.collide,
                                                                                              objects))))])

    def collide_action(self, *_):
        pass


class Item(Entity):
    type = 'item'

    def __init__(self, rect, field, owner):
        super(Item, self).__init__(rect, field)
        self.dropped = False
        self.name = None

        self.owner = owner

        self.action_delay = 15
        self.last_action_tick = 0

    def action(self, player):
        if self.field.tick - self.last_action_tick < self.action_delay:
            return
        self.last_action_tick = self.field.tick

    def collide_action(self, players):
        if not self.dropped:
            return
        player = players[0]
        if len(player.inventory) <= MAX_ITEMS:
            player.get_item(self)

    def get_index(self, inventory):
        if self in inventory:
            return inventory.index(self)
        return 0


class Weapon(Item):
    def __init__(self, field, owner):
        self.width = 10
        self.height = 15

        super(Weapon, self).__init__(Rect(0, 0, self.width, self.height), field, owner)
        self.damage_value = 0
        self.damage_radius = 70

        self.damage_delay = 15
        self.last_damage_tick = 0

    def hit(self):
        if self.field.tick - self.last_damage_tick < self.damage_delay:
            return
        self.last_damage_tick = self.field.tick
        npcs = self.field.npc + self.field.players
        npcs.remove(self.owner)
        for npc in npcs:
            if (abs(npc.rect.center[0] - self.rect.center[0]) < self.damage_radius) \
                    and (abs(npc.rect.center[1] - self.rect.center[1]) < self.damage_radius):
                self.damage(npc)

    def damage(self, npc):
        npc.hp -= self.damage_value


class Effect:
    type = 'effect'

    def __init__(self, npc, ticks, delay):
        self.npc = npc
        self.ticks = ticks
        self.delay = delay

    def update(self):
        if self.ticks == 0:
            self.npc.effects.remove(self)
            return
        if not self.ticks % self.delay:
            self.action()
        self.ticks -= 1

    def action(self):
        pass


class NPC(Object):
    type = 'NPC'

    def __init__(self, rect, field, hp):
        super(NPC, self).__init__(rect, field)
        self.hp = hp
        self.effects = []

    def drop_item(self, item):
        if type(item) == list:
            for i in item:
                self.drop_item(i)
        else:
            item.dropped = True
            self.field.entities.append(item)
            if self.rect.y <= 70:
                item.rect.x, item.rect.y = self.rect.x, self.rect.y - 50
            else:
                item.rect.x, item.rect.y = self.rect.x, self.rect.y + 70

    def update(self):
        super(NPC, self).update()
        for effect in self.effects:
            effect.update()
        if self.hp <= 0:
            self.kill()

    def kill(self):
        self.field.npc.remove(self)
