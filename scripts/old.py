import json
import os
from collections import defaultdict
from default_generator.localization import Localization

BIOME_ORDER = [
    "Meadows", "BlackForest", "Swamp",
    "Mountain", "Plains", "Mistlands",
    "AshLands", "DeepNorth", "Ocean", "Unknown"
]

# ===== paths =====
BepInExPath = r"C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx"
ICON_DIR = "icons"  # Unityで出力したやつ
SITE_DIR = "site"

# ===== load =====
items = dict()

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

with open(os.path.join(BepInExPath, "items.json"), "r", encoding="utf-8") as f:
    items = json.load(f)
    #items = sorted(items, key=lambda x: x['type'])
    items = sorted(items, key=sort_key)
    items = {i["id"]: i for i in items}

with open(os.path.join(BepInExPath, "recipes.json"), "r", encoding="utf-8") as f:
    recipes = json.load(f)

with open(os.path.join(BepInExPath, "drops.json"), "r", encoding="utf-8") as f:
    drops = json.load(f)

with open(os.path.join(BepInExPath, "mobs.json"), "r", encoding="utf-8") as f:
    mobs = json.load(f)

with open(os.path.join(BepInExPath, "spawnLocations.json"), "r", encoding="utf-8") as f:
    spawn_locations = json.load(f)

os.makedirs(f"{SITE_DIR}/items", exist_ok=True)
os.makedirs(f"{SITE_DIR}/mobs", exist_ok=True)

# ===== helper =====
def item_name(item_id):
    if item_id in items:
        item_name = items.get(item_id)['name']
    else:
        item_name = item_id
    return item_name

def mob_name(id):
    if id in mobs:
        name = mobs.get(id)['name']
    else:
        name = id
    return name

def mob_biomes(id):
    for loc in spawn_locations:
        if loc['enabled'] and loc['name'] == id:
            if not loc['requiredGlobalKey'] and not loc['requiredEnvironments']:
                return loc['biome']
    return None

def icon_path(item_id):
    path = f"../../{ICON_DIR}/{item_id}.png"
    if os.path.exists(f"{ICON_DIR}/{item_id}.png"):
        return path
    return None

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

