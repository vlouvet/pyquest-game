import random

class npcMonster:
    def __init__(self, level=1):
        self.name = "wildling"
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
        animalAscii['elephant'] = """
            ___     _,.--.,_
        .-~   ~--"~-.   ._ "-.
        /      ./_    Y    "-. \
        Y       :~     !         Y
        lq p    |     /         .|
    _   \. .-, l    /          |j
    ()\___) |/   \_/";          !
    \._____.-~\  .  ~\.      ./
                Y_ Y_. "vr"~  T
                (  (    |L    j   
                [nn[nn..][nn..]
        ~~~~~~~~~~~~~~~~~~~~~~~"""

        animalAscii['giraffe'] = """\
                ._ o o
                \_`-)|_
            ,""       \ 
            ,"  ## |   ಠ ಠ. 
        ," ##   ,-\__    `.
        ,"       /     `--._;)
    ,"     ## /
    ,"   ##    /
                    """
        
        animalAscii['Gryffon'] = """
                                   _
                          _)\.-.
         .-.__,___,_.-=-. )\`  a`\_
     .-.__\__,__,__.-=-. `/  \     `\
     {~,-~-,-~.-~,-,;;;;\ |   '--;`)/
      \-,~_-~_-,~-,(_(_(;\/   ,;/
       ",-.~_,-~,-~,)_)_)'.  ;;(
         `~-,_-~,-~(_(_(_(_\  `;\
   ,          `"~~--,)_)_)_)\_   \
   |\              (_(_/_(_,   \  ;
   \ '-.       _.--'  /_/_/_)   | |
    '--.\    .'          /_/    | |
        ))  /       \      |   /.'
       //  /,        | __.'|  ||
      //   ||        /`    (  ||
     ||    ||      .'       \ \\
     ||    ||    .'_         \ \\
      \\   //   / _ `\        \ \\__
       \'-'/(   _  `\,;        \ '--:,
        `"`  `"` `-,,;         `"`",,; """

        animalAscii['Dragon'] = """
            (  )   /\   _                 (     
        \ |  (  \ ( \.(               )                      _____
    \  \ \  `  `   ) \             (  ___                 / _   \
    (_`    \+   . x  ( .\            \/   \____-----------/ (o)   \_
    - .-               \+  ;          (  O                           \____
                            )        \_____________  `              \  /
    (__                +- .( -'.- <. - _  VVVVVVV VV V\                 \/
    (_____            ._._: <_ - <- _  (--  _AAAAAAA__A_/                  |
    .    /./.+-  . .- /  +--  - .     \______________//_              \_______
    (__ ' /x  / x _/ (                                  \___'          \     /
    , x / ( '  . / .  /                                      |           \   /
        /  /  _/ /    +                                      /              \/
    '  (__/                                             /                  \ """