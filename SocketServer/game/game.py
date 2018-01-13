from game.config import *
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
    def __init__(self, x, y, hp, inventory, active_item, field, user):
        super(Player, self).__init__(Rect(x, y, PLAYER_WIDTH, PLAYER_HEIGHT), field, hp)
        self.name = user.user
        self.id = user.user_id
        self.user = user
        self.inventory = inventory
        self.active_item = active_item

        self.speed_x = self.speed_y = 0

    def kill(self):
        self.field.channel.send_pm({'type': 'dead', 'data': 'You dead.'}, self.name)
        self.rect.x = random.randint(0, self.field.width)
        self.rect.y = random.randint(0, self.field.height)
        self.hp = 100
        for item in self.inventory.copy():
            self.drop_item(item)
        self.drop_item(self.active_item)

    def action(self, act, data):
        if act == 'left':
            self.speed_x = -PLAYER_SPEED
        elif act == 'right':
            self.speed_x = PLAYER_SPEED
        elif act == 'up':
            self.speed_y = -PLAYER_SPEED
        elif act == 'down':
            self.speed_y = PLAYER_SPEED
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
        super(Player, self).drop_item(item)
        self.inventory.remove(item)

    def get_item(self, item):
        if type(item) == str:
            item = self.canon_id(item)
            for entity in self.field.entities:
                if entity.id == item:
                    break
            else:
                return
            self.get_item(entity)
            return
        item.owner = self
        self.inventory.append(item)
        self.field.entities.remove(item)
        item.dropped = False
        item.rect.x = -1
        item.rect.y = -1

    def update(self):
        super(Player, self).update()
        self.speed_x = 0
        self.speed_y = 0


class Field:
    type = 'field'

    def __init__(self, channel):
        self.objects = []
        self.channel = channel

        self.players = []
        self.npc = []
        self.entities = []

        self.tick = 0

        self.width, self.height = FIELD_WIDTH, FIELD_HEIGHT
        self.rect = Rect(0, 0, self.width, self.height)

    def do_tick(self):
        for player in self.players:
            player.update()
        for npc in self.npc:
            npc.update()
        for entity in self.entities:
            entity.update()
        self.tick += 1

    def add_player(self, x, y, hp, inventory, active_item, user):
        player = Player(x, y, hp, inventory, active_item, self, user)
        for i in range(len(player.inventory)):
            player.inventory[i] = player.inventory[i](self, player)
        if active_item:
            player.active_item = player.active_item(self, player)
        self.players.append(player)
        return player

    def spawn_entity(self, entity, x, y, speed_x, speed_y):
        entity.rect.x = x
        entity.rect.y = y
        entity.speed_x = speed_x
        entity.speed_y = speed_y
        self.entities.append(entity)

    @staticmethod
    def add_effect(effect):
        npc = effect.npc
        for eff in npc.effects:
            if eff.id == effect.id:
                npc.effects.remove(eff)
        npc.effects.append(effect)

    @staticmethod
    def get_attr(obj, attr='id'):
        try:
            return getattr(obj, attr)
        except AttributeError:
            return False

    def get_object_by_id(self, item_id):
        if item_id is []:
            return []
        if type(item_id) == list:
            return [self.get_object_by_id(i) for i in item_id]
        all_objects = list(filter(lambda x: self.get_attr(x),
                                  map(lambda x: getattr(game.objects, x), dir(game.objects))))
        ids = list(map(lambda x: x.id, all_objects))
        return all_objects[ids.index(item_id)]


class Game(threading.Thread):
    def __init__(self, channel):
        threading.Thread.__init__(self, target=self.run)
        self.channel = channel
        self.field = Field(channel)

    def add_player(self, user):
        inventory = self.field.get_object_by_id(user.player_info['inventory'])
        try:
            active_item = inventory[user.player_info['active_item']]
        except IndexError:
            active_item = None
        return self.field.add_player(user.player_info['x'], user.player_info['y'],
                                     user.player_info['hp'], inventory,
                                     active_item, user)

    def delete_player(self, user):
        self.field.players.remove(user.me)
        self.channel.send({'type': 'player_left', 'data': ''})

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
            self.field.do_tick()
            data = {
                'players': [
                    {
                        'x': player.rect.x,
                        'y': player.rect.y,
                        'hp': player.hp,
                        'id': player.user.user_id,
                        'active_item': player.active_item.get_index(player.inventory)
                        if getattr(player, 'active_item', None) else 0,
                        'inventory': list(map(lambda x: x.id, player.inventory)),
                        'effects': [
                            {
                                'id': effect.id,
                                'ticks': effect.ticks
                            } for effect in player.effects
                        ]
                    } for player in self.field.players
                ],
                'objects': [
                    {
                        'x': obj.rect.x,
                        'y': obj.rect.y,
                        'id': obj.id
                    } for obj in self.field.objects
                ],
                'entities': [
                    {
                        'x': entity.rect.x,
                        'y': entity.rect.y,
                        'id': entity.id
                    } for entity in self.field.entities
                ],
                'npcs': [
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
                    } for npc in self.field.npc
                ]
            }
            self.channel.send({'type': 'tick', 'data': data})
            if TICK - time.time() + t > 0:
                time.sleep(TICK - time.time() + t)
