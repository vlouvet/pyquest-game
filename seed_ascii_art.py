#!/usr/bin/env python3
"""
Seed ASCII art from text files into the database.
This script loads ASCII art from the ascii_art/ directory and updates 
the TileTypeOption records with the corresponding art.

Usage:
    python seed_ascii_art.py
"""
import os
import sys
from pathlib import Path

# Add the parent directory to Python path to import pq_app
sys.path.insert(0, str(Path(__file__).parent))

from pq_app import create_app
from pq_app.model import db, TileTypeOption


def load_ascii_art_from_file(filename):
    """Load ASCII art content from a file"""
    filepath = Path(__file__).parent / "ascii_art" / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"Warning: File not found: {filepath}")
        return None


def seed_ascii_art():
    """Seed ASCII art into TileTypeOption records"""
    app = create_app()
    
    with app.app_context():
        # Mapping of tile type names to their ASCII art files
        art_mapping = {
            'monster': 'monster.txt',
            'scene': 'scene.txt',
            'sign': 'sign.txt',
            'treasure': 'treasure.txt',
        }
        
        updated_count = 0
        
        for tile_type_name, art_filename in art_mapping.items():
            # Find the tile type in database
            tile_type = TileTypeOption.query.filter_by(name=tile_type_name).first()
            
            if tile_type:
                # Load ASCII art from file
                ascii_art = load_ascii_art_from_file(art_filename)
                
                if ascii_art:
                    tile_type.ascii_art = ascii_art
                    db.session.add(tile_type)
                    updated_count += 1
                    print(f"✓ Updated '{tile_type_name}' with ASCII art from {art_filename}")
                else:
                    print(f"✗ Failed to load ASCII art for '{tile_type_name}' from {art_filename}")
            else:
                print(f"✗ Tile type '{tile_type_name}' not found in database")
        
        # Commit all changes
        if updated_count > 0:
            db.session.commit()
            print(f"\n✓ Successfully seeded {updated_count} tile type(s) with ASCII art")
        else:
            print("\n✗ No tile types were updated")


if __name__ == '__main__':
    print("Seeding ASCII art into database...\n")
    seed_ascii_art()
