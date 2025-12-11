#!/usr/bin/env python3
"""
Test Phase 3: Enhanced Combat System
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pq_app import create_app, model
from pq_app.services import CombatService


def test_enhanced_combat():
    """Test Phase 3 enhanced combat implementation"""
    app = create_app('testing')
    
    with app.app_context():
        # Initialize database
        model.db.create_all()
        model.init_defaults()
        
        print("=" * 70)
        print("PHASE 3: ENHANCED COMBAT SYSTEM TEST")
        print("=" * 70)
        
        # Create test players with different classes
        print("\n1. Creating test players...")
        
        # Witch player
        witch_class = model.PlayerClass.query.filter_by(name='witch').first()
        witch = model.User(username="test_witch", email="witch@test.com")
        witch.set_password("password")
        witch.playerclass = witch_class.id
        witch.playerrace = model.PlayerRace.query.filter_by(name='Human').first().id
        model.db.session.add(witch)
        
        # Fighter player
        fighter_class = model.PlayerClass.query.filter_by(name='fighter').first()
        fighter = model.User(username="test_fighter", email="fighter@test.com")
        fighter.set_password("password")
        fighter.playerclass = fighter_class.id
        fighter.playerrace = model.PlayerRace.query.filter_by(name='Human').first().id
        model.db.session.add(fighter)
        
        # Elf healer
        healer_class = model.PlayerClass.query.filter_by(name='healer').first()
        elf_race = model.PlayerRace.query.filter_by(name='Elf').first()
        elf_healer = model.User(username="test_elf_healer", email="elf@test.com")
        elf_healer.set_password("password")
        elf_healer.playerclass = healer_class.id
        elf_healer.playerrace = elf_race.id
        model.db.session.add(elf_healer)
        
        model.db.session.commit()
        print(f"  ✓ Created witch (id={witch.id})")
        print(f"  ✓ Created fighter (id={fighter.id})")
        print(f"  ✓ Created elf healer (id={elf_healer.id})")
        
        # Test get_available_actions
        print("\n2. Testing get_available_actions()...")
        service = CombatService()
        
        witch_actions = service.get_available_actions(witch, "monster")
        fighter_actions = service.get_available_actions(fighter, "monster")
        elf_actions = service.get_available_actions(elf_healer, "monster")
        
        print(f"\n  Witch available actions ({len(witch_actions)}):")
        for action in witch_actions:
            class_req = f" [{action.required_class.name}]" if action.required_class else ""
            race_req = f" [{action.required_race.name}]" if action.required_race else ""
            print(f"    • {action.name}{class_req}{race_req}")
        
        print(f"\n  Fighter available actions ({len(fighter_actions)}):")
        for action in fighter_actions:
            class_req = f" [{action.required_class.name}]" if action.required_class else ""
            print(f"    • {action.name}{class_req}")
        
        print(f"\n  Elf Healer available actions ({len(elf_actions)}):")
        for action in elf_actions:
            class_req = f" [{action.required_class.name}]" if action.required_class else ""
            race_req = f" [{action.required_race.name}]" if action.required_race else ""
            print(f"    • {action.name}{class_req}{race_req}")
        
        # Verify class-specific filtering
        witch_has_fireball = any(a.code == "fireball" for a in witch_actions)
        fighter_has_fireball = any(a.code == "fireball" for a in fighter_actions)
        fighter_has_power_strike = any(a.code == "power_strike" for a in fighter_actions)
        elf_has_elven_grace = any(a.code == "elven_grace" for a in elf_actions)
        
        assert witch_has_fireball, "Witch should have Fireball"
        assert not fighter_has_fireball, "Fighter should NOT have Fireball"
        assert fighter_has_power_strike, "Fighter should have Power Strike"
        assert elf_has_elven_grace, "Elf should have Elven Grace"
        
        print("\n  ✓ Class/race filtering working correctly!")
        
        # Test execute_combat_action
        print("\n3. Testing execute_combat_action()...")
        
        # Create a test tile
        playthrough = model.Playthrough(user_id=witch.id)
        model.db.session.add(playthrough)
        model.db.session.commit()
        
        monster_type = model.TileTypeOption.query.filter_by(name='monster').first()
        tile = model.Tile(
            user_id=witch.id,
            type=monster_type.id,
            content="A goblin appears!",
            playthrough_id=playthrough.id
        )
        model.db.session.add(tile)
        model.db.session.commit()
        
        # Execute a light attack
        light_attack = model.CombatAction.query.filter_by(code='attack_light').first()
        result = service.execute_combat_action(witch, tile, light_attack)
        
        print(f"  ✓ Executed Light Attack")
        print(f"    - Success: {result.success}")
        print(f"    - Message: {result.message}")
        print(f"    - HP Change: {result.player_hp_change}")
        print(f"    - Player alive: {result.player_alive}")
        
        # Verify Encounter was created
        encounter_count = model.Encounter.query.filter_by(tile_id=tile.id).count()
        assert encounter_count > 0, "Encounter should be created"
        print(f"  ✓ Encounter record created (count={encounter_count})")
        
        encounter = model.Encounter.query.filter_by(tile_id=tile.id).first()
        print(f"    - Combat Action: {encounter.combat_action.name}")
        print(f"    - Damage Dealt: {encounter.damage_dealt}")
        print(f"    - Damage Received: {encounter.damage_received}")
        print(f"    - Player HP: {encounter.player_hp_before} → {encounter.player_hp_after}")
        
        # Test with Fireball (witch-specific)
        print("\n4. Testing class-specific action (Fireball)...")
        fireball = model.CombatAction.query.filter_by(code='fireball').first()
        
        # Create new tile for witch
        tile2 = model.Tile(
            user_id=witch.id,
            type=monster_type.id,
            content="A troll appears!",
            playthrough_id=playthrough.id
        )
        model.db.session.add(tile2)
        model.db.session.commit()
        
        result = service.execute_combat_action(witch, tile2, fireball)
        print(f"  ✓ Witch executed Fireball")
        print(f"    - Message: {result.message}")
        
        # Test heal action
        print("\n5. Testing heal action...")
        # Damage witch first
        witch.take_damage(30)
        hp_before = witch.hitpoints
        
        heal = model.CombatAction.query.filter_by(code='heal').first()
        tile3 = model.Tile(
            user_id=witch.id,
            type=monster_type.id,
            content="Resting spot",
            playthrough_id=playthrough.id
        )
        model.db.session.add(tile3)
        model.db.session.commit()
        
        result = service.execute_combat_action(witch, tile3, heal)
        hp_after = witch.hitpoints
        
        print(f"  ✓ Executed Heal")
        print(f"    - HP Before: {hp_before}")
        print(f"    - HP After: {hp_after}")
        print(f"    - HP Change: {result.player_hp_change}")
        
        # Test API endpoint
        print("\n6. Testing /combat-actions endpoint...")
        with app.test_client() as client:
            # Login witch
            from flask_login import login_user
            with client.session_transaction() as sess:
                sess['_user_id'] = str(witch.id)
            
            # Get combat actions
            response = client.get(
                f'/player/{witch.id}/game/tile/{tile.id}/combat-actions',
                headers={'X-Requested-With': 'XMLHttpRequest'}
            )
            
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.get_json()
            
            print(f"  ✓ API returned {len(data['available_actions'])} actions")
            print(f"    - Tile type: {data['tile_type']}")
            
            # Verify fireball is in the list
            action_codes = [a['code'] for a in data['available_actions']]
            assert 'fireball' in action_codes, "Fireball should be available for witch"
            assert 'power_strike' not in action_codes, "Power Strike should NOT be available for witch"
            
            print(f"  ✓ API correctly filters actions by class")
        
        print("\n" + "=" * 70)
        print("PHASE 3 ENHANCED COMBAT: ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Task 3: get_available_actions() - COMPLETE")
        print("✅ Task 4: execute_combat_action() - COMPLETE")
        print("✅ Task 5: Encounter tracking - COMPLETE")
        print("✅ API endpoint for combat actions - COMPLETE")
        print("\nNext steps:")
        print("  • Add UI for combat action selection")
        print("  • Integrate monster HP system")
        print("  • Add defense boost persistence")
        print("  • Create combat action selection modal/buttons")


if __name__ == '__main__':
    test_enhanced_combat()
