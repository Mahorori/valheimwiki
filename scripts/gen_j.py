from jinja2 import Environment, FileSystemLoader
import json, os
from collections import defaultdict

# ===== definitions =====
ITEM_CATEGORY_ORDER = [
    "Ammo",
    "Weapon",
    "Armor",
    "Shield",
    "Tool",
    "Torch",
    "Trinket",
    "Utility",
    "Consumable",
    "Material",
    "Trophy",
    "Misc"
]

AMMO_TYPES = {
    "Ammo",
    "AmmoNonEquipable"
}

WEAPON_TYPES = {
    "Bow",
    "OneHandedWeapon",
    "TwoHandedWeapon",
    "TwoHandedWeaponLeft",
}

ARMOR_TYPES = {
    "Helmet",
    "Chest",
    "Legs",
    "Shoulder",
}

DAMAGE_TYPES = [
    "damage",
    "blunt",
    "slash",
    "pierce",
    "chop",
    "pickaxe",
    "fire",
    "frost",
    "lightning",
    "poison",
    "spirit",
]

# ===== paths =====
BepInExPath = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx"
SITE_DIR = "../site"

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=True
)

# ===== filters =====
def fmt_number(v):
    if v is None:
        return ""
    if isinstance(v, (int, float)) and float(v).is_integer():
        return str(int(v))
    return str(v)

env.filters["num"] = fmt_number

# ===== load =====
def get_total_damage(item):
    damages = item.get('damages', {})
    return (
        damages.get("damage", 0) +
        damages.get("blunt", 0) +
        damages.get("slash", 0) +
        damages.get("pierce", 0) +
        damages.get("chop", 0) +
        damages.get("pickaxe", 0) +
        damages.get("fire", 0) +
        damages.get("frost", 0) +
        damages.get("lightning", 0) +
        damages.get("poison", 0) +
        damages.get("spirit", 0)
    )

def sort_key(item):
    t = item.get("type", "")

    # ammo, weapons
    if t in ("Ammo", "AmmoNonEquipable", "Bow", "OneHandedWeapon", "TwoHandedWeapon"):
        return (
            item["type"],
            get_total_damage(item)
        )

    # armors
    if t in ("Helmet", "Chest", "Legs", "Shoulder"):
        return (
            item["type"],
            item.get("armor", 0)
        )
    
    # shields
    if t in ("Shield"):
        return (
            item["type"],
            item.get("blockPower", 0)
        )

    # etc
    return (
        item["type"],
        item.get("id", "")
    )

def load_json(name):
    with open(os.path.join(BepInExPath, name), encoding="utf-8") as f:
        return json.load(f)

# load items and sort by damage etc...
items = load_json("items.json")
items = sorted(items, key=sort_key)
items = {i["id"]: i for i in items}
recipes = load_json("recipes.json")
drops = load_json("drops.json")
mobs = load_json("mobs.json")
spawn_locations = load_json("spawnLocations.json")

os.makedirs(f"{SITE_DIR}/items", exist_ok=True)
os.makedirs(f"{SITE_DIR}/mobs", exist_ok=True)

# ===== helpers =====
def icon_path(id):
    p = f"../site/static/icons/{id}.png"
    return p if os.path.exists(f"../site/static/icons/{id}.png") else None

def item_recipes(item_id):
    return [r for r in recipes if r["result"] == item_id]

def drops_by_item():
    d = defaultdict(list)
    for mob in drops:
        for drop in mob["drops"]:
            d[drop["item"]].append(mob["name"])
    return d

dropped_by = drops_by_item()

# ===== item category =====
def item_category(item):
    item_type = item.get("type", "")
    if item_type in AMMO_TYPES:
        return "Ammo"
    if item_type in WEAPON_TYPES:
        return "Weapon"
    if item_type in ARMOR_TYPES:
        return "Armor"
    return item_type

def ammo_group(item):
    return item.get("ammoType")

def weapon_group(item):
    return item.get("skillType")

def food_group(item):
    eitr = item.get("foodEitr", 0)
    if eitr > 0:
        return "Eitr"
    
    food = item.get("food", 0)
    stamina = item.get("foodStamina", 0)
    if not food and not stamina:
        if item.get("isDrink", 0):
            return "Drink"
        return "Misc"
    if food > stamina:
        return "Food"
    return "Stamina"

