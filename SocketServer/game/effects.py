from .models import Effect
from .config import *


class PoisonEffect(Effect):
    id = '100'
    damage_value = 1

    def __init__(self, npc, ticks, delay=EFFECT_DELAY):
        super(PoisonEffect, self).__init__(npc, ticks, delay)

    def action(self):
        self.npc.hp -= self.damage_value


class ExtraPoisonEffect(PoisonEffect):
    id = '100:1'
    damage_value = 5


class HealingEffect(Effect):
    id = '101'
    healing_value = 1

    def __init__(self, npc, ticks, delay=EFFECT_DELAY):
        super(HealingEffect, self).__init__(npc, ticks, delay)

    def action(self):
        self.npc.hp += self.healing_value


class FireEffect(ExtraPoisonEffect):
    id = '102'