def fmt_number(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    return str(value)

def render_item_description(item):
    description = item.get("description", "")
    if not description:
        return ""
    return section("Description", f"<div style='color:#ccc;line-height:1.5'>{description}</div>")

def render_food_details(item):
    food_keys = [
        ("Health", "food"),
        ("Stamina", "foodStamina"),
        ("Eitr", "foodEitr"),
        ("Duration", "foodBurnTime"),
        ("Regen", "foodRegen"),
    ]

    rows = ""
    for label, key in food_keys:
        if key in item:
            rows += f"<tr><th>{label}</th><td>{fmt_number(item.get(key))}</td></tr>"

    if not rows:
        return ""

    #if "isDrink" in item:
    #    rows += f"<tr><th>Drink</th><td>{'Yes' if item.get('isDrink') else 'No'}</td></tr>"

    return section("Food", f"""
<table class="info-table">
  {rows}
</table>
""")

def small_icon(item_id, size=24):
    icon = icon_path(item_id)
    if not icon:
        return ""
    return f'<img src="{icon}" style="width:{size}px;height:{size}px;object-fit:contain;border-radius:4px">'

def crafting_station_icon_path(station):
    path = f"../../{ICON_DIR}/craftingStation/{station}.png"
    if os.path.exists(f"{ICON_DIR}/craftingStation/{station}.png"):
        return path
    return None

def crafting_station_icon(station, size=22):
    icon = crafting_station_icon_path(station)
    if not icon:
        return ""
    return f'<img src="{icon}" style="width:{size}px;height:{size}px;object-fit:contain;border-radius:4px">'

def render_recipe_station(recipe):
    station = recipe.get("craftingStation", "")
    min_level = recipe.get("minStationLevel")

    if not station:
        return ""

    station_text = station
    station_icon = crafting_station_icon(station, 22)
    level_text = f"Lv {fmt_number(min_level)}" if min_level is not None else ""

    return f"""
<div style="display:flex;align-items:center;gap:6px;color:#999;font-size:13px">
  {station_icon}
  <span>{station_text}</span>
  <span style="color:#666">{level_text}</span>
</div>
"""

def render_recipes(item):
    item_id = item['id']
    recipe_body = ""

    for recipe in recipes:
        if recipe["result"] != item_id:
            continue

        result_icon = small_icon(item_id, 36)

        recipe_body += f"""
<div style="margin-bottom:12px">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap">
    <div style="display:flex;align-items:center;gap:10px">
      {result_icon}
      <b style="color:#ddd">{item_name(item_id)} × {recipe['amount']}</b>
    </div>
    {render_recipe_station(recipe)}
  </div>
</div>
"""

        for req in recipe["requirements"]:
            if isinstance(req, str):
                icon2 = icon_path(req)
                recipe_body += link_item(
                    f"{req}.html",
                    icon2,
                    item_name(req)
                )
            else:
                icon2 = icon_path(req["item"])
                req_amount = req.get("amount", req.get("count", 0))
                recipe_body += link_item(
                    f"{req['item']}.html",
                    icon2,
                    f"{item_name(req['item'])} × {req_amount}"
                )

    if recipe_body:
        return section("Recipe", recipe_body)
    else:
        return section("Recipe", "<div style='color:#777'>No recipe</div>")

def item_durability_at_quality(item, quality):
    return item.get("maxDurability", 0) + item.get("durabilityPerLevel", 0) * (quality - 1)

def item_damage_at_quality(item, quality):
    damages = item.get("damages", {})
    damages_per_level = item.get("damagesPerLevel", {})
    return {
        damage_type: damages.get(damage_type, 0) + damages_per_level.get(damage_type, 0) * (quality - 1)
        for damage_type in DAMAGE_TYPES
    }

def non_zero_damage_types(item):
    types = []
    max_quality = int(item.get("maxQuality", 1) or 1)
    for damage_type in DAMAGE_TYPES:
        for quality in range(1, max_quality + 1):
            if item_damage_at_quality(item, quality).get(damage_type, 0):
                types.append(damage_type)
                break
    return types

def item_recipe(item_id):
    for recipe in recipes:
        if recipe.get("result") == item_id:
            return recipe
    return None

def recipe_requirement_amount(req, quality):
    if isinstance(req, str):
        return 1
    if quality <= 1:
        return req.get("amount", req.get("count", 0))
    return req.get("amountPerLevel", 0)

def recipe_station_level(recipe, quality):
    if not recipe:
        return ""
    min_station_level = recipe.get("minStationLevel")
    if min_station_level is None:
        return ""
    return min_station_level + quality - 1

def render_damage_table(item):
    damage_types = non_zero_damage_types(item)
    if not damage_types:
        return ""

    base_damage = item_damage_at_quality(item, 1)
    rows = "".join(
        f"<tr><th>{damage_type}</th><td>{fmt_number(base_damage[damage_type])}</td></tr>"
        for damage_type in damage_types
    )
    total = sum(base_damage[damage_type] for damage_type in damage_types)

    return f"""
<h3 style="margin:14px 0 6px;font-size:15px;color:#ddd">Weapon Damage</h3>
<table class="info-table">
  <tr><th>Total</th><td>{fmt_number(total)}</td></tr>
  {rows}
</table>
"""

def render_upgrade_table(item):
    max_quality = int(item.get("maxQuality", 1) or 1)
    if max_quality <= 1:
        return ""

    item_type = item.get("type", "")
    recipe = item_recipe(item.get("id"))
    if item_type in WEAPON_TYPES:
        damage_types = non_zero_damage_types(item)
        if not damage_types:
            return ""

        header = "".join(f"<th>{damage_type}</th>" for damage_type in damage_types)
        rows = ""
        for quality in range(1, max_quality + 1):
            damages = item_damage_at_quality(item, quality)
            total = sum(damages[damage_type] for damage_type in damage_types)
            cells = "".join(f"<td>{fmt_number(damages[damage_type])}</td>" for damage_type in damage_types)
            rows += (
                f"<tr><th>{quality}</th>"
                f"<td>{fmt_number(item_durability_at_quality(item, quality))}</td>"
                f"<td>{fmt_number(recipe_station_level(recipe, quality))}</td>"
                f"<td>{fmt_number(total)}</td>{cells}</tr>"
            )

        return f"""
<h3 style="margin:14px 0 6px;font-size:15px;color:#ddd">Upgrade</h3>
<table class="info-table">
  <tr><th>Quality</th><th>Durability</th><th>Workbench Level</th><th>Total Damage</th>{header}</tr>
  {rows}
</table>
"""

    if item_type in ARMOR_TYPES:
        armor = item.get("armor", 0)
        armor_per_level = item.get("armorPerLevel", 0)
        rows = ""
        for quality in range(1, max_quality + 1):
            rows += (
                f"<tr><th>{quality}</th>"
                f"<td>{fmt_number(item_durability_at_quality(item, quality))}</td>"
                f"<td>{fmt_number(recipe_station_level(recipe, quality))}</td>"
                f"<td>{fmt_number(armor + armor_per_level * (quality - 1))}</td></tr>"
            )

        return f"""
<h3 style="margin:14px 0 6px;font-size:15px;color:#ddd">Upgrade</h3>
<table class="info-table">
  <tr><th>Quality</th><th>Durability</th><th>Workbench Level</th><th>Armor</th></tr>
  {rows}
</table>
"""

    return ""

def render_recipe_upgrade_table(item):
    recipe = item_recipe(item.get("id"))
    if not recipe:
        return ""

    requirements = recipe.get("requirements", [])
    if not requirements:
        return ""

    max_quality = int(item.get("maxQuality", 1) or 1)
    header = "".join(
        f"<th>{item_name(req) if isinstance(req, str) else item_name(req.get('item', ''))}</th>"
        for req in requirements
    )
    rows = ""
    for quality in range(1, max_quality + 1):
        cells = "".join(
            f"<td>{fmt_number(recipe_requirement_amount(req, quality))}</td>"
            for req in requirements
        )
        rows += (
            f"<tr><th>{quality}</th>"
            f"<td>{fmt_number(recipe_station_level(recipe, quality))}</td>"
            f"{cells}</tr>"
        )

    station = recipe.get("craftingStation", "")
    station_row = ""
    if station:
        station_row = f"""
<table class="info-table">
  <tr><th>Crafting Station</th><td>{station}</td></tr>
</table>
"""

    return f"""
<h3 style="margin:14px 0 6px;font-size:15px;color:#ddd">Recipe</h3>
{station_row}
<table class="info-table">
  <tr><th>Quality</th><th>Workbench Level</th>{header}</tr>
  {rows}
</table>
"""

def render_equipment_details(item):
    item_type = item.get("type", "")
    if item_type not in WEAPON_TYPES and item_type not in ARMOR_TYPES and item_type not in AMMO_TYPES:
        return ""
    
    weapon_type = None
    if item_type in WEAPON_TYPES:
        weapon_type = item.get("skillType", "")
    elif item_type in AMMO_TYPES:
        weapon_type = item.get("ammoType", "")
    if weapon_type:
        label = "Ammo Type" if item_type in AMMO_TYPES else "Weapon Type"
        weapon_type = f"""<tr><th>{label}</th><td>{weapon_type}</td></tr>"""
    
    recipe = item_recipe(item.get("id"))
    if recipe:
        crafting_station = recipe.get('craftingStation', 'None')
    else:
        crafting_station = 'None'
    
    if "maxDurability" in item:
        durability = f"""
<tr><th>Durability</th><td>{fmt_number(item.get("maxDurability", 0))}</td></tr>
<tr><th>Durability Per Level</th><td>{fmt_number(item.get("durabilityPerLevel", 0))}</td></tr>
"""
    else:
        durability = ""
    
    details = f"""
<table class="info-table">
  <tr><th>Internal ID</th><td>{item.get("id", "")}</td></tr>
  <tr><th>Type</th><td>{item_type}</td></tr>
  {weapon_type}
  <tr><th>Source</th><td>{crafting_station}</td></tr>
  {durability}
</table>
"""

    if item_type in WEAPON_TYPES or item_type in AMMO_TYPES:
        details += render_damage_table(item)
    elif item_type in ARMOR_TYPES:
        details += f"""
<table class="info-table">
  <tr><th>Armor</th><td>{fmt_number(item.get("armor", 0))}</td></tr>
  <tr><th>Armor Per Level</th><td>{fmt_number(item.get("armorPerLevel", 0))}</td></tr>
</table>
"""

    details += render_upgrade_table(item)
    details += render_recipe_upgrade_table(item)
    return section("Details", details)

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

def item_card(item_id, item):
    img = f'<img src="../../{ICON_DIR}/{item_id}.png" width="64"><br>'
    return f"""
    <div style="width:110px;text-align:center;margin:6px">
    <a href="{item_id}.html" style="color:white;text-decoration:none">
        {img}
        <div style="font-size:12px">{item["name"]}</div>
    </a>
    </div>
    """

def breadcrumb(path):
    return f"""
<div class="breadcrumb">
  {' <span style="opacity:0.5">›</span> '.join(path)}
</div>
"""

def page_template(title, body, style=''):
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>

* {{
  box-sizing: border-box;
}}

body {{
  margin: 0;
  display: flex;
  font-family: sans-serif;
  background: #111;
  color: #eee;
}}

.sidebar {{
  position: fixed;
  left: 0;
  top: 0;
  width: 220px;
  height: 100vh;
  background: #1a1a1a;
  padding: 12px;
  border-right: 1px solid #333;
  overflow-y: auto;
}}

.breadcrumb {{
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 13px;
  color: #888;
  margin-bottom: 10px;
  line-height: 1;   /* ←これ重要 */
}}
.breadcrumb a {{
  display: inline;   /* ←これ超重要 */
  color: #888;
  text-decoration: none;
}}

.content {{
  flex: 1;
  padding: 16px;
  margin-left: 220px;
}}

a {{
  color: #ccc;
  text-decoration: none;
  display: block;
  padding: 6px 8px;
  border-radius: 6px;
}}

a:hover {{
  background: #2a2a2a;
}}

.section-title {{
  margin-top: 14px;
  font-size: 12px;
  color: #777;
}}

.info-table, .resist-table {{
    border-collapse: collapse;
    margin: 10px 0;
}}

.info-table th, .info-table td,
.resist-table th, .resist-table td {{
    border: 1px solid #444;
    padding: 6px 10px;
}}

.info-table th {{
    background: #222;
    text-align: left;
}}

.resist-table th {{
    background: #333;
}}

.drop-table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 10px;
}}

