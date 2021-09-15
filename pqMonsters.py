import random

class npcMonster:
    def __init__(self, level=1):
        self.name = self.chooseType()
        self.race = "none"
        self.strength = 1
        self.intelligence = 1
        self.hitpoints = 2
        self.stealth = 1
        self.level = 1

    def doAttack(self, pc):
        if self.level == 1:
            attack_max = int(pc.maxhp / 5)
        elif self.level > 1 and self.level < 5:
            attack_max = int(pc.maxhp / 2)
        else:
            attack_max = pc.maxhp
        attackDamage = random.randint(1, attack_max)
        print(f"{self.name} attacks {pc.name} for {attackDamage} for hitpoints!")
        pc.hitpoints = pc.hitpoints - attackDamage
        print(f"{pc.name}'s Hitpoints: {pc.hitpoints}")

    def chooseType(self):
        animalAscii = {}
        animalAscii['elephant'] = "elephant"
        
        animalAscii['giraffe'] = "giraffe"
        
        animalAscii['Gryffon'] = "gryffon"

        animalAscii['Dragon'] = "dragon"

        return random.choice(list(animalAscii.values()))