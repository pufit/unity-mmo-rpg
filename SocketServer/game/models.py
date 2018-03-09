from pygame import Rect


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
        self.speed_x, self.speed_y = 0, 0
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


class Block(Object):
    type = 'block'
    size = 50


class Entity(Object):
    type = 'entity'
    static = False
    collide = False
    touchable = True

    def __init__(self, world):
        super(Entity, self).__init__(world)

    def update(self):
        if not (self.speed_x or self.speed_y):
            return

        self.move(int(self.speed_x), int(self.speed_y))

    def check_collide(self, rect):
        objects = self.chunk.get_near('objects', 'players', 'npc', 'entities')
        objects.remove(self)
        if self.world.rect.contains(rect) \
                and ((rect.collidelist((list(map(lambda x: x.rect,
                                                 filter(lambda x: x.collide, objects)))))) or not self.collide):
            return False
        return True

    def spawn(self, x, y, speed_x=0, speed_y=0):
        self.rect.center = x, y
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.world.get_chunk_by_coord(x, y).add(self)

    def move(self, x, y):
        """
        Change current coordinates with collision
        :param x: int
        :param y: int
        :return: None
        """
        move_x = self.rect.move(x, 0)
        if not self.check_collide(move_x):
            self.rect = move_x

        move_y = self.rect.move(0, y)
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


class Item(Entity):
    type = 'item'

    def __init__(self, world, owner):
        super(Item, self).__init__(world)
        self.dropped = False
        self.name = None

        self.owner = owner

        self.action_delay = 15
        self.last_action_tick = 0

    def action(self, *args):
        if self.world.tick - self.last_action_tick < self.action_delay:
            return
        self.last_action_tick = self.world.tick

    def collide_action(self, players):
        if not self.dropped:
            return
        player = players[0]
        if len(player.inventory) <= player.max_items:
            player.get_item(self)


class Weapon(Item):
    width = 10
    height = 15

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
            if (abs(npc.rect.center[0] - self.rect.center[0]) < self.damage_radius) \
                    and (abs(npc.rect.center[1] - self.rect.center[1]) < self.damage_radius):
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