.drop-table th, .drop-table td {{
    border: 1px solid #444;
    padding: 6px 10px;
}}

.drop-table th {{
    background: #222;
}}

.item-icon {{
    height: 1.8em;
    vertical-align: middle;
    margin-right: 6px;
}}

.drop-chance {{
    position: relative;
    background: #222;
    height: 14px;
    border-radius: 4px;
}}

.drop-chance .bar {{
    background: #4caf50;
    height: 100%;
    border-radius: 4px;
}}

.drop-chance span {{
    position: absolute;
    left: 6px;
    top: -2px;
    font-size: 12px;
}}

.mob-grid {{
    display: flex;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin-top: 10px;
}}

.mob-card {{
    display: block;
    background: #1b1b1b;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    text-decoration: none;
    color: #ddd;
    position: relative;
    transition: 0.2s;
}}

.mob-card:hover {{
    background: #2a2a2a;
    transform: translateY(-2px);
}}

.mob-icon {{
    height: 64px;
    margin-bottom: 6px;
}}

.mob-name {{
    font-weight: bold;
    margin-bottom: 4px;
}}

.mob-hp {{
    font-size: 0.9em;
    color: #aaa;
}}

.boss-tag {{
    position: absolute;
    top: 6px;
    left: 6px;
    background: #c33;
    color: white;
    font-size: 0.7em;
    padding: 2px 6px;
    border-radius: 4px;
}}