def material_group(item):
    if item.get("teleportable") is False:
        return "Ore"
    if any(key in item and item.get(key) >= 0 for key in ("food", "foodStamina", "foodEitr")):
        return food_group(item)
    return "Drops"

def consumable_group(item):
    if item.get("isDrink") is True:
        return "Drink"
    return food_group(item)

def food_sort_key(entry):
    item_id, item = entry
    return (
        item.get("food", 0),
        item.get("foodStamina", 0),
        item.get("foodEitr", 0),
        item.get("foodBurnTime", 0),
        item.get("foodRegen", 0),
        item.get("name", item_id),
    )

def category_sort_key(category):
    if category in ITEM_CATEGORY_ORDER:
        return (ITEM_CATEGORY_ORDER.index(category), category)
    return (len(ITEM_CATEGORY_ORDER), category)

def material_group_sort_key(group):
    preferred = ["Ore", "Food", "Stamina", "Eitr", "Drops"]
    if group in preferred:
        return (preferred.index(group), group)
    return (len(preferred), group)

def consumable_group_sort_key(group):
    preferred = ["Drink", "Food", "Stamina", "Eitr"]
    if group in preferred:
        return (preferred.index(group), group)
    return (len(preferred), group)

def skill_type_sort_key(skill_type):
    preferred = [
        "Swords",
        "Knives",
        "Clubs",
        "Polearms",
        "Spears",
        "Axes",
        "Bows",
        "Crossbows",
        "ElementalMagic",
        "BloodMagic",
        "Unarmed",
        "Pickaxes",
        "Arrow",
        "Bolt",
        "Missile",
    ]
    if skill_type in preferred:
        return (preferred.index(skill_type), skill_type)
    return (len(preferred), str(skill_type))


# ===== render util =====
def render(template_name, **ctx):
    return env.get_template(template_name).render(**ctx)

def write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ===== item pages =====
for item_id, item in items.items():

    html = render("pages/item.html",
        item=item,
        icon=f"../static/icons/{item_id}.png",
        recipes=item_recipes(item_id),
        dropped_by=dropped_by.get(item_id, []),
        breadcrumbs = [
            {"name": "Home", "url": "../index.html"},
            {"name": "Items", "url": "index.html"},
            {"name": item["id"], "url": None }
        ],
        base_path="../")

    page = render("base.html",
        title=item["name"],
        content=html,
        base_path="../"
    )

    write(f"{SITE_DIR}/items/{item_id}.html", page)

# ===== item index =====
grouped_and_sorted_items = defaultdict(list)
grouped = defaultdict(list)
for item_id, item in items.items():
    if not icon_path(item_id):
        continue
    grouped[item_category(item)].append((item_id, item))

# we need CAT1 > CAT2 > items
def category_sort_key(category):
    if category in ITEM_CATEGORY_ORDER:
        return (ITEM_CATEGORY_ORDER.index(category), category)
    return (len(ITEM_CATEGORY_ORDER), category)

# CAT2
for category in sorted(grouped.keys(), key=category_sort_key):
    category_items = grouped[category]
    if category == "Ammo":
        ammo_by_type = defaultdict(list)
        for item_id, item in category_items:
            ammo_by_type[ammo_group(item)].append((item_id, item))
        
        grouped_and_sorted_items[category] = dict(sorted(ammo_by_type.items(), key=skill_type_sort_key))
    elif category == "Weapon":
        ammo_by_type = defaultdict(list)
        for item_id, item in category_items:
            ammo_by_type[weapon_group(item)].append((item_id, item))
        
        grouped_and_sorted_items[category] = dict(sorted(ammo_by_type.items(), key=skill_type_sort_key))
    elif category == "Material":
        ammo_by_type = defaultdict(list)
        for item_id, item in category_items:
            ammo_by_type[material_group(item)].append((item_id, item))
        
        grouped_and_sorted_items[category] = dict(sorted(ammo_by_type.items(), key=material_group_sort_key))
    elif category == "Consumable":
        ammo_by_type = defaultdict(list)
        for item_id, item in category_items:
            ammo_by_type[consumable_group(item)].append((item_id, item))
        
        grouped_and_sorted_items[category] = dict(sorted(ammo_by_type.items(), key=material_group_sort_key))
    else:
        ammo_by_type = defaultdict(list)
        for item_id, item in category_items:
            ammo_by_type[item.get("type", "Unknown")].append((item_id, item))
        
        grouped_and_sorted_items[category] = ammo_by_type
            
