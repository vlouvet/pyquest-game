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
        # Use correct attribute names from the User model: max_hp and username
        max_hp = getattr(player_char, "max_hp", None)
        if not isinstance(max_hp, int) or max_hp <= 0:
            # Fallback to a small default to avoid errors
            max_hp = 10

        if self.level == 1:
            attack_max = max(1, int(max_hp / 5))
        elif 1 < self.level < 5:
            attack_max = max(1, int(max_hp / 2))
        else:
            attack_max = max(1, max_hp)

        attack_damage = random.randint(1, attack_max)
        player_name = getattr(player_char, "username", "player")
        print(f"{self.name} attacks {player_name} for {attack_damage} hitpoints!")
        # Defensive update of hitpoints attribute
        current_hp = getattr(player_char, "hitpoints", None)
        if current_hp is None:
            # If player doesn't have hitpoints attr, set one
            setattr(player_char, "hitpoints", 0)
            current_hp = 0
        player_char.hitpoints = max(0, current_hp - attack_damage)
        print(f"{player_name}'s Hitpoints: {player_char.hitpoints}")

    def choose_type(self):
        animal_ascii = {}
        animal_ascii["elephant"] = "elephant"

        animal_ascii["giraffe"] = "giraffe"

        animal_ascii["Gryffon"] = "gryffon"

        animal_ascii["Dragon"] = "dragon"

        return random.choice(list(animal_ascii.values()))
