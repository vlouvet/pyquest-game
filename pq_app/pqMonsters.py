import random

class NPCMonster:
    def __init__(self):
        self.name = self.choose_type()
        self.race = "none"
        self.strength = 1
        self.intelligence = 1
        self.hitpoints = 2
        self.stealth = 1
        self.level = 1

    def do_attack(self, player_char):
        if self.level == 1:
            attack_max = int(player_char.maxhp / 5)
        elif self.level > 1 and self.level < 5:
            attack_max = int(player_char.maxhp / 2)
        else:
            attack_max = player_char.maxhp
        attack_damage = random.randint(1, attack_max)
        print(f"{self.name} attacks {player_char.name} for {attack_damage} for hitpoints!")
        player_char.hitpoints = player_char.hitpoints - attack_damage
        print(f"{player_char.name}'s Hitpoints: {player_char.hitpoints}")

    def choose_type(self):
        animal_ascii = {}
        animal_ascii['elephant'] = "elephant"

        animal_ascii['giraffe'] = "giraffe"

        animal_ascii['Gryffon'] = "gryffon"

        animal_ascii['Dragon'] = "dragon"

        return random.choice(list(animal_ascii.values()))
