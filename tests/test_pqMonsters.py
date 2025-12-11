import types
import random

from pq_app.pqMonsters import NPCMonster


class DummyPlayer:
    def __init__(self, username="hero", max_hp=100, hitpoints=None):
        self.username = username
        self.max_hp = max_hp
        if hitpoints is not None:
            self.hitpoints = hitpoints


def test_choose_type_returns_expected_values(monkeypatch):
    # Force random.choice to select a known value
    monkeypatch.setattr(random, "choice", lambda seq: "dragon")
    m = NPCMonster()
    assert m.name == "dragon"
    # choose_type should return one of the expected strings
    assert m.choose_type() in {"elephant", "giraffe", "gryffon", "dragon"}


def test_do_attack_level_1_with_no_hitpoints_attr(monkeypatch, capsys):
    # Deterministic damage
    monkeypatch.setattr(random, "randint", lambda a, b: 2)
    monster = NPCMonster()
    monster.level = 1
    # Player with no hitpoints attribute set initially
    player = types.SimpleNamespace(username="tester", max_hp=None)

    monster.do_attack(player)

    captured = capsys.readouterr()
    assert "attacks tester for" in captured.out
    # hitpoints should be created and reduced
    assert hasattr(player, "hitpoints")
    assert player.hitpoints >= 0


def test_do_attack_level_2_midrange(monkeypatch, capsys):
    # For level 2, attack_max should be max(1, int(max_hp/2))
    monkeypatch.setattr(random, "randint", lambda a, b: 5)
    monster = NPCMonster()
    monster.level = 2
    player = DummyPlayer(username="ally", max_hp=30, hitpoints=30)

    monster.do_attack(player)

    captured = capsys.readouterr()
    assert "attacks ally for" in captured.out
    # damage was 5 and hp should have decreased accordingly
    assert player.hitpoints == 25


def test_do_attack_level_high_clamps_and_never_negative(monkeypatch, capsys):
    # For high level, attack_max should be max(1, max_hp)
    monkeypatch.setattr(random, "randint", lambda a, b: 200)
    monster = NPCMonster()
    monster.level = 10
    player = DummyPlayer(username="big", max_hp=150, hitpoints=10)

    monster.do_attack(player)

    captured = capsys.readouterr()
    # hp should not go below 0
    assert player.hitpoints == 0
    assert "Hitpoints: 0" in captured.out


def test_do_attack_with_negative_max_hp_fallback(monkeypatch, capsys):
    # Negative or non-int max_hp should fallback to 10
    monkeypatch.setattr(random, "randint", lambda a, b: 3)
    monster = NPCMonster()
    monster.level = 1
    player = types.SimpleNamespace(username="nope", max_hp=-5, hitpoints=5)

    monster.do_attack(player)
    # damage 3 should reduce hp
    assert player.hitpoints == 2


def test_do_attack_default_player_name_and_missing_attributes(monkeypatch, capsys):
    monkeypatch.setattr(random, "randint", lambda a, b: 1)
    monster = NPCMonster()
    monster.level = 1
    # Player lacks username attribute
    player = types.SimpleNamespace(max_hp=20)

    monster.do_attack(player)
    captured = capsys.readouterr()
    assert "attacks player for" in captured.out
    # hitpoints attribute should be present after attack
    assert hasattr(player, "hitpoints")
