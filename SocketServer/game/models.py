from pygame import Rect
from pygame.math import Vector2
import math
from random import uniform


class Object:
    id = '0'
    type = 'object'
    static = True
    visible = True
    collide = True

    width = 50
    height = 50

    x = 0
    y = 0

    def __init__(self, world, x=0, y=0):
        self.rect = Rect(x, y, self.width, self.height)
        self.world = world

        self.direction = 0
        self.speed = Vector2(0, 0)
        self.chunk = self.world.get_chunk_by_coord(x, y)

    @staticmethod
    def canon_id(i):
        if type(i) == int:
            return str(i)
        if i.count(':') != -1:
            main_id, sub_id = i.split(':')
            if sub_id == 0:
                return main_id
        return i

    def spawn(self, x, y):
        self.rect.center = x, y
        self.world.get_chunk_by_coord(x, y).add(self)


class Block(Object):
    type = 'block'
    size = 50


class Entity(Object):
    type = 'entity'
    static = False
    collide = False
    touchable = True

    def update(self):
        if not self.speed:
            return

        self.move(self.speed)

    def check_collide(self, rect):
        objects = self.chunk.get_near('objects', 'players', 'npc', 'entities')
        objects.remove(self)
        if self.world.rect.contains(rect) \
                and ((rect.collidelist((list(map(lambda x: x.rect,
                                                 filter(lambda x: x.collide, objects)))))) or not self.collide):
            return False
        return True

    def move(self, speed):
        """
        Change current coordinates with collision
        """
        move_x = self.rect.move(speed.x, 0)
        if not self.check_collide(move_x):
            self.rect = move_x

        move_y = self.rect.move(0, speed.y)
        if not self.check_collide(move_y):
            self.rect = move_y

        self.check_chunk()

        if self.touchable:
            objects = self.chunk.objects + self.chunk.players + self.chunk.npc + self.chunk.entities
            objects.remove(self)
            self.collide_action([objects[i] for i in self.rect.collidelistall(list(map(lambda r: r.rect,
                                                                                       filter(lambda r: r.collide,
                                                                                              objects))))])

    def tp(self, x, y):
        """
        Change current coordinates
        :param x: int
        :param y: int
        :return: None
        """
        self.rect.center = x, y
        self.check_chunk()

    def check_chunk(self):
        chunk = self.world.get_chunk_by_coord(self.rect.centerx, self.rect.centery)
        if chunk != self.chunk:
            self.chunk.remove(self)
            chunk.add(self)
            return True

    def collide_action(self, *_):
        pass


class TempEntity(Entity):
    ttl = 10

    def update(self):
        super().update()
        self.ttl -= 1
        if self.ttl <= 0:
            self.chunk.remove(self)


class Item(Entity):
    type = 'item'

    stackable = True  # TODO: check name

    def __init__(self, world, owner):
        super(Item, self).__init__(world)
        self.dropped = False
        self.name = None

        self.owner = owner
        self.stack = None

        self.action_delay = 15
        self.last_action_tick = 0

    def action(self, *args):
        if self.world.tick - self.last_action_tick < self.action_delay:
            return
        self.last_action_tick = self.world.tick

    def stop_action(self, *args):
        pass

    def collide_action(self, players):
        if not self.dropped:
            return
        player = players[0]
        if len(player.inventory) <= player.max_items:
            player.get_item(self)


class Stack:

    max_count = 99

    def __init__(self, item, count=1):
        self.item = item
        self.count = count

    def add(self, n=1):
        if self.count + n > self.max_count:
            raise OverflowError()
        self.count += n


class Weapon(Item):
    width = 10
    height = 15

    stackable = False

    damage_value = 0
    damage_radius = 70
    damage_delay = 15

    def __init__(self, world, owner):

        super(Weapon, self).__init__(world, owner)
        self.last_damage_tick = 0

    def hit(self):
        if self.world.tick - self.last_damage_tick < self.damage_delay:
            return
        self.last_damage_tick = self.world.tick
        npcs = self.owner.chunk.get_near('npc', 'players')
        npcs.remove(self.owner)
        for npc in npcs:
            if Vector2(abs(npc.rect.centerx - self.owner.rect.centerx),
                       abs(npc.rect.centery - self.owner.rect.centery)).as_polar()[0] < self.damage_radius:
                self.damage(npc)

    def damage(self, npc):
        npc.hp -= self.damage_value

    def drop(self):
        self.dropped = True
        if self.owner.rect.y <= 70:
            x, y = self.owner.rect.x, self.owner.rect.y - 50
        else:
            x, y = self.owner.rect.x, self.owner.rect.y + 70
        self.spawn(x, y)


class Potion(Item):
    drink_delay = 30

    def __init__(self, world, owner):
        super().__init__(world, owner)
        self.is_drinking = False
        self.drink_tick = 0

    def update(self):
        super().update()
        if self.is_drinking:
            self.drink_tick += 1

        if self.drink_tick >= self.drink_delay:
            self.drink_tick = 0
            self.drink_action()

    def drink_action(self, *args):
        pass

    def action(self, *_):
        self.is_drinking = True

    def stop_action(self, *_):
        self.is_drinking = False
        self.drink_tick = 0


class Effect:
    type = 'effect'
    id = '100'

    delay = 2
    ticks = 20

    def __init__(self, npc):
        self.npc = npc

        for eff in npc.effects:
            if eff.id == self.id:
                npc.effects.remove(eff)
        npc.effects.append(self)

    def update(self):
        if self.ticks == 0:
            self.npc.effects.remove(self)
            return
        if not self.ticks % self.delay:
            self.action()
        self.ticks -= 1

    def action(self):
        pass


class NPC(Entity):
    type = 'NPC'
    collide = True
    touchable = False
    vision_radius = 100
    hp = 100

    max_speed = 2

    def __init__(self, world):
        super(NPC, self).__init__(world)
        self.effects = []

    def update(self):
        super(NPC, self).update()
        for effect in self.effects:
            effect.update()
        if self.hp <= 0:
            self.kill()

    def kill(self):
        self.chunk.npc.remove(self)


class EnemyNPC(NPC):
    hp = 50

    damage_value = 5
    damage_delay = 30
    damage_radius = 3

    loot = {}  # id: [freq, count]

    max_speed = 3

    def __init__(self, world):
        super(EnemyNPC, self).__init__(world)
        self.last_damage_tick = 0

    def hit(self):
        if self.world.tick - self.last_damage_tick < self.damage_delay:
            return
        for player in self.chunk.get_near('players'):
            if Vector2(abs(player.rect.centerx - self.rect.centerx),
                       abs(player.rect.centery - self.rect.centery)).length() < self.damage_radius:
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

    def kill(self):
        for item_id, param in zip(self.loot, self.loot.values()):
            item = self.world.get_object_by_id(item_id)  # TODO: drop (need Stack structure)
        super().kill()


class Achievement:

    header = 'Zero Achievement'
    text = 'System class'

    def __init__(self, world):
        self.world = world

    def check(self):
        pass


def my_random(count, freq):
    return int(sigmoid(uniform(1/freq, 1) - 1) * 2 * count)


def sigmoid(z):
    """Sigmoid function"""
    if z > 100:
        return 0
    return 1.0 / (1.0 + math.exp(z))
