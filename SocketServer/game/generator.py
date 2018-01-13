import random


class Generator:
    def __init__(self, field):
        self.seed = random.randint(0, 100000000000000)
        self.field = field

        random.seed(self.seed)

    def generate_obj(self):
        self.field.objects.append(self.field.get_object_by_id(random.randint(1, 3))(self.field))