{style}
</style>
</head>
<body>
{body}
</body>
</html>
"""

def side_bar(base_path="./"):
    return f"""
<div class="sidebar">

  <h3>Wiki</h3>

  <a href="{base_path}index.html">🏠 Home</a>
  <a href="{base_path}items/index.html">📦 Items</a>
  <a href="{base_path}mobs/index.html">👹 Mobs</a>

  <div class="section-title">Categories</div>

  <a href="{base_path}items/index.html#Weapon">⚔ Weapon</a>
  <a href="{base_path}items/index.html#Armor">🛡 Armor</a>
  <a href="{base_path}items/index.html#Consumable">🍖 Consumable</a>
  <a href="{base_path}items/index.html#Material">🪵 Material</a>

  <div class="section-title">Search</div>

  <input id="search" placeholder="Search..." style="
  width:100%;
  padding:5px 8px;
  margin-top:6px;
  border-radius:6px;
  border:1px solid #2a2a2a;
  background:#0f0f0f;
  color:#ddd;
  font-size:13px;
  outline:none;
  ">

</div>
    """

def section(title, body):
    return f"""
<div style="
  margin-top:28px;
  padding:12px;
  border-radius:10px;
  background:#1a1a1a;
  border:1px solid #333;
">
  <h2 style="
    margin:0 0 12px 0;
    font-size:18px;
    color:#ddd;
    border-bottom:1px solid #333;
    padding-bottom:6px;
  ">{title}</h2>
  {body}
