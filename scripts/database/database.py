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
        self._crafting_stations = dict()

        # cache
        self._biome_locations = dict()

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

        # link entries
        entities = self.locations["entities"]
        for loc in self.locations["locations"].values():

            # link exteriors
            loc["exteriors"] = [
                entities.get(entity_id, {"id": entity_id})
                for entity_id in loc.get("exteriors", [])
            ]

            # link rooms
            for i, room in enumerate(loc.get("rooms", [])):
                remove_indexes = []
                for j, component in enumerate(room['components']):
                    c = entities.get(component)
                    if not c:
                        # probably this is useless so remove from list
                        remove_indexes.append(j)
                    else:
                        loc["rooms"][i]['components'][j] = c
                for j in reversed(remove_indexes):
                    room['components'].pop(j)

        # link entities
        for entity in self.locations["entities"].values():
            for component in entity.values():
                spawnWhenDestroyed = component.get('spawnWhenDestroyed', None)
                if spawnWhenDestroyed:
                    component["spawnWhenDestroyed"] = entities.get(spawnWhenDestroyed, {})

    def _load_spawns(self):
        path = self.directory_path / 'spawnLocations.json'
        with open(path, "r", encoding="utf-8") as f:
            self.spawns = json.load(f)

    def _load_traders(self):
        path = self.directory_path / 'traders.json'
        with open(path, "r", encoding="utf-8") as f:
            self._traders = json.load(f)

    def _load_crafting_stations(self):
        path = self.directory_path / 'craftingStations.json'
        with open(path, "r", encoding="utf-8") as f:
            self._crafting_stations = json.load(f)

    def _load_vegetations(self):
        path = self.directory_path / 'vegetations.json'
        with open(path, "r", encoding="utf-8") as f:
            self.vegetations = json.load(f)

    def load(self, directory_path: Path):
        if isinstance(directory_path, str):
            self.directory_path = Path(directory_path)
        else:
            self.directory_path = directory_path
        
        self._load_items()
        self._load_recipes()
        self._load_drops()
        self._load_mobs()
        self._load_locations()
        self._load_spawns()
        self._load_traders()
        self._load_crafting_stations()
        self._load_vegetations()

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
            if not recipe['enabled']:
                continue

            if recipe.get("result") == item_id:
                return recipe
        return None
    
    def item_recipes(self, item_id):
        result = []
        for recipe in self.recipes:
            if not recipe['enabled']:
                continue

            if recipe.get("result") == item_id:
                result.append(recipe)
        return result
    
    def is_ore(self, item_id):
        for recipe in self.recipes:
            if len(recipe['requirements']) == 1:
                if recipe['requirements'][0] == item_id:
                    return recipe['craftingStation'] in ('smelter', 'blastfurnace')
        return False
    
    def is_ingot(self, item_id):
        # well...
        if item_id == 'Bronze':
            return True
        for recipe in self.recipes:
            if recipe['result'] == item_id:
                if recipe['craftingStation'] in ('smelter', 'blastfurnace'):
                    return True
                return False
        return False

    def get_mob_biomes(self, mob_id):
        for loc in self.spawns:
            if loc['enabled'] and loc['name'] == mob_id:
                if not loc['requiredGlobalKey'] and not loc['requiredEnvironments']:
                    return loc['biome']
        return []

    def get_traders(self):
        return self._traders
    
    def get_trader(self, id):
        return self._traders.get(id, None)
    
    def iter_vegetations_dropping(self, item_id):
        for id, veg in self.vegetations.items():
            for drop in veg['drops']:
                if drop['name'] == item_id:
                    yield veg

    def get_vegetations_by_biome(self, biome: str):
        result = []
        visited = set()

        def add_vegetation(veg: dict):
            veg_id = veg["id"]

            if veg_id in visited:
                return

            visited.add(veg_id)

            # add vegetation DATA itself
            result.append(veg)

            # recursively add spawned objects
            for child_id in veg.get("spawnWhenDestroyed", []):
                child = self.vegetations.get(child_id)

                if child:
                    add_vegetation(child)

        # start from biome matches
        for veg in self.vegetations.values():
            if biome in veg.get("biomes", []):
                add_vegetation(veg)

        return result

    def get_crafting_station(self, id):
        return self._crafting_stations.get(id, None)
    
    def get_locations_by_biome(self, biome):

        if biome in self._biome_locations:
            return self._biome_locations.get(biome)

        result = []
        for loc_id, loc in self.locations['locations'].items():
            if biome in loc['biomes']:
                result.append(loc)

        # cache locations
        self._biome_locations[biome] = result
        return result
    
    def find_location_by_mobid(self, mob_id):
        for loc in self.locations['locations'].values():
            for exterior in loc.get('exteriors', []):
                if 'OfferingBowl' in exterior:
                    if exterior['OfferingBowl'].get('bossPrefab', '') == mob_id:
                        return loc['biomes']
                    
                if 'CreatureSpawner' in exterior:
                    if exterior['CreatureSpawner'].get('mob_id', '') == mob_id:
                        return loc['biomes']
                    
            for room in loc.get('rooms', []):
                for component in room.get('components', []):
                    if 'OfferingBowl' in component:
                        if component['OfferingBowl'].get('bossPrefab', '') == mob_id:
                            return loc['biomes']
                        
                    if 'CreatureSpawner' in component:
                        if component['CreatureSpawner'].get('mob_id', '') == mob_id:
                            return loc['biomes']