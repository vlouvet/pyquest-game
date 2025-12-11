"""
MediaService - Business logic for media management

Handles ASCII art, images, and other media assets associated with tiles.
"""
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from .. import model


@dataclass
class MediaData:
    """Container for media information"""
    id: int
    media_type: str
    content: Optional[str]
    url: Optional[str]
    is_default: bool
    display_order: int


class MediaService:
    """Service for managing tile media (ASCII art, images, etc.)"""
    
    def __init__(self):
        self.ascii_art_dir = Path(__file__).parent.parent.parent / "ascii_art"
    
    def get_media_for_tile_type(self, tile_type_id: int) -> List[MediaData]:
        """
        Get all media records for a specific tile type.
        
        Args:
            tile_type_id: The ID of the tile type
            
        Returns:
            List of MediaData objects sorted by display_order
        """
        media_records = model.TileMedia.query.filter_by(
            tile_type_id=tile_type_id
        ).order_by(model.TileMedia.display_order).all()
        
        return [
            MediaData(
                id=media.id,
                media_type=media.media_type,
                content=media.content,
                url=media.url,
                is_default=media.is_default,
                display_order=media.display_order
            )
            for media in media_records
        ]
    
    def get_default_media(self, tile_type_id: int, media_type: str = "ascii_art") -> Optional[MediaData]:
        """
        Get the default media for a tile type.
        
        Args:
            tile_type_id: The ID of the tile type
            media_type: Type of media to retrieve (default: "ascii_art")
            
        Returns:
            MediaData object or None if not found
        """
        media = model.TileMedia.query.filter_by(
            tile_type_id=tile_type_id,
            media_type=media_type,
            is_default=True
        ).first()
        
        if media:
            return MediaData(
                id=media.id,
                media_type=media.media_type,
                content=media.content,
                url=media.url,
                is_default=media.is_default,
                display_order=media.display_order
            )
        return None
    
    def get_media_for_tile(self, tile_id: int) -> Optional[MediaData]:
        """
        Get specific media associated with an individual tile.
        
        Args:
            tile_id: The ID of the tile
            
        Returns:
            MediaData object or None if not found
        """
        media = model.TileMedia.query.filter_by(tile_id=tile_id).first()
        
        if media:
            return MediaData(
                id=media.id,
                media_type=media.media_type,
                content=media.content,
                url=media.url,
                is_default=media.is_default,
                display_order=media.display_order
            )
        return None
    
    def create_media_record(
        self,
        tile_type_id: Optional[int] = None,
        tile_id: Optional[int] = None,
        media_type: str = "ascii_art",
        content: Optional[str] = None,
        url: Optional[str] = None,
        is_default: bool = False,
        display_order: int = 0
    ) -> model.TileMedia:
        """
        Create a new TileMedia record.
        
        Args:
            tile_type_id: ID of tile type (for type-level media)
            tile_id: ID of specific tile (for tile-specific media)
            media_type: Type of media ("ascii_art", "image", "animation")
            content: Media content (ASCII art text or file path)
            url: External URL or local file path
            is_default: Whether this is the default media for the type
            display_order: Display order for multiple media items
            
        Returns:
            Created TileMedia record
        """
        # If setting as default, unset other defaults for this type/media_type
        if is_default and tile_type_id:
            existing_defaults = model.TileMedia.query.filter_by(
                tile_type_id=tile_type_id,
                media_type=media_type,
                is_default=True
            ).all()
            for media in existing_defaults:
                media.is_default = False
                model.db.session.add(media)
        
        media = model.TileMedia(
            tile_type_id=tile_type_id,
            tile_id=tile_id,
            media_type=media_type,
            content=content,
            url=url,
            is_default=is_default,
            display_order=display_order
        )
        
        model.db.session.add(media)
        model.db.session.commit()
        
        return media
    
    def update_tile_type_ascii(self, tile_type_id: int, ascii_art: str) -> bool:
        """
        Update the ASCII art directly on a TileTypeOption record.
        This is the legacy method - new media should use TileMedia.
        
        Args:
            tile_type_id: ID of the tile type
            ascii_art: ASCII art content
            
        Returns:
            True if successful, False otherwise
        """
        tile_type = model.db.session.get(model.TileTypeOption, tile_type_id)
        if tile_type:
            tile_type.ascii_art = ascii_art
            model.db.session.add(tile_type)
            model.db.session.commit()
            return True
        return False
    
    def load_ascii_from_files(self, create_tilemedia_records: bool = True) -> dict:
        """
        Load ASCII art from files and update database.
        Updates both TileTypeOption.ascii_art (legacy) and creates TileMedia records.
        
        Args:
            create_tilemedia_records: If True, also create TileMedia records
            
        Returns:
            Dictionary with results: {"updated": int, "failed": list}
        """
        art_mapping = {
            'monster': 'monster.txt',
            'scene': 'scene.txt',
            'sign': 'sign.txt',
            'treasure': 'treasure.txt',
        }
        
        updated_count = 0
        failed = []
        
        for tile_type_name, art_filename in art_mapping.items():
            # Find the tile type in database
            tile_type = model.TileTypeOption.query.filter_by(name=tile_type_name).first()
            
            if not tile_type:
                failed.append(f"Tile type '{tile_type_name}' not found")
                continue
            
            # Load ASCII art from file
            filepath = self.ascii_art_dir / art_filename
            if not filepath.exists():
                failed.append(f"File not found: {filepath}")
                continue
            
            with open(filepath, 'r', encoding='utf-8') as f:
                ascii_art = f.read()
            
            # Update TileTypeOption (legacy method)
            tile_type.ascii_art = ascii_art
            model.db.session.add(tile_type)
            
            # Create TileMedia record if requested
            if create_tilemedia_records:
                # Check if default media already exists
                existing_media = model.TileMedia.query.filter_by(
                    tile_type_id=tile_type.id,
                    media_type="ascii_art",
                    is_default=True
                ).first()
                
                if not existing_media:
                    media = model.TileMedia(
                        tile_type_id=tile_type.id,
                        media_type="ascii_art",
                        content=ascii_art,
                        is_default=True,
                        display_order=0
                    )
                    model.db.session.add(media)
            
            updated_count += 1
        
        model.db.session.commit()
        
        return {
            "updated": updated_count,
            "failed": failed
        }
    
    def delete_media(self, media_id: int) -> bool:
        """
        Delete a TileMedia record.
        
        Args:
            media_id: ID of the media record to delete
            
        Returns:
            True if successful, False otherwise
        """
        media = model.db.session.get(model.TileMedia, media_id)
        if media:
            model.db.session.delete(media)
            model.db.session.commit()
            return True
        return False
    
    def set_default_media(self, media_id: int) -> bool:
        """
        Set a media record as the default for its tile type and media type.
        Unsets other defaults of the same type.
        
        Args:
            media_id: ID of the media record to set as default
            
        Returns:
            True if successful, False otherwise
        """
        media = model.db.session.get(model.TileMedia, media_id)
        if not media or not media.tile_type_id:
            return False
        
        # Unset other defaults for this tile type and media type
        existing_defaults = model.TileMedia.query.filter_by(
            tile_type_id=media.tile_type_id,
            media_type=media.media_type,
            is_default=True
        ).all()
        
        for existing in existing_defaults:
            if existing.id != media_id:
                existing.is_default = False
                model.db.session.add(existing)
        
        # Set this one as default
        media.is_default = True
        model.db.session.add(media)
        model.db.session.commit()
        
        return True
    
    def get_tile_display_media(self, tile_id: int) -> Optional[str]:
        """
        Get the media to display for a tile.
        Priority: tile-specific media > tile type default media > TileTypeOption.ascii_art
        
        Args:
            tile_id: ID of the tile
            
        Returns:
            ASCII art content or None
        """
        # First check for tile-specific media
        tile_media = self.get_media_for_tile(tile_id)
        if tile_media and tile_media.content:
            return tile_media.content
        
        # Get the tile to find its type
        tile = model.db.session.get(model.Tile, tile_id)
        if not tile:
            return None
        
        # Check for default media for the tile type
        default_media = self.get_default_media(tile.type, "ascii_art")
        if default_media and default_media.content:
            return default_media.content
        
        # Fall back to TileTypeOption.ascii_art (legacy)
        tile_type = model.db.session.get(model.TileTypeOption, tile.type)
        if tile_type and tile_type.ascii_art:
            return tile_type.ascii_art
        
        return None