</div>
"""

def link_item(url, icon, text):
    img = f'<img src="{icon}" style="height:2.2em;vertical-align:middle;margin-right:8px;border-radius:4px;">' if icon else ""
    return f"""
<a href="{url}" style="
  display:flex;
  align-items:center;
  padding:6px 8px;
  border-radius:6px;
  text-decoration:none;
  color:#eee;
  transition:0.15s;
" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
  {img}
  <span>{text}</span>
</a>
"""

# ===== reverse index =====
crafted_from = {}
for r in recipes:
    for req in r["requirements"]:
        if isinstance(req, str):
            # smelter
            crafted_from.setdefault(req, []).append(r["result"])
        else:
            crafted_from.setdefault(req["item"], []).append(r["result"])

dropped_by = {}
for mob_id, drops in drops.items():
    for d in drops:
        dropped_by.setdefault(d["item"], []).append(mob_id)

# ===== item pages =====
for item_id, item in items.items():
    name = item["name"]

    html = side_bar("../")
    html += r"""<div class="content">"""

    html += breadcrumb([
        '<a href="../index.html" style="color:#888">Home</a>',
        '<a href="index.html" style="color:#888">Items</a>',
        f'<a href="index.html#{item["type"]}" style="color:#888">{item["type"]}</a>',
        item["name"]
    ])

    icon = icon_path(item_id)
    title_icon = ""
    if icon:
        title_icon = f'<img src="{icon}" style="width:48px;height:48px;object-fit:contain;border-radius:6px">'

    html += f"""
<h1 style="margin-bottom:8px">{name}</h1>

<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
  {title_icon}
  <div style="color:#aaa;font-size:14px;line-height:1.5">
    <div><b style="color:#ddd">ID:</b> {item_id}</div>
    <div><b style="color:#ddd">Type:</b> {item["type"]}</div>
  </div>
</div>
"""

    html += render_item_description(item)
    html += render_food_details(item)

    # ===== Recipe =====
    html += render_recipes(item)

    # === Details ===
    html += render_equipment_details(item)

    # ===== Crafted into =====
    crafted_body = ""

    for out in crafted_from.get(item_id, []):
        icon2 = icon_path(out)
        crafted_body += link_item(
            f"{out}.html",
            icon2,
            item_name(out)
        )

    html += section("Crafted into", crafted_body or "<div style='color:#777'>None</div>")

    # ===== Drops =====
    drops_body = ""

    for mob in dropped_by.get(item_id, []):
        drops_body += f"""
<a href="../mobs/{mob}.html" style="
  display:block;
  padding:6px 8px;
  border-radius:6px;
  color:#eee;
  text-decoration:none;
" onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
  {mob_name(mob)}
