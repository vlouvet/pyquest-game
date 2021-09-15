import random

class playerCharacter:
    def __init__(self, name):
        self.name = "player1"
        self.race = "none"
        self.chrClass = "none"
        self.strength = 10
        self.intelligence = 10
        self.hitpoints = 100
        self.maxhp = 100
        self.expPoints = 1
        self.maxExp = 100
        self.stealth = 10
        self.chrLevel = 1
        self.nextLevelExp = self.chrLevel * 100

    def setName(self):
        userInput = input("Please enter your character's name:")
        if userInput != "exit":
            self.name = userInput
        else:
            print("Exit requested")
            exit()

    def setClass(self, request_data):
        # userInput = input("what is your class?\n[wiz,pldn,warr]\n")
        # if userInput == "exit":
        #     exit()
        # elif userInput not in ["wiz", "pldn", "warr"]:
        #     print("that is not a valid class, Try again!")
        #     self.getClass()
        # else:
        #     self.chrClass = userInput
        self.chrClass = request_data['pc']['chrClass']
        return self.chrClass

    def setRace(self, request_data):
        # userInput = input("what is your race?\n[elf,hbt,kjt]\n")
        # if userInput not in ["elf", "hbt", "kjt"]:
        #     print("that is not a valid class, Try again!")
        #     self.getRace()
        # else:
        print(type(request_data))
        self.race = request_data['pc']['race']
        return self.race

    def setStats(self):
        # start by setting all stats to default values
        self.strength = 10
        self.intelligence = 10
        self.maxhp = 100
        self.stealth = 10
        self.expPoints = 1
        # elves are weak, smart, and stealth
        if self.race == "elf":
            self.strength -= 5
            self.intelligence += 5
            self.stealth += 5
            self.maxhp = 80
        # Hobbits are midly strong, midly smart, but stealthy
        elif self.race == "hbt":
            self.strength += 2
            self.intelligence -= 1
            self.stealth += 5
            self.maxhp = 100
        # Kajit are strong, dumb, but stealthy
        elif self.race == "kjt":
            self.strength += 5
            self.intelligence -= 5
            self.stealth += 5
            self.maxhp = 120
        # wizards are smart, but gain no strength or stealth bonus
        if self.chrClass == "wiz":
            # hero['stats']['str'] -= 5
            self.intelligence += 5
            # hero['stats']['stl'] += 5
            self.maxhp = self.maxhp * 0.9
        # paladins are midly strong, and midly smart but lack in stealth
        elif self.chrClass == "pldn":
            self.strength += 2
            self.intelligence += 2
            self.stealth -= 5
            self.maxhp = self.maxhp * 1.25
        # Warriors are strong, dumb, and not sneaky. but strong.
        elif self.chrClass == "warr":
            self.strength += 5
            self.intelligence -= 5
            self.stealth -= 5
            self.maxhp = self.maxhp * 1.5
        self.hitpoints = self.maxhp

    def setDead(self, tileObj):
        print(f"Congrats! you died after {tileObj.tile_id} tiles.")
        print(f"Better luck next time!")

    def setExp(self, monsterObj):
        if monsterObj.level == 1:
            self.expPoints += 10
        elif monsterObj.level >= 2 and monsterObj.level <= 10:
            self.expPoints += 5

    def getStats(self):
        print(f"Race: {self.race}")
        print(f"Class: {self.chrClass}")
        print(f"Intelligence: {self.intelligence}")
        print(f"Strength: {self.strength}")
        print(f"Stealth: {self.stealth}")
        print(f"Hitpoints: {self.hitpoints}/{self.maxhp}")
        print(f"Experience Points: {self.expPoints}/{self.nextLevelExp}")
        print(f"Character level: {self.chrLevel}")
        json_output = {'name': self.name, 'race': self.race, 'class':self.chrClass}
        return json_output

    def doAttack(self, monsterObj):
        attackDamage = random.randint(1, self.chrLevel)
        #strength modifier add 1/10th of character's strength rating to attackDamage
        attackDamage += self.strength/10 
        critRoll = random.randrange(1, 10, 1)
        if critRoll == 5:
            attackDamage = attackDamage * 2
            print(f"{self.name} struck a critical blow for {attackDamage} hitpoints")
        else:
            print(
                f"{self.name} attacks {monsterObj.name} for {attackDamage} hitpoints!"
            )
        monsterObj.hitpoints = monsterObj.hitpoints - attackDamage
        print(f"{monsterObj.name}'s Hitpoints: {monsterObj.hitpoints}")

    def doMagic(self, monsterObj):
        spellname = input("Select Spell: fireball, 'lightning bolt', 'ice shard', heal")
        if spellname in ['fireball', 'lightning bolt', 'ice shard']:
            magicDamage = random.randint(1, self.chrLevel)
            #strength modifier add 1/10th of character's strength rating to attackDamage
            magicDamage += self.intelligence/10
            critRoll = random.randrange(1, 10, 1)
            if critRoll == 5:
                magicDamage = magicDamage * 2
                print(f"{self.name} struck a critical blow for {magicDamage} hitpoints")
            else:
                print(
                    f"{self.name} does a {spellname} spell on {monsterObj.name} for {magicDamage} hitpoints!"
                )
            monsterObj.hitpoints = monsterObj.hitpoints - magicDamage
            print(f"{monsterObj.name}'s Hitpoints: {monsterObj.hitpoints}")
        elif spellname in ['heal']:
            if self.hitpoints + 10 > self.maxhp:
                self.hitpoints = self.maxhp
            else:
                self.hitpoints += 10

    def doFlee(self, monsterObj):
        if monsterObj.level > self.chrLevel:
            return False
        else:
            print("you swiftly run away")
            return True

    def doLevelUp(self):
        self.strength = int(self.strength * 1.5)
        self.intelligence = int(self.intelligence * 1.5)
        self.stealth = int(self.stealth * 1.5)
        self.maxhp = int(self.maxhp * 1.5)
        self.hitpoints = self.maxhp
        self.chrLevel += 1
        self.nextLevelExp = self.chrLevel * 100
        print("Level up! stats upgraded")

    def doRestHP(self):
        if self.hitpoints < self.maxhp:
            if self.hitpoints + 10 > self.maxhp:
                self.hitpoints = self.maxhp
            else:
                self.hitpoints += 10
            print(
                f"You feel well rested, you now have {self.hitpoints}/{self.maxhp} hitpoints"
            )
