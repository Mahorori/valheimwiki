import json
import os, sys

# ===== paths =====
BepInExPath = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx"
ICON_DIR = "icons"  # Unityで出力したやつ
SITE_DIR = "site"

# ===== load =====
items = dict()

printed = set()

with open(os.path.join(BepInExPath, "locations.json"), "r", encoding="utf-8") as f:
    items = json.load(f)
    for id, loc in items.items():
        if 'BlackForest' in loc['biomes']:
            print(id)
            for id, entity in loc["entities"].items():
                if 'name' in entity:
                    print(' ', entity.get('name', 'noname'))
                if 'id' in entity:
                    print(' ', entity.get('id', 'noid'))
            print(' rooms')
            if loc['rooms']:
                if loc["rooms"]:
                    for room_id, rooms in loc["rooms"].items():
                        print('  ', room_id)
                        for room in rooms:
                            if 'name' in room:
                                print('    ', room['name'])
                            elif 'id' in room:
                                print('    ', room['id'])

sys.exit(0)

printed = set()
with open(os.path.join(BepInExPath, "vegetations.json"), "r", encoding="utf-8") as f:
    items = json.load(f)
    for item in items:
        if 'BlackForest' in item['biome']:
            id = item['id']
            if id in printed:
                continue
            printed.add(id)
            print(item['name'], id)

            printed_name = set()
            for d in item['drops']:
                if d['name'] in printed_name:
                    continue
                printed_name.add(d['name'])
                print('  ', d['name'])