</a>
"""

    html += section("Dropped by", drops_body or "<div style='color:#777'>None</div>")

    # end of content
    html += r"""</div>"""

    with open(f"{SITE_DIR}/items/{item_id}.html", "w", encoding="utf-8") as f:
        f.write(page_template(name, html))

# ===== mob pages =====
for mob_id, mob in mobs.items():

    html = side_bar('../')
    html += r"""<div class="content">"""

    html += breadcrumb([
        '<a href="../index.html" style="color:#888">Home</a>',
        '<a href="index.html" style="color:#888">Mobs</a>',
        mob['name']
    ])

    html += f"<h1>{mob['name']}</h1>"

    # ========================
    # 基本情報
    # ========================
    html += "<h2>基本情報</h2>"
    html += '<table class="info-table">'

    biomes = mob_biomes(mob['id'])
    if biomes:
        html += f"<tr><th>バイオーム</th><td>{', '.join(biomes)}</td></tr>"
    else:
        pass
    html += f"<tr><th>HP</th><td>{mob.get('hp','-')}</td></tr>"
    html += f"<tr><th>派閥</th><td>{mob.get('faction','-')}</td></tr>"
    html += f"<tr><th>ボス</th><td>{'Yes' if mob.get('boss') else 'No'}</td></tr>"
    html += f"<tr><th>テイム可能</th><td>{'Yes' if mob.get('tameable') else 'No'}</td></tr>"

    html += "</table>"

    # ========================
    # 耐性
    # ========================
    if "damageModifiers" in mob:
        html += "<h2>耐性</h2>"
        html += '<table class="resist-table">'
        html += "<tr><th>属性</th><th>効果</th></tr>"

        for dmg, val in mob["damageModifiers"].items():
            html += f"<tr><td>{dmg}</td><td>{val}</td></tr>"

        html += "</table>"

    # ========================
    # ドロップ
    # ========================
    if mob_id in drops:
        html += "<h2>ドロップ</h2><ul>"
        html += '<table class="drop-table">'
        html += "<tr><th>アイテム</th><th>数量</th><th>確率</th></tr>"

        for d in drops[mob_id]:
            item = d["item"]
            icon = icon_path(item)

            img = f'<img src="{icon}" class="item-icon">' if icon else ""
            name = f'<a href="../items/{item}.html">{item_name(item)}</a>'

            # 数量
            min_stack = d.get("min", 1)
            max_stack = d.get("max", 1)
            stack_text = f"{min_stack}" if min_stack == max_stack else f"{min_stack}–{max_stack}"

            # 確率
            chance = d.get("chance", 1.0)
            percent = int(chance * 100)

            html += f"""
            <tr>
                <td>{img} {name}</td>
                <td>{stack_text}</td>
                <td>
                    <div class="drop-chance">
                        <div class="bar" style="width:{percent}%"></div>
                        <span>{percent}%</span>
                    </div>
                </td>
            </tr>
            """

        html += "</table>"

    html += "</div>"

    with open(f"{SITE_DIR}/mobs/{mob['id']}.html", "w", encoding="utf-8") as f:
        f.write(page_template(mob["id"], html))

# ===== index =====
def item_index():
    html = side_bar('../')
    html += r"""<div class="content">"""
    html += breadcrumb([
        '<a href="../index.html" style="color:#888">Home</a>',
        '<a href="index.html" style="color:#888">Items</a>'
    ])

    html += "<h1>Items</h1>"

    grouped = defaultdict(list)
    for item_id, item in items.items():
        icon = icon_path(item_id)
        if not icon:
            continue
        grouped[item_category(item)].append((item_id, item))

    for category in sorted(grouped.keys(), key=category_sort_key):
        html += f"""
    <h2 id="{category}" style="width:100%;margin-top:24px;border-bottom:1px solid #444;padding-bottom:4px">
    {category}
    </h2>
"""

        category_items = grouped[category]

        if category == "Ammo":
            ammo_by_type = defaultdict(list)
            for item_id, item in category_items:
                ammo_by_type[ammo_group(item)].append((item_id, item))

            for ammo_type in sorted(ammo_by_type.keys(), key=skill_type_sort_key):
                html += f"""
    <h3 id="Ammo-{ammo_type}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
    {ammo_type}
    </h3>
    <div style="display:flex;flex-wrap:wrap">
"""
                for item_id, item in ammo_by_type[ammo_type]:
                    html += item_card(item_id, item)
                html += "</div>"
        elif category == "Weapon":
            weapons_by_skill = defaultdict(list)
            for item_id, item in category_items:
                weapons_by_skill[weapon_group(item)].append((item_id, item))

            for skill_type in sorted(weapons_by_skill.keys(), key=skill_type_sort_key):
                html += f"""
    <h3 id="Weapon-{skill_type}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
    {skill_type}
    </h3>
    <div style="display:flex;flex-wrap:wrap">
"""
                for item_id, item in weapons_by_skill[skill_type]:
                    html += item_card(item_id, item)
                html += "</div>"
        elif category == "Material":
            materials_by_group = defaultdict(list)
            for item_id, item in category_items:
                materials_by_group[material_group(item)].append((item_id, item))

            for material_type in sorted(materials_by_group.keys(), key=material_group_sort_key):
                html += f"""
    <h3 id="Material-{material_type}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
    {material_type}
    </h3>
    <div style="display:flex;flex-wrap:wrap">