html = render("pages/items_index.html", grouped=grouped_and_sorted_items, breadcrumbs = [
    {"name": "Home", "url": "../index.html"},
    {"name": "Items", "url": None},
])
write(f"{SITE_DIR}/items/index.html",
      render("base.html", title="Items", content=html, base_path="../"))

# ===== mob pages =====
for mob_id, mob in mobs.items():

    mob_drops = next((d["drops"] for d in drops if d["name"] == mob_id), [])

    html = render("pages/mob.html",
        mob=mob,
        drops=mob_drops
    )

    write(f"{SITE_DIR}/mobs/{mob_id}.html",
          render("base.html", title=mob["name"], content=html, base_path="../"))

# ===== mobs index =====
def spawn_time_tags(entry):
    tags = []

    if entry.get("spawnAtDay") and entry.get("spawnAtNight"):
        tags.append("Day/Night")
    elif entry.get("spawnAtDay"):
        tags.append("Day")
    elif entry.get("spawnAtNight"):
        tags.append("Night")

    if entry.get("tameable"):
        tags.append("Tameable")

    return tags

def condition_values(value):
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [value]

def mob_groups():
    # ========================
    # グループ分け
    # ========================
    boss_groups = defaultdict(list)
    normal_groups = defaultdict(list)
    grouped_spawns = set()

    for loc in spawn_locations:
        if not loc.get("enabled"):
            continue

        mob = mobs.get(loc.get("name"))
        if not mob:
            continue

        biomes = loc.get("biome") or ["Unknown"]
        global_key = loc.get("requiredGlobalKey", "")
        environments = loc.get("requiredEnvironments", [])
        environment_key = tuple(environments) if isinstance(environments, list) else (environments,)
        spawn_at_day = loc.get("spawnAtDay")
        spawn_at_night = loc.get("spawnAtNight")

        for b in biomes:
            spawn_key = (mob["id"], b, global_key, environment_key, spawn_at_day, spawn_at_night)
            if spawn_key in grouped_spawns:
                continue
            grouped_spawns.add(spawn_key)

            entry = {
                "mob": mob,
                "requiredGlobalKey": global_key,
                "requiredEnvironments": environments,
                "spawnAtDay": spawn_at_day,
                "spawnAtNight": spawn_at_night,
                "tameable": mob.get('tameable', False)
            }
            if mob.get("boss"):
                boss_groups[b](entry)
            else:
                normal_groups[b].append(entry)
    
    # merge day/night
    def merge_and_sort(mob_groups):
        for biome, entries in mob_groups.items():
            normal = []
            normal_by_id = {}
            required_env = []
            for entry in entries:
                global_keys = condition_values(entry.get("requiredGlobalKey"))
                environments = condition_values(entry.get("requiredEnvironments"))

                if not global_keys and not environments:
                    mob_id = entry["mob"].get("id")
                    if mob_id in normal_by_id:
                        merged = normal_by_id[mob_id]
                        merged["spawnAtDay"] = merged.get("spawnAtDay") is True or entry.get("spawnAtDay") is True
                        merged["spawnAtNight"] = merged.get("spawnAtNight") is True or entry.get("spawnAtNight") is True
                        continue
                    normal_entry = dict(entry)
                    normal_by_id[mob_id] = normal_entry
                    normal.append(normal_entry)
                    continue
                
                required_env.append(entry)

            mob_groups[biome] = sorted(normal + required_env, key=lambda e: (e["mob"]["hp"]))
        return mob_groups

    for id, mob in mobs.items():
        if any(key[0] == mob["id"] for key in grouped_spawns):
            continue

        entry = {
            "mob": mob,
            "requiredGlobalKey": "",
            "requiredEnvironments": [],
            "spawnAtDay": None,
            "spawnAtNight": None,
        }
        if mob.get("boss"):
            boss_groups["Unknown"].append(entry)
        else:
            normal_groups["Unknown"].append(entry)
    return merge_and_sort(normal_groups), merge_and_sort(boss_groups)

groups, bosses = mob_groups()

html = render("pages/mobs_index.html", normal_mobs=groups, bosses=bosses, spawn_time_tags=spawn_time_tags)
write(f"{SITE_DIR}/mobs/index.html",
      render("base.html", title="Mobs", content=html, base_path="../", content_class="mob-page"))

# ===== home =====
write(f"{SITE_DIR}/index.html",
      render("base.html",
             title="Home",
             content=render("pages/home.html"),
             base_path=""))

print("done")