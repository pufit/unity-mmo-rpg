from .models import EnemyNPC


class Zombie(EnemyNPC):
    id = '200'

    loot = {'53': [1/8, 10]}