"""
                material_items = materials_by_group[material_type]
                if material_type == "Food":
                    material_items = sorted(material_items, key=food_sort_key)
                for item_id, item in material_items:
                    html += item_card(item_id, item)
                html += "</div>"
        elif category == "Consumable":
            consumables_by_group = defaultdict(list)
            for item_id, item in category_items:
                consumables_by_group[consumable_group(item)].append((item_id, item))

            for consumable_type in sorted(consumables_by_group.keys(), key=consumable_group_sort_key):
                html += f"""
    <h3 id="Consumable-{consumable_type}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
    {consumable_type}
    </h3>
    <div style="display:flex;flex-wrap:wrap">
"""
                for item_id, item in sorted(consumables_by_group[consumable_type], key=food_sort_key):
                    html += item_card(item_id, item)
                html += "</div>"
        elif category == "Trophy":
            # sort by biome and hp
            type_groups = defaultdict(list)
            for item_id, item in category_items:
                type_groups[item.get("type", "Unknown")].append((item_id, item))

            for item_type in sorted(type_groups.keys()):
                if len(type_groups) > 1:
                    html += f"""
                    <h3 id="{category}-{item_type}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
                    {item_type}
                    </h3>
                    """

                # mob_id = find_mob_by_drop_id(item_id)
                def find_mob_by_drop_id(item_id):
                    _mobs = dropped_by.get(item_id, [])
                    for mob in _mobs:
                        return mobs.get(mob)
                def aaa(item_id):
                    mob = find_mob_by_drop_id(item_id[0])
                    if mob:
                        return mob.get('hp')
                    return 0

                biome_groups = defaultdict(list)
                for item_id, item in sorted(type_groups[item_type], key=aaa):
                    mob = find_mob_by_drop_id(item_id)
                    if not mob:
                        continue
                    biome = mob_biomes(mob['id'])
                    if biome:
                        def easiest_biome(biomes):
                            for b in BIOME_ORDER:
                                if b in biomes:
                                    return b
                            return 'Unknown'
                        biome_groups[easiest_biome(biome)].append((item_id, item))
                    else:
                        biome_groups['Unknown'].append((item_id, item))

                sorted_dict = {k: biome_groups[k] for k in BIOME_ORDER if k in biome_groups}

                for biome, _items in sorted_dict.items():
                    html += f"""
                        <h3 id="Trophy-{biome}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
                        {biome}
                        </h3>
                    
                    """
                    html += '<div style="display:flex;flex-wrap:wrap">'
                    for item_id, item in _items:
                        html += item_card(item_id, item)
                    html += "</div>"

        else:
            type_groups = defaultdict(list)
            for item_id, item in category_items:
                type_groups[item.get("type", "Unknown")].append((item_id, item))

            for item_type in sorted(type_groups.keys()):
                if len(type_groups) > 1:
                    html += f"""
    <h3 id="{category}-{item_type}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
    {item_type}
    </h3>
