import json
import os

# ===== paths =====
BepInExPath = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx"
ICON_DIR = "icons"  # Unityで出力したやつ
SITE_DIR = "site"

# ===== load =====
items = dict()

printed = set()

with open(os.path.join(BepInExPath, "locationDrops.json"), "r", encoding="utf-8") as f:
    items = json.load(f)
    for item in items:
        if 'BlackForest' in item['biome']:
            for i in item["items"]:
                if i['id'] in printed:
                    continue
                printed.add(i['id'])
                print(i['id'])
