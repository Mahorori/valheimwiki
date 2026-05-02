import json
from pathlib import Path
from collections import defaultdict
from .item_db import ItemDrop

class ValheimDatabase:
    def __init__(self):
        self.directory_path = ''
        self._items = dict()
        self.recipes = dict()
        self.drops = dict()
        self.mobs = dict()
        self.locations = dict()
        self.spawns = dict()
        self._dropped_by = dict()
        self._traders = dict()

    def _load_items(self):
        path = self.directory_path / 'items.json'
        with open(path, "r", encoding="utf-8") as f:
            for id, item in json.load(f).items():
                entry = ItemDrop(**item)
                self._items[id] = entry

    def _load_recipes(self):
        path = self.directory_path / 'recipes.json'
        with open(path, "r", encoding="utf-8") as f:
            self.recipes = json.load(f)

    def _load_drops(self):
        path = self.directory_path / 'drops.json'
        with open(path, "r", encoding="utf-8") as f:
            self.drops = json.load(f)

    def _load_mobs(self):
        path = self.directory_path / 'mobs.json'
        with open(path, "r", encoding="utf-8") as f:
            self.mobs = json.load(f)

    def _load_locations(self):
        path = self.directory_path / 'locations.json'
        with open(path, "r", encoding="utf-8") as f:
            self.locations = json.load(f)

    def _load_spawns(self):
        path = self.directory_path / 'spawnLocations.json'
        with open(path, "r", encoding="utf-8") as f:
            self.spawns = json.load(f)

    def _load_traders(self):
        path = self.directory_path / 'traders.json'
        with open(path, "r", encoding="utf-8") as f:
            self._traders = json.load(f)

    def load(self, directory_path: Path):
        if isinstance(directory_path, str):
            self.directory_path = Path(directory_path)
        else:
            self.directory_path = directory_path
        
        self._load_items()
        self._load_recipes()
        self._load_drops()
        self._load_mobs()
        #self._load_locations()
        self._load_spawns()
        self._load_traders()

        # ===== reverse index =====
        self._crafted_from = {}
        for r in self.recipes:
            for req in r["requirements"]:
                if isinstance(req, str):
                    # smelter
                    self._crafted_from.setdefault(req, []).append(r["result"])
                else:
                    self._crafted_from.setdefault(req["item"], []).append(r["result"])

        self._dropped_by = {}
        for mob_id, drops in self.drops.items():
            for d in drops:
                self._dropped_by.setdefault(d["item"], []).append(mob_id)

    def get_item(self, item_id):
        if not item_id or item_id not in self._items:
            return None
        
        return self._items[item_id]

    def item_name(self, item_id):
        if item_id not in self._items:
            return ''
        
        return self._items[item_id].name

    def get_mob(self, mob_id):
        if not mob_id or mob_id not in self.mobs:
            return None
        
        return self.mobs[mob_id]

    def dropped_by(self, item_id):
        if not item_id:
            yield None
        
        for mob_id in self._dropped_by.get(item_id, []):
            mob = self.get_mob(mob_id)
            if mob:
                yield mob

    def get_drops(self, mob_id):
        if not mob_id or mob_id not in self.drops:
            return []
        return self.drops[mob_id]

    def crafted_from(self, item_id):
        if not item_id:
            return []
        
        ingredients = []
        for item_id in self._crafted_from.get(item_id, []):
            ingredients.append(self.get_item(item_id))
        return ingredients
    
    def item_recipe(self, item_id):
        for recipe in self.recipes:
            if recipe.get("result") == item_id:
                return recipe
        return None

    def get_mob_biomes(self, mob_id):
        for loc in self.spawns:
            if loc['enabled'] and loc['name'] == mob_id:
                if not loc['requiredGlobalKey'] and not loc['requiredEnvironments']:
                    return loc['biome']
        return []

    def get_traders(self):
        return self._traders