"""
                html += '<div style="display:flex;flex-wrap:wrap">'
                for item_id, item in type_groups[item_type]:
                    html += item_card(item_id, item)
                html += "</div>"


    # end of content
    html += r"""</div>"""

    with open(f"{SITE_DIR}/items/index.html", "w", encoding="utf-8") as f:
        f.write(page_template("Items", html))

# ===== index =====
# ========================
# 描画関数
# ========================
def spawn_time_tags(entry):
    spawn_at_day = entry.get("spawnAtDay")
    spawn_at_night = entry.get("spawnAtNight")
    tags = []

    if spawn_at_day is True and spawn_at_night is True:
        tags.append("Day/Night")
    elif spawn_at_day is True:
        tags.append("Day")
    elif spawn_at_night is True:
        tags.append("Night")

    if entry["mob"].get("tameable"):
        tags.append("Tameable")

    return "".join(f'<span class="spawn-tag">{tag}</span>' for tag in tags)

def mob_card(entry):
    mob = entry["mob"]
    name = mob["name"]
    mob_id = mob["id"]

    icon = icon_path(mob_id)
    img = f'<img src="{icon}" class="mob-icon">' if icon else '<div class="mob-icon placeholder"></div>'

    hp = mob.get("hp", "-")
    boss = mob.get("boss", False)

    boss_tag = '<div class="boss-tag">BOSS</div>' if boss else ""
    time_tags = spawn_time_tags(entry)

    return f"""
            <a href="{mob_id}.html" class="mob-card">
                {boss_tag}
                {img}
                <div class="mob-name">{mob_name(name)}</div>
                <div class="mob-hp">HP: {hp}</div>
                <div class="spawn-tags">{time_tags}</div>
            </a>
            """

def render_mob_grid(entries):
    out = '<div class="mob-grid">'
    group_sorted = sorted(entries, key=lambda e: e["mob"].get("hp", 0), reverse=False)
    for entry in group_sorted:
        out += mob_card(entry)
    out += "</div>"
    return out

def condition_values(value):
    if not value:
        return []
    if isinstance(value, list):
        return [v for v in value if v]
    return [value]

def render_conditioned_mobs(entries):
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

    out = ""
    if normal:
        out += render_mob_grid(normal)

    if required_env:
        out += f"<h4>Conditional Spawn</h4>"
        out += render_mob_grid(required_env)

    return out

def render_group(title, groups):

    out = f"<h2>{title}</h2>"

    for biome in BIOME_ORDER:
        if biome not in groups:
            continue
        out += f"<h3>{biome}</h3>"
        out += render_conditioned_mobs(groups[biome])

    return out

def mob_index():
    html = side_bar('../')
    html += r"""<div class="content mob-page">"""
    html += breadcrumb([
        '<a href="../index.html" style="color:#888">Home</a>',
        'Mobs'
    ])
    html += "<h1>Mobs</h1>"

    # ========================
    # グループ分け
    # ========================
    boss_groups = defaultdict(list)
    mob_groups = defaultdict(list)
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
            }
            if mob.get("boss"):
                boss_groups[b].append(entry)
            else:
                mob_groups[b].append(entry)

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
            mob_groups["Unknown"].append(entry)

    html += render_group("Mobs", mob_groups)
    html += render_group("Bosses", boss_groups)
    html += "</div>"

    with open(f"{SITE_DIR}/mobs/index.html", "w", encoding="utf-8") as f:
        f.write(page_template("Mobs", html, r"""
/* =========================
   見出し
========================= */
.mob-page h1 {
    margin-bottom: 10px;
}

.mob-page h2 {
    margin-top: 30px;
    border-bottom: 2px solid #333;
    padding-bottom: 5px;
}

.mob-page h3 {
    margin-top: 20px;
    border-bottom: 1px solid #333;
    padding-bottom: 4px;
}

.mob-page h4 {
    margin: 16px 0 6px;
    color: #aaa;
    font-size: 14px;
    font-weight: 600;
}

/* =========================
   Mob一覧（グリッド）
========================= */
.mob-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 10px;
}

.mob-card {
    display: block;
    width: 140px;
    background: #1b1b1b;
    border: 1px solid #333;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    text-decoration: none;
    color: #ddd;
    position: relative;
    transition: 0.2s;
}

.mob-card:hover {
    background: #2a2a2a;
    transform: translateY(-2px);
}

.mob-icon {
    height: 64px;
    margin-top: 10px;
    margin-bottom: 6px;
}

.mob-name {
    font-weight: bold;
    margin-bottom: 4px;
}

.mob-hp {
    font-size: 0.9em;
    color: #aaa;
}

.spawn-tags {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 3px;
    min-height: 18px;
    margin-top: 6px;
}

.spawn-tag {
    display: inline-block;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 1px 5px;
    color: #bbb;
    font-size: 11px;
    line-height: 1.3;
}

/* ボスタグ */
.boss-tag {
    position: absolute;
    top: 6px;
    right: 6px;
    background: #c33;
    color: white;
    font-size: 0.7em;
    padding: 2px 6px;
    border-radius: 4px;
}

/* =========================
   レスポンシブ
========================= */
@media (max-width: 600px) {
    .mob-card {
        width: 100px;
        padding: 6px;
    }

    .mob-icon {
        height: 48px;
    }
}
"""))

# ===== index =====
def home_index():
    html = side_bar()
    html += r"""<div class="content">"""
    html += breadcrumb([
        'Home',
    ])
    html += "</div>"
    with open(f"{SITE_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(page_template("Home", html))

item_index()
mob_index()
home_index()
print("done")
