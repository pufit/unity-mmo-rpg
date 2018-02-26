import game.items
import game.entities
import game.objects
import game.effects
import game.models

import threading
import time
import pygame
from pygame import Rect
import random


class Player(game.models.NPC):
    width = 40
    height = 60
    speed = 2
    max_items = 10
    vision_radius = 1000

    def __init__(self, world, user):
        super(Player, self).__init__(world)
        self.name = user.name
        self.id = user.id
        self.user = user
        self.inventory = []
        self.active_item = None  # TODO: Fists

        self.speed_x = self.speed_y = 0

    def kill(self):
        self.world.channel.send_pm({'type': 'dead', 'data': 'You dead.'}, self.name)  # TODO: send death data
        self.rect.x = random.randint(0, self.world.width)
        self.rect.y = random.randint(0, self.world.height)
        self.hp = 100
        for item in self.inventory.copy():
            item.drop()

    def action(self, act, data):
        if act == 'left':
            self.speed_x = -self.speed
        elif act == 'right':
            self.speed_x = self.speed
        elif act == 'up':
            self.speed_y = -self.speed
        elif act == 'down':
            self.speed_y = self.speed
        elif act == 'stop':
            if data == 'horizontal':
                self.speed_x = 0
            elif data == 'vertical':
                self.speed_y = 0
            else:
                raise Exception("Wrong direction")
        elif act == 'hit':
            if self.active_item:
                self.active_item.hit()
        elif act == 'action':
            if not self.active_item:
                return
            if data is not None:
                self.active_item.action(self, data)
            else:
                self.active_item.action(self)
        elif act == 'active_item_change':
            try:
                self.active_item = self.inventory[data]
            except IndexError:
                self.active_item = None
        elif act == 'drop':
            if not self.active_item:
                return
            self.drop_item(self.active_item)
            self.active_item = None

    def drop_item(self, item):
        """
        :param item: id or class
        :return: None
        """
        if type(item) == str:
            item = self.canon_id(item)
            for i in self.inventory:
                if i.id == item:
                    break
            else:
                return
            self.drop_item(i)
            return
        item.drop()
        self.inventory.remove(item)

    def get_item(self, item):
        item.owner = self
        self.inventory.append(item)
        item.chunk.entities.remove(item)
        item.dropped = False

    def update(self):
        super(Player, self).update()


class Chunk:
    size = 20

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.objects = []
        self.players = []
        self.npc = []
        self.entities = []

    def update(self):
        for player in self.players:
            player.update()
        for npc in self.npc:
            npc.update()
        for entity in self.entities:
            entity.update()


class World:
    type = 'world'

    width = 5000
    height = 5000

    def __init__(self, channel):
        self.channel = channel

        self.active_chunks = []
        self.chunks = []

        self.tick = 0

        self.rect = Rect(0, 0, self.width, self.height)

        self.all_objects = list(filter(lambda x: self.get_attr(x),
                                       map(lambda x: getattr(game.objects, x), dir(game.objects))))

    def do_tick(self):
        for chunk in self.active_chunks:
            chunk.update()
        self.tick += 1

    def add_player(self, x, y, hp, inventory, active_item, user):
        player = Player(self, user)
        player.hp = hp
        player.inventory = inventory
        for i in range(len(player.inventory)):
            player.inventory[i] = player.inventory[i](self, player)
        if active_item:
            player.active_item = player.active_item(self, player)
        player.spawn(x, y)
        return player

    @staticmethod
    def get_attr(obj, attr='id'):
        try:
            return getattr(obj, attr)
        except AttributeError:
            return False

    @staticmethod
    def get_visible_objects(vision_radius, objects):
        return [objects[i] for i in vision_radius.collidelistall(
            list(map(lambda x: x.rect, filter(lambda x: x.visible, objects))))]

    def get_object_by_id(self, item_id):
        if item_id is []:
            return []
        if type(item_id) == list:
            return [self.get_object_by_id(i) for i in item_id]
        ids = list(map(lambda x: x.id, self.all_objects))
        return self.all_objects[ids.index(item_id)]

    def get_chunk_by_cords(self, x, y):
        pass


class Game(threading.Thread):
    tick = 1 / 30

    def __init__(self, channel):
        threading.Thread.__init__(self, target=self.run)
        self.channel = channel
        self.world = World(channel)

    def add_player(self, user):
        inventory = self.world.get_object_by_id(user.player_info['inventory'])
        try:
            active_item = inventory[user.player_info['active_item']]
        except IndexError:
            active_item = 0
        return self.world.add_player(user.player_info['x'], user.player_info['y'],
                                     user.player_info['hp'], inventory,
                                     active_item, user)

    def delete_player(self, user):
        user.me.chunk.players.remove(user.me)
        self.channel.send({'type': 'player_left', 'data': ''})  # TODO: send data

    @staticmethod
    def get_img(name):
        s = pygame.image.load('game/src/img/' + name)
        return {
            'name': name,
            'src': str(pygame.image.tostring(s, 'RGBA')),
            'size': s.get_size()
        }

    def run(self):
        while True:
            t = time.time()
            self.world.do_tick()
            for player in self.world.players:
                vision_rect = pygame.rect.Rect(player.rect.centerx - player.vision_radius // 2,
                                               player.rect.centery - player.vision_radius // 2,
                                               player.vision_radius, player.vision_radius)
                data = {
                    'players': [
                        {
                            'x': player.rect.x,
                            'y': player.rect.y,
                            'hp': player.hp,
                            'id': player.user.id,
                            'name': player.user.name,
                            'active_item': player.active_item.get_index(player.inventory)
                            if getattr(player, 'active_item', None) else 0,
                            'inventory': list(map(lambda x: x.id, player.inventory)),
                            'effects': [
                                {
                                    'id': effect.id,
                                    'ticks': effect.ticks
                                } for effect in player.effects
                            ]
                        } for player in self.world.get_visible_objects(vision_rect, self.world.players)
                    ],
                    'entities': [
                        {
                            'x': entity.rect.x,
                            'y': entity.rect.y,
                            'id': entity.id
                        } for entity in self.world.get_visible_objects(vision_rect, self.world.entities)
                    ],
                    'npc': [
                        {
                            'x': npc.rect.x,
                            'y': npc.rect.y,
                            'hp': npc.hp,
                            'effects': [
                                {
                                    'id': effect.id,
                                    'ticks': effect.ticks
                                } for effect in npc.effects
                            ]
                        } for npc in self.world.get_visible_objects(vision_rect, self.world.npc)
                    ]
                }
                self.channel.send_pm({'type': 'tick', 'data': data}, player.name)
            if self.tick - time.time() + t > 0:
                time.sleep(self.tick - time.time() + t)
            else:
                print(self.tick - time.time() + t)
