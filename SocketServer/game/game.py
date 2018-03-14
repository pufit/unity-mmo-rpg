import game.items
import game.entities
import game.objects
import game.effects
import game.models
from numba import jit

import threading
import time
import pygame
from pygame import Rect
import random

import pickle  # I turned myself into a python library, Morty!
# TODO: save world


class Player(game.models.NPC):
    type = 'player'

    width = 40
    height = 60

    max_speed = 2
    max_items = 10
    render_radius = 2

    def __init__(self, world, user):
        super(Player, self).__init__(world)
        self.name = user.name
        self.id = user.id
        self.user = user
        self.inventory = []
        self.active_item = None  # TODO: Fists

        self.render_chunks = set()

        self.state = {}

    def kill(self):
        self.world.channel.send_pm({'type': 'dead', 'data': 'You dead.'}, self.name)  # TODO: send death data
        self.chunk.remove(self)
        self.hp = Player.hp
        for item in self.inventory.copy():
            item.drop()
        self.spawn(random.randint(100, self.world.width - 100), random.randint(100, self.world.height - 100))
        # TODO: respawn after request

    def action(self, act, data):
        if act == 'left':
            self.speed.x = -self.max_speed
        elif act == 'right':
            self.speed.x = self.max_speed
        elif act == 'up':
            self.speed.y = -self.max_speed
        elif act == 'down':
            self.speed.y = self.max_speed
        elif act == 'stop':
            if data == 'horizontal':
                self.speed.x = 0
            elif data == 'vertical':
                self.speed.y = 0
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

    def spawn(self, x, y, *args):
        super().spawn(x, y)
        self.render_chunks = self.chunk.get_near_chunks(self.render_radius)
        self.world.reload_active_chunks()

    def check_chunk(self):
        if super().check_chunk():
            self.render_chunks = self.chunk.get_near_chunks(self.render_radius)
            self.world.reload_active_chunks()


class Chunk:
    size = 20

    def __init__(self, x, y, world):
        self.x, self.y = x, y
        self.objects = []
        self.players = []
        self.npc = []
        self.entities = []
        self.world = world

    def update(self):
        for player in self.players:
            player.update()
        for npc in self.npc:
            npc.update()
        for entity in self.entities:
            entity.update()

    def remove(self, obj):
        self.get_group(obj.type).remove(obj)

    def add(self, obj):
        obj.chunk = self
        self.get_group(obj.type).append(obj)

    def get_group(self, t):
        """
        :type t: str
        :param t:  Type of object
        :return: list
        """
        if t == 'object':
            return self.objects
        if t == 'entity':
            return self.entities
        if t == 'npc':
            return self.npc
        if t == 'player':
            return self.players

    def get_near_chunks(self, r=2):
        """
        :return: set
        """
        chunks = set()
        for i in range(-r, r + 1):
            for j in range(-r, r + 1):
                if 0 <= self.x + i < len(self.world.chunks) and 0 <= self.y + j < len(self.world.chunks[0]):
                    chunks.add(self.world.chunks[self.x + i][self.y + j])
        return chunks

    def get_near(self, *args, r=1):
        objects = []
        for chunk in self.get_near_chunks(r):
            for arg in args:
                objects += getattr(chunk, arg)
        return objects


class World:
    type = 'world'

    width = 5000
    height = 5000

    def __init__(self, channel):
        self.channel = channel

        self.players = []

        self.active_chunks = set()
        self.chunks = [[Chunk(x, y, self) for y in range(self.width // Chunk.size // game.models.Block.size)]
                       for x in range(self.height // Chunk.size // game.models.Block.size)]

        self.tick = 0

        self.rect = Rect(0, 0, self.width, self.height)

        self.all_objects = list(filter(lambda x: self.get_attr(x),
                                       map(lambda x: getattr(game.objects, x), dir(game.objects))))

    def reload_active_chunks(self):
        self.active_chunks = set()
        for player in self.players:
            self.active_chunks |= player.render_chunks

    def do_tick(self):
        for chunk in self.active_chunks:
            chunk.update()
        self.tick += 1

    def add_player(self, x, y, hp, inventory, active_item, user):
        player = Player(self, user)
        player.hp = hp
        player.inventory = inventory
        for i, item in enumerate(player.inventory):
            _item = item(self, player)
            player.inventory[i] = _item
            if i == active_item:
                player.active_item = _item
        self.players.append(player)
        player.spawn(x, y)
        return player

    @staticmethod
    def get_attr(obj, attr='id'):
        try:
            return getattr(obj, attr)
        except AttributeError:
            return False

    @staticmethod
    def get_visible_objects(objects):
        return [obj for obj in objects if obj.visible]

    def get_object_by_id(self, item_id):
        if item_id is []:
            return []
        if type(item_id) == list:
            return [self.get_object_by_id(i) for i in item_id]
        ids = [obj.id for obj in self.all_objects]
        return self.all_objects[ids.index(item_id)]

    def get_chunk_by_coord(self, x, y):
        return self.chunks[x // (game.models.Block.size * Chunk.size)][y // (game.models.Block.size * Chunk.size)]


class Game(threading.Thread):
    tps = 30

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
        user.me.chunk.remove(user.me)
        self.world.players.remove(user.me)
        self.world.reload_active_chunks()
        self.channel.send({'type': 'player_left', 'data': ''})  # TODO: send data

    @staticmethod
    def get_img(name):
        s = pygame.image.load('game/src/img/' + name)
        return {
            'name': name,
            'src': str(pygame.image.tostring(s, 'RGBA')),
            'size': s.get_size()
        }

    @staticmethod
    @jit
    def get_diff(first_state, second_state):
        # TODO: diff algo
        pass

    def run(self):
        while True:
            t = time.time()
            self.world.do_tick()
            for player in self.world.players:
                entities = []
                npc = []
                players = []
                for chunk in player.chunk.get_near_chunks(Player.render_radius):
                    entities += chunk.entities
                    npc += chunk.npc
                    players += chunk.players
                data = {
                    'players': [
                        {
                            'x': player.rect.x,
                            'y': player.rect.y,
                            'hp': player.hp,
                            'id': player.user.id,
                            'name': player.user.name,
                            'active_item': player.inventory.index(player.active_item)
                            if (getattr(player, 'active_item', None) in player.inventory) else -1,
                            'inventory': [item.id for item in player.inventory],
                            'effects': [
                                {
                                    'id': effect.id,
                                    'ticks': effect.ticks
                                } for effect in player.effects
                            ]
                        } for player in self.world.get_visible_objects(players)
                    ],
                    'entities': [
                        {
                            'x': entity.rect.x,
                            'y': entity.rect.y,
                            'id': entity.id
                        } for entity in self.world.get_visible_objects(entities)
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
                        } for npc in self.world.get_visible_objects(npc)
                    ]
                }
                self.channel.send_pm({'type': 'tick', 'data': data}, player.name)
            if 1 / self.tps - time.time() + t > 0:
                time.sleep(1 / self.tps - time.time() + t)
            else:
                print(self.tps + 1 / self.tps - time.time() + t)
