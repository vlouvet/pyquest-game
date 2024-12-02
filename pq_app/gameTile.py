class pqGameTile:
    def __init__(self):
        self.tile_id = 1
        self.tile_content_type = "quest_info"
        self.tile_content = "The time has come to leave this place.\nPress enter to move onto the next tile\n\n"
    
    def generate_signpost(self):
        self.tile_content_type = "quest_info for tile signpost"
        return self.tile_content
