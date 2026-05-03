import os
from collections import defaultdict

BIOME_ORDER = [
    "Meadows", "BlackForest", "Swamp",
    "Mountain", "Plains", "Mistlands",
    "AshLands", "DeepNorth", "Ocean", "Unknown"
]

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

def item_category(item):
    item_type = item.type
    if item_type in AMMO_TYPES:
        return "Ammo"
    if item_type in WEAPON_TYPES:
        return "Weapon"
    if item_type in ARMOR_TYPES:
        return "Armor"
    return item_type

def ammo_group(item):
    return item.ammoType

def weapon_group(item):
    return item.skillType

def food_group(item):
    eitr = item.foodEitr
    if eitr > 0:
        return "Eitr"
    
    food = item.food
    stamina = item.foodStamina
    if not food and not stamina:
        if item.isDrink:
            return "Drink"
        return "Misc"
    if food == stamina:
        return 'Balance'
    if food > stamina:
        return "Food"
    return "Stamina"

def material_group(database, item):
    # if smelter...
    if database.is_ore(item.id):
        return "Ore"
    elif database.is_ingot(item.id):
        return "Ingot"
    elif item.consumeStatusEffect:
        return "Consumable"
    elif item.food or item.foodStamina or item.foodEitr:
        return food_group(item)
    return "Drops"

def consumable_group(item):
    if item.isDrink is True:
        return "Drink"
    return food_group(item)

def trophy_group(item, database):
    for mob in database.dropped_by(item.id):
        biomes = database.get_mob_biomes(mob['id'])
        for i, b1 in enumerate(BIOME_ORDER):
            for b2 in biomes:
                if b1 == b2:
                    return b1
    return 'Unknown'

# sort key
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

def material_group_sort_key(group):
    preferred = ["Ore", "Ingot", "Food", "Stamina", "Eitr", "Consumable", "Drops"]
    if group in preferred:
        return (preferred.index(group), group)
    return (len(preferred), group)

def consumable_group_sort_key(group):
    preferred = ["Drink", "Food", "Stamina", "Eitr"]
    if group in preferred:
        return (preferred.index(group), group)
    return (len(preferred), group)

def trophy_sort_key(group):
    for i, b1 in enumerate(BIOME_ORDER):
        if b1 == group:
            return str(i)
    return str(99)

# helper (calculators)
def get_total_damage(item: dict):
    damages = item.damages
    if not damages:
        return 0
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

# helper (format)
def fmt_number(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    return str(value)


class DefaultGenerator:

    def __init__(self, localization, database):
        self.localization = localization
        self.database = database

    #
    def localize(self, name):
        return self.localization.localize(name)
    
    def item_name(self, item_id):
        return self.localize(self.database.item_name(item_id))

    # html components
    def side_bar(self, base_path="./"):
        return f"""
            <div class="sidebar">
            <h3>Wiki</h3>
            <a href="{base_path}index.html">🏠 Home</a>
            <a href="{base_path}items/index.html">📦 Items</a>
            <a href="{base_path}mobs/index.html">👹 Mobs</a>
            <a href="{base_path}traders/index.html">👤 Traders</a>
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

    def breadcrumb(self, path):
        return f"""
            <div class="breadcrumb">
            {' <span style="opacity:0.5">›</span> '.join(path)}
            </div>
        """

    def page_template(self, title, body, style=''):
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
    margin-left: 10px;
}}

.drop-table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 10px;
    margin-left: 10px;
}}

.drop-table th, .drop-table td,
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

    # item index
    def item_card(self, item_id, item):
        img = f'<img src="../../icons/{item_id}.png" width="64"><br>'
        return f"""
<div style="width:110px;text-align:center;margin:6px">
<a href="{item_id}.html" style="color:white;text-decoration:none">
    {img}
    <div style="font-size:12px">{self.localization.localize(item.name)}</div>
</a>
</div>
        """

    def icon_path(self, item_id):
        path = f"../../icons/{item_id}.png"
        if os.path.exists(f"icons/{item_id}.png"):
            return path
        return None

    def small_icon(self, item_id, size=24):
        icon = self.icon_path(item_id)
        if not icon:
            return ""
        return f'<img src="{icon}" style="width:{size}px;height:{size}px;object-fit:contain;border-radius:4px">'

    # pages
    def _section(self, title, body):
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

    def render_item_description(self, item):
        description = item.description
        if not description:
            return ""
        description = self.localization.localize(description)
        return self._section("Description", f"<div style='color:#ccc;line-height:1.5'>{description}</div>")

    def render_status_effect(self, item):
        html = ""
        effect = item.fullAdrenalineSE
        if not effect:
            effect = item.consumeStatusEffect
        if not effect:
            return ""

        def pct(v):
            return f"{v*100:+.0f}%"

        def flat(v):
            return f"{v:+.0f}"

        # ===== Duration =====
        if effect.get("ttl", 0) > 0:
            if item.maxAdrenaline:
                html += f'''
                <div style="color:#aaa;margin-bottom:10px">
                    Adrenaline: <span style="color:orange">{item.maxAdrenaline:.0f}</span>
                </div>
                '''
            html += f'''
            <div style="color:#aaa;margin-bottom:10px">
                Duration: <span style="color:orange">{effect["ttl"]:.0f}s</span>
            </div>
            '''

            # ===== Health =====
            health_lines = []
            if effect["healthUpFront"] != 0:
                health_lines.append(f"Health: <span style='color:orange'>{flat(effect['healthUpFront'])}</span>")
            if effect["healthOverTime"] != 0:
                health_lines.append(f"Health (over time): <span style='color:orange'>{flat(effect['healthOverTime'])}</span>")
            if effect["healthRegenMultiplier"] != 1:
                health_lines.append(f"Health Regen: <span style='color:orange'>{pct(effect['healthRegenMultiplier']-1)}</span>")

            if health_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(health_lines)}</div>"

            # ===== Stamina =====
            stamina_lines = []
            if effect["staminaUpFront"] != 0:
                stamina_lines.append(f"Stamina: <span style='color:orange'>{flat(effect['staminaUpFront'])}</span>")
            if effect["staminaOverTime"] != 0:
                stamina_lines.append(f"Stamina (over time): <span style='color:orange'>{flat(effect['staminaOverTime'])}</span>")
            if effect["staminaRegenMultiplier"] != 1:
                stamina_lines.append(f"Stamina Regen: <span style='color:orange'>{pct(effect['staminaRegenMultiplier']-1)}</span>")

            if stamina_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(stamina_lines)}</div>"

            # ===== Eitr =====
            eitr_lines = []
            if effect["eitrUpFront"] != 0:
                eitr_lines.append(f"Eitr: <span style='color:orange'>{flat(effect['eitrUpFront'])}</span>")
            if effect["eitrOverTime"] != 0:
                eitr_lines.append(f"Eitr (over time): <span style='color:orange'>{flat(effect['eitrOverTime'])}</span>")
            if effect["eitrRegenMultiplier"] != 1:
                eitr_lines.append(f"Eitr Regen: <span style='color:orange'>{pct(effect['eitrRegenMultiplier']-1)}</span>")

            if eitr_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(eitr_lines)}</div>"

            # ===== Combat / Defense =====
            combat_lines = []
            if effect["addArmor"] != 0:
                combat_lines.append(f"Armor: <span style='color:orange'>{flat(effect['addArmor'])}</span>")
            if effect["armorMultiplier"] != 0:
                combat_lines.append(f"Armor Multiplier: <span style='color:orange'>{pct(effect['armorMultiplier'])}</span>")
            if effect["staggerModifier"] != 0:
                combat_lines.append(f"Stagger: <span style='color:orange'>{pct(-effect['staggerModifier'])}</span>")
            if effect["timedBlockBonus"] != 0:
                combat_lines.append(f"Parry Bonus: <span style='color:orange'>{pct(effect['timedBlockBonus'])}</span>")

            if combat_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(combat_lines)}</div>"

            # ===== Movement =====
            move_lines = []
            if effect["speedModifier"] != 0:
                move_lines.append(f"Speed: <span style='color:orange'>{pct(effect['speedModifier'])}</span>")
            if effect["swimSpeedModifier"] != 0:
                move_lines.append(f"Swim Speed: <span style='color:orange'>{pct(effect['swimSpeedModifier'])}</span>")
            if effect["runStaminaDrainModifier"] != 0:
                move_lines.append(f"Run Stamina Drain: <span style='color:orange'>{pct(effect['runStaminaDrainModifier'])}</span>")

            # jump
            j = effect["jumpModifier"]
            if j["y"] not in (0, 1):
                move_lines.append(f"Jump Height: <span style='color:orange'>{pct(j['y'])}</span>")
            if max(j["x"], j["z"]) != 0:
                move_lines.append(f"Jump Distance: <span style='color:orange'>{pct(max(j['x'], j['z']))}</span>")

            if move_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(move_lines)}</div>"

            # ===== Stamina Usage =====
            usage_lines = []
            if effect["attackStaminaUseModifier"] != 0:
                usage_lines.append(f"Attack Stamina: <span style='color:orange'>{pct(effect['attackStaminaUseModifier'])}</span>")
            if effect["blockStaminaUseModifier"] != 0:
                usage_lines.append(f"Block Stamina: <span style='color:orange'>{pct(effect['blockStaminaUseModifier'])}</span>")
            if effect["blockStaminaUseFlatValue"] != 0:
                usage_lines.append(f"Block Stamina (flat): <span style='color:orange'>{flat(effect['blockStaminaUseFlatValue'])}</span>")
            if effect["dodgeStaminaUseModifier"] != 0:
                usage_lines.append(f"Dodge Stamina: <span style='color:orange'>{pct(effect['dodgeStaminaUseModifier'])}</span>")
            if effect["runStaminaUseModifier"] != 0:
                usage_lines.append(f"Run Stamina: <span style='color:orange'>{pct(effect['runStaminaUseModifier'])}</span>")
            if effect["jumpStaminaUseModifier"] != 0:
                usage_lines.append(f"Jump Stamina: <span style='color:orange'>{pct(effect['jumpStaminaUseModifier'])}</span>")
            if effect["swimStaminaUseModifier"] != 0:
                usage_lines.append(f"Swim Stamina: <span style='color:orange'>{pct(effect['swimStaminaUseModifier'])}</span>")
            if effect["sneakStaminaUseModifier"] != 0:
                usage_lines.append(f"Sneak Stamina: <span style='color:orange'>{pct(effect['sneakStaminaUseModifier'])}</span>")

            if usage_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(usage_lines)}</div>"

            # ===== Utility =====
            util_lines = []
            if effect["noiseModifier"] != 0:
                util_lines.append(f"Noise: <span style='color:orange'>{pct(effect['noiseModifier'])}</span>")
            if effect["stealthModifier"] != 0:
                util_lines.append(f"Stealth: <span style='color:orange'>{pct(effect['stealthModifier'])}</span>")
            if effect["fallDamageModifier"] != 0:
                util_lines.append(f"Fall Damage: <span style='color:orange'>{pct(effect['fallDamageModifier'])}</span>")
            if effect["maxMaxFallSpeed"] != 0:
                util_lines.append(f"Max Fall Speed: <span style='color:orange'>{flat(effect['maxMaxFallSpeed'])}</span>")
            if effect["addMaxCarryWeight"] != 0:
                util_lines.append(f"Carry Weight: <span style='color:orange'>{flat(effect['addMaxCarryWeight'])}</span>")

            if util_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(util_lines)}</div>"

            # ===== Adrenaline =====
            adr_lines = []
            if effect["adrenalineUpFront"] != 0:
                adr_lines.append(f"Adrenaline: <span style='color:orange'>{flat(effect['adrenalineUpFront'])}</span>")
            if effect["adrenalineModifier"] != 0:
                adr_lines.append(f"Adrenaline Gain: <span style='color:orange'>{pct(effect['adrenalineModifier'])}</span>")

            if adr_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(adr_lines)}</div>"

            # ===== Skills =====
            if effect["skillLevel"] and effect["skillLevelModifier"] != 0:
                html += f"""
                <div style="margin-bottom:10px">
                    <div>{effect["skillLevel"]} Skill: <span style="color:orange">{flat(effect["skillLevelModifier"])}</span></div>
                </div>
                """

            # ===== Damage Modifiers(Take) =====
            dmg_lines = []
            for mod in effect["mods"]:
                dmg_lines.append(f"{mod['type']}: <span style='color:orange'>{mod['modifier']}</span>")

            # ===== Damage Modifiers =====
            for k, v in effect["percentigeDamageModifiers"].items():
                if v != 0:
                    name = k.replace("m_", "").capitalize()
                    dmg_lines.append(f"{name}: <span style='color:orange'>{pct(v)}</span>")

            if dmg_lines:
                html += f"<div style='margin-bottom:10px'>{'<br>'.join(dmg_lines)}</div>"

            return self._section('Status Effect', f"""
            <div style='color:#ccc;line-height:1.5'>
                {html if html else "<div style='color:#777'>No effects</div>"}
            </div>
            """)

    def render_food_details(self, item):
        food_keys = [
            ("Health", item.food),
            ("Stamina", item.foodStamina),
            ("Eitr", item.foodEitr),
            ("Duration", item.foodBurnTime),
            ("Regen", item.foodRegen),
        ]

        rows = ""
        for label, value in food_keys:
            if value:
                rows += f"<tr><th>{label}</th><td>{fmt_number(value)}</td></tr>"

        if not rows:
            return ""

        #if "isDrink" in item:
        #    rows += f"<tr><th>Drink</th><td>{'Yes' if item.get('isDrink') else 'No'}</td></tr>"

        return self._section("Food", f"""
    <table class="info-table">
    {rows}
    </table>
    """)

    def crafting_station_icon_path(self, station):
        path = f"../../icons/craftingStation/{station}.png"
        if os.path.exists(f"icons/craftingStation/{station}.png"):
            return path
        return None

    def crafting_station_icon(self, station, size=22):
        icon = self.crafting_station_icon_path(station)
        if not icon:
            return ""
        return f'<img src="{icon}" style="width:{size}px;height:{size}px;object-fit:contain;border-radius:4px">'

    def render_recipe_station(self, recipe):
        station = recipe.get("craftingStation", "")
        min_level = recipe.get("minStationLevel")

        if not station:
            return ""

        station_text = self.localize(station)
        station_icon = self.crafting_station_icon(station, 22)
        level_text = f"Lv {fmt_number(min_level)}" if min_level is not None else ""

        return f"""
    <div style="display:flex;align-items:center;gap:6px;color:#999;font-size:13px">
    {station_icon}
    <span>{station_text}</span>
    <span style="color:#666">{level_text}</span>
    </div>
    """

    def link_item(self, url, icon, text):
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

    def render_recipes(self, item):
        item_id = item.id
        recipe_body = ""

        for recipe in self.database.recipes:
            if recipe["result"] != item_id:
                continue

            result_icon = self.small_icon(item_id, 36)

            recipe_body += f"""
    <div style="margin-bottom:12px">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:10px">
        {result_icon}
        <b style="color:#ddd">{self.localization.localize(item.name)} × {recipe['amount']}</b>
        </div>
        {self.render_recipe_station(recipe)}
    </div>
    </div>
    """

            for req in recipe["requirements"]:
                if isinstance(req, str):
                    icon2 = self.icon_path(req)
                    recipe_body += self.link_item(
                        f"{req}.html",
                        icon2,
                        self.localize(self.database.item_name(req))
                    )
                else:
                    icon2 = self.icon_path(req["item"])
                    req_amount = req.get("amount", req.get("count", 0))
                    recipe_body += self.link_item(
                        f"{req['item']}.html",
                        icon2,
                        f"{self.localize(self.database.item_name(req['item']))} × {req_amount}"
                    )

        if recipe_body:
            return self._section("Recipe", recipe_body)
        else:
            return self._section("Recipe", "<div style='color:#777'>No recipe</div>")

    def item_durability_at_quality(self, item, quality):
        return item.maxDurability + item.durabilityPerLevel * (quality - 1)

    def item_damage_at_quality(self, item, quality):
        damages = item.damages
        damages_per_level = item.damagesPerLevel
        return {
            damage_type: damages.get(damage_type, 0) + damages_per_level.get(damage_type, 0) * (quality - 1)
            for damage_type in DAMAGE_TYPES
        }

    def non_zero_damage_types(self, item):
        types = []
        max_quality = int(item.maxQuality or 1)
        for damage_type in DAMAGE_TYPES:
            for quality in range(1, max_quality + 1):
                if self.item_damage_at_quality(item, quality).get(damage_type, 0):
                    types.append(damage_type)
                    break
        return types
    
    def recipe_requirement_amount(self, req, quality):
        if isinstance(req, str):
            return 1
        if quality <= 1:
            return req.get("amount", req.get("count", 0))
        return req.get("amountPerLevel", 0)

    def recipe_station_level(self, recipe, quality):
        if not recipe:
            return ""
        min_station_level = recipe.get("minStationLevel")
        if min_station_level is None:
            return ""
        return min_station_level + quality - 1

    def render_damage_table(self, item):
        damage_types = self.non_zero_damage_types(item)
        if not damage_types:
            return ""

        base_damage = self.item_damage_at_quality(item, 1)
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

    def render_upgrade_table(self, item):
        max_quality = int(item.maxQuality or 1)
        if max_quality <= 1:
            return ""

        item_type = item.type
        recipe = self.database.item_recipe(item.id)
        if item_type in WEAPON_TYPES:
            damage_types = self.non_zero_damage_types(item)
            if not damage_types:
                return ""

            header = "".join(f"<th>{damage_type}</th>" for damage_type in damage_types)
            rows = ""
            for quality in range(1, max_quality + 1):
                damages = self.item_damage_at_quality(item, quality)
                total = sum(damages[damage_type] for damage_type in damage_types)
                cells = "".join(f"<td>{fmt_number(damages[damage_type])}</td>" for damage_type in damage_types)
                rows += (
                    f"<tr><th>{quality}</th>"
                    f"<td>{fmt_number(self.item_durability_at_quality(item, quality))}</td>"
                    f"<td>{fmt_number(self.recipe_station_level(recipe, quality))}</td>"
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
            armor = item.armor
            armor_per_level = item.armorPerLevel
            rows = ""
            for quality in range(1, max_quality + 1):
                rows += (
                    f"<tr><th>{quality}</th>"
                    f"<td>{fmt_number(self.item_durability_at_quality(item, quality))}</td>"
                    f"<td>{fmt_number(self.recipe_station_level(recipe, quality))}</td>"
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

    def render_recipe_upgrade_table(self, item):
        recipe = self.database.item_recipe(item.id)
        if not recipe:
            return ""

        requirements = recipe.get("requirements", [])
        if not requirements:
            return ""

        max_quality = int(item.maxQuality or 1)
        header = "".join(
            f"<th>{self.item_name(req) if isinstance(req, str) else self.item_name(req.get('item', ''))}</th>"
            for req in requirements
        )
        rows = ""
        for quality in range(1, max_quality + 1):
            cells = "".join(
                f"<td>{fmt_number(self.recipe_requirement_amount(req, quality))}</td>"
                for req in requirements
            )
            rows += (
                f"<tr><th>{quality}</th>"
                f"<td>{fmt_number(self.recipe_station_level(recipe, quality))}</td>"
                f"{cells}</tr>"
            )

        station = recipe.get("craftingStation", "")
        station_row = ""
        if station:
            station_row = f"""
    <table class="info-table">
    <tr><th>Crafting Station</th><td>{self.localize(station)}</td></tr>
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

    def render_equipment_details(self, item):
        item_type = item.type
        if item_type not in WEAPON_TYPES and item_type not in ARMOR_TYPES and item_type not in AMMO_TYPES:
            return ""
        
        weapon_type = None
        if item_type in WEAPON_TYPES:
            weapon_type = item.skillType
        elif item_type in AMMO_TYPES:
            weapon_type = self.localize(item.ammoType)
        if weapon_type:
            label = "Ammo Type" if item_type in AMMO_TYPES else "Weapon Type"
            weapon_type = f"""<tr><th>{label}</th><td>{weapon_type}</td></tr>"""
        
        recipe = self.database.item_recipe(item.id)
        if recipe and 'craftingStation' in recipe:
            crafting_station = self.localize(recipe.get('craftingStation', 'None'))
        else:
            crafting_station = 'None'
        
        if item.maxDurability:
            durability = f"""
    <tr><th>Durability</th><td>{fmt_number(item.maxDurability)}</td></tr>
    <tr><th>Durability Per Level</th><td>{fmt_number(item.durabilityPerLevel)}</td></tr>
    """
        else:
            durability = ""
        
        details = f"""
    <table class="info-table">
    <tr><th>Internal ID</th><td>{item.id}</td></tr>
    <tr><th>Type</th><td>{item_type}</td></tr>
    {weapon_type}
    <tr><th>Source</th><td>{crafting_station}</td></tr>
    {durability}
    </table>
    """

        if item_type in WEAPON_TYPES or item_type in AMMO_TYPES:
            details += self.render_damage_table(item)
        elif item_type in ARMOR_TYPES:
            details += f"""
    <table class="info-table">
    <tr><th>Armor</th><td>{fmt_number(item.armor)}</td></tr>
    <tr><th>Armor Per Level</th><td>{fmt_number(item.armorPerLevel)}</td></tr>
    </table>
    """

        details += self.render_upgrade_table(item)
        details += self.render_recipe_upgrade_table(item)
        return self._section("Details", details)

    def render_crafted_into(self, item):
        crafted_body = ""

        wrote = set()
        for crafted_into in self.database.crafted_from(item.id):
            if crafted_into.id in wrote:
                continue

            wrote.add(crafted_into.id)
            icon2 = self.icon_path(crafted_into.id)
            crafted_body += self.link_item(
                f"{crafted_into.id}.html",
                icon2,
                self.localize(crafted_into.name)
            )
        return self._section("Crafted into", crafted_body or "<div style='color:#777'>None</div>")

    def render_dropped_by(self, item):
        drops_body = ""

        for mob in self.database.dropped_by(item.id):
            drops_body += f"""
    <a href="../mobs/{mob['id']}.html" style="
    display:block;
    padding:6px 8px;
    border-radius:6px;
    color:#eee;
    text-decoration:none;
    " onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
    {self.localize(mob['name'])}
    </a>
    """
        return self._section("Dropped by", drops_body or "<div style='color:#777'>None</div>")

    def render_sold_by(self, item):
        sold_by_body = ""

        coin_icon = self.icon_path('Coins')
        coin_img = f'<img src="{coin_icon}" style="height:2.2em;vertical-align:middle;margin-right:8px;border-radius:4px;">' if coin_icon else ""

        # <b style="color:#ddd">{self.localization.localize(item.name)} × {recipe['amount']}</b>
        for trader_id, trader in self.database.get_traders().items():
            name = self.localize(trader['name']) if trader['name'] else trader_id
            for trader_item in trader['items']:
                if trader_item['id'] == item.id:
                    sold_by_body += f"""
    <a href="../traders/{trader_id}.html" style="
    display:block;
    padding:6px 8px;
    border-radius:6px;
    color:#eee;
    text-decoration:none;
    " onmouseover="this.style.background='#2a2a2a'" onmouseout="this.style.background='transparent'">
    {name} {coin_img}×{trader_item['price']}
    </a>
    """
        return self._section("Sold by", sold_by_body or "<div style='color:#777'>None</div>")

    def generate_item_detail(self, item, outdir):
        item_id = item.id
        name = self.localization.localize(item.name)

        html = self.side_bar("../")
        html += r"""<div class="content">"""

        html += self.breadcrumb([
            '<a href="../index.html" style="color:#888">Home</a>',
            '<a href="index.html" style="color:#888">Items</a>',
            f'<a href="index.html#{item.type}" style="color:#888">{item.type}</a>',
            item_id
        ])

        icon = f'../../icons/{item_id}.png'
        title_icon = ""
        if icon:
            title_icon = f'<img src="{icon}" style="width:48px;height:48px;object-fit:contain;border-radius:6px">'

        html += f"""
    <h1 style="margin-bottom:8px">{name}</h1>

    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
    {title_icon}
    <div style="color:#aaa;font-size:14px;line-height:1.5">
        <div><b style="color:#ddd">ID:</b> {item_id}</div>
        <div><b style="color:#ddd">Type:</b> {item.type}</div>
    </div>
    </div>
    """

        html += self.render_item_description(item)
        html += self.render_status_effect(item)
        html += self.render_food_details(item)
        html += self.render_recipes(item)
        html += self.render_equipment_details(item)
        html += self.render_crafted_into(item)
        html += self.render_dropped_by(item)
        html += self.render_sold_by(item)

        # end of content
        html += r"""</div>"""

        with open(f"{outdir}/items/{item_id}.html", "w", encoding="utf-8") as f:
            f.write(self.page_template(name, html))

    def generate_mob_detail(self, mob, outdir):
        html = self.side_bar('../')
        html += r"""<div class="content">"""

        html += self.breadcrumb([
            '<a href="../index.html" style="color:#888">Home</a>',
            '<a href="index.html" style="color:#888">Mobs</a>',
            mob['id']
        ])

        html += f"<h1>{self.localize(mob['name'])}</h1>"

        # ========================
        # 基本情報
        # ========================
        html += "<h2>基本情報</h2>"
        html += '<table class="info-table">'

        biomes = self.database.get_mob_biomes(mob['id'])
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
        drops = self.database.get_drops(mob['id'])
        if drops:
            html += "<h2>ドロップ</h2>"
            html += '<table class="drop-table">'
            html += "<tr><th>アイテム</th><th>数量</th><th>確率</th></tr>"

            for d in drops:
                item = d["item"]
                icon = self.icon_path(item)

                img = f'<img src="{icon}" class="item-icon">' if icon else ""
                name = f'<a href="../items/{item}.html">{self.item_name(item)}</a>'

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

        with open(f"{outdir}/mobs/{mob['id']}.html", "w", encoding="utf-8") as f:
            f.write(self.page_template(mob["id"], html))

    def generate_items(self, outdir):

        os.makedirs(outdir + '/items', exist_ok=True)

        html = self.side_bar('../')
        html += r"""<div class="content">"""
        html += self.breadcrumb([
            '<a href="../index.html" style="color:#888">Home</a>',
            '<a href="index.html" style="color:#888">Items</a>'
        ])

        html += "<h1>Items</h1>"

        grouped = defaultdict(list)
        for item_id, item in self.database._items.items():
            # img = f'<img src="../../icons/{item_id}.png" width="64"><br>'
            if not item.icon or not os.path.exists(f'icons/{item_id}.png'):
                continue

            grouped[item_category(item)].append((item_id, item))

        def category_sort_key(category):
            if category in ITEM_CATEGORY_ORDER:
                return (ITEM_CATEGORY_ORDER.index(category), category)
            return (len(ITEM_CATEGORY_ORDER), category)
        for category in sorted(grouped.keys(), key=category_sort_key):
            html += f"""
                <h2 id="{category}" style="width:100%;margin-top:24px;border-bottom:1px solid #444;padding-bottom:4px">
                {category}
                </h2>
            """

            def items_sort_key(pair):
                item = pair[1]
                if item.type in ("Ammo", "AmmoNonEquipable", "Bow", "OneHandedWeapon", "TwoHandedWeapon"):
                    return (item.type, get_total_damage(item))

                # armors
                if item.type in ("Helmet", "Chest", "Legs", "Shoulder"):
                    return (item.type, item.armor)
                
                # shields
                if item.type in ("Shield"):
                    return (item.type, item.blockPower)

                if item.type == 'Consumable':
                    if item.foodEitr:
                        return (item.foodEitr, item.food, item.foodStamina)
                    if item.food > item.foodStamina:
                        return (item.food, item.foodStamina, item.foodEitr)
                    return (item.foodStamina, item.food, item.foodEitr)

                if item.type == 'Trophy':
                    for mob in self.database.dropped_by(item.id):
                        return (item.type, mob['hp'])
                    return (item.type, 99999999.0)

                # TODO: sort by biome
                return (item.type, item.id)

            category_items = grouped[category]
            if category == 'Ammo':
                sub_category_items = defaultdict(list)
                for item_id, item in category_items:
                    sub_category_items[ammo_group(item)].append((item_id, item))
                sub_category_items_sorted = sorted(sub_category_items.keys(), key=skill_type_sort_key)

            elif category == 'Weapon':
                sub_category_items = defaultdict(list)
                for item_id, item in category_items:
                    sub_category_items[weapon_group(item)].append((item_id, item))
                sub_category_items_sorted = sorted(sub_category_items.keys(), key=skill_type_sort_key)

            elif category == 'Material':
                sub_category_items = defaultdict(list)
                for item_id, item in category_items:
                    sub_category_items[material_group(self.database, item)].append((item_id, item))
                sub_category_items_sorted = sorted(sub_category_items.keys(), key=material_group_sort_key)

                # sort food

            elif category == 'Consumable':
                sub_category_items = defaultdict(list)
                for item_id, item in category_items:
                    sub_category_items[consumable_group(item)].append((item_id, item))
                sub_category_items_sorted = sorted(sub_category_items.keys(), key=consumable_group_sort_key)

                # TODO: sort by food status
                #sorted(consumables_by_group[consumable_type], key=food_sort_key)

            elif category == 'Trophy':
                sub_category_items = defaultdict(list)
                for item_id, item in category_items:
                    sub_category_items[trophy_group(item, self.database)].append((item_id, item))
                sub_category_items_sorted = sorted(sub_category_items.keys(), key=trophy_sort_key)
            else:
                sub_category_items = defaultdict(list)
                for item_id, item in category_items:
                    sub_category_items[item.type].append((item_id, item))
                sub_category_items_sorted = sorted(sub_category_items.keys())

            for sub_category in sub_category_items_sorted:
                sub_category_text = self.localization.localize(sub_category)
                if len(sub_category_items_sorted) > 1:
                    html += f"""
<h3 id="{sub_category_text}" style="width:100%;margin:18px 0 6px;color:#aaa;font-size:15px">
{sub_category_text}
</h3>
                    """

                html += """<div style="display:flex;flex-wrap:wrap">"""
                for item_id, item in sorted(sub_category_items.get(sub_category), key=items_sort_key):
                    html += self.item_card(item_id, item)
                    self.generate_item_detail(item, outdir)
                html += "</div>"

        # end of content
        html += r"""</div>"""

        os.makedirs(f"{outdir}/items", exist_ok=True)
        with open(f"{outdir}/items/index.html", "w", encoding="utf-8") as f:
            f.write(self.page_template("Items", html))

    # mobs
    def spawn_time_tags(self, entry):
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

    def mob_card(self, entry):
        mob = entry["mob"]
        name = mob["name"]
        mob_id = mob["id"]

        icon = self.icon_path(mob_id)
        img = f'<img src="{icon}" class="mob-icon">' if icon else '<div class="mob-icon placeholder"></div>'

        hp = mob.get("hp", "-")
        boss = mob.get("boss", False)

        boss_tag = '<div class="boss-tag">BOSS</div>' if boss else ""
        time_tags = self.spawn_time_tags(entry)

        return f"""
                <a href="{mob_id}.html" class="mob-card">
                    {boss_tag}
                    {img}
                    <div class="mob-name">{self.localize(name)}</div>
                    <div class="mob-hp">HP: {hp}</div>
                    <div class="spawn-tags">{time_tags}</div>
                </a>
                """

    def render_mob_grid(self, entries):
        out = '<div class="mob-grid">'
        group_sorted = sorted(entries, key=lambda e: e["mob"].get("hp", 0), reverse=False)
        for entry in group_sorted:
            out += self.mob_card(entry)
        out += "</div>"
        return out

    def condition_values(self, value):
        if not value:
            return []
        if isinstance(value, list):
            return [v for v in value if v]
        return [value]

    def render_conditioned_mobs(self, entries):
        normal = []
        normal_by_id = {}
        required_env = []

        for entry in entries:
            global_keys = self.condition_values(entry.get("requiredGlobalKey"))
            environments = self.condition_values(entry.get("requiredEnvironments"))

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
            out += self.render_mob_grid(normal)

        if required_env:
            out += f"<h4>Conditional Spawn</h4>"
            out += self.render_mob_grid(required_env)

        return out

    def render_group(self, title, groups):

        out = f"<h2>{title}</h2>"

        for biome in BIOME_ORDER:
            if biome not in groups:
                continue
            out += f"<h3>{biome}</h3>"
            out += self.render_conditioned_mobs(groups[biome])

        return out

    def generate_mobs(self, outdir):

        os.makedirs(outdir + '/mobs', exist_ok=True)

        html = self.side_bar('../')
        html += r"""<div class="content mob-page">"""
        html += self.breadcrumb([
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

        for loc in self.database.spawns:
            if not loc.get("enabled"):
                continue

            mob = self.database.mobs.get(loc.get("name"))
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

        for id, mob in self.database.mobs.items():

            # detail
            self.generate_mob_detail(mob, outdir)

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

        html += self.render_group("Mobs", mob_groups)
        html += self.render_group("Bosses", boss_groups)
        html += "</div>"

        html += "</div>"

        with open(f"{outdir}/mobs/index.html", "w", encoding="utf-8") as f:
            f.write(self.page_template("Mobs", html, r"""
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


    # traders/npcs
    def generate_npc_detail(self, trader_id, trader, outdir):
        name = self.localization.localize(trader['name'])

        html = self.side_bar("../")
        html += r"""<div class="content">"""

        html += self.breadcrumb([
            '<a href="../index.html" style="color:#888">Home</a>',
            '<a href="index.html" style="color:#888">Traders</a>',
            trader_id
        ])

        icon = f'../../icons/{trader_id}.png'
        title_icon = ""
        if icon:
            title_icon = f'<img src="{icon}" style="width:48px;height:48px;object-fit:contain;border-radius:6px">'

        html += f"""
    <h1 style="margin-bottom:8px">{name}</h1>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">
    {title_icon}
    <div style="color:#aaa;font-size:14px;line-height:1.5">
        <div><b style="color:#ddd">ID:</b> {trader_id}</div>
    </div>
    </div>
    """
        
        coin_icon = self.icon_path('Coins')
        coin_img = f'<img src="{coin_icon}" style="height:2.2em;vertical-align:middle;border-radius:4px;">' if coin_icon else ""

        html += '<div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap:8px;">'
        for trader_item in trader['items']:
            item = self.database.get_item(trader_item['id'])
            if item:
                if trader_item['requiredGlobalKey']:
                    flag = f"""<div style="font-size:0.8em; opacity:0.6;">{trader_item['requiredGlobalKey']}</div>"""
                else:
                    flag = ""
                html += self.link_item(
                    f'../items/{trader_item['id']}.html',
                    self.icon_path(trader_item['id']),
                    f"""
                    <div style="display:flex; flex-direction:column; line-height:1.2;">
                        <div style="font-weight:600;">
                            {self.localize(item.name)}
                        </div>
                        <div style="font-size:0.9em; opacity:0.8;">
                            {coin_img}{trader_item['price']}
                        </div>
                        { flag }
                    </div>
                    """
                )

        # end of content
        html += r"""</div></div>"""

        with open(f"{outdir}/traders/{trader_id}.html", "w", encoding="utf-8") as f:
            f.write(self.page_template(name, html))

    def generate_npcs(self, outdir):
        os.makedirs(outdir + '/traders', exist_ok=True)

        html = self.side_bar('../')
        html += r"""<div class="content">"""
        html += self.breadcrumb([
            '<a href="../index.html" style="color:#888">Home</a>',
            'Traders'
        ])
        html += "<h1>Traders</h1>"
        for trader_id, trader in self.database.get_traders().items():
            html += f"""<a href="{trader_id}.html">{trader_id}</a><br>"""
            self.generate_npc_detail(trader_id, trader, outdir)

        html += "</div>"

        with open(f"{outdir}/traders/index.html", "w", encoding="utf-8") as f:
            f.write(self.page_template("Traders", html, r""""""))

    def generate_home(self, outdir):
        html = self.side_bar()
        html += r"""<div class="content">"""
        html += self.breadcrumb([
            'Home',
        ])
        html += "</div>"
        with open(f"{outdir}/index.html", "w", encoding="utf-8") as f:
            f.write(self.page_template("Home", html))

    def generate(self, outdir):

        os.makedirs(outdir, exist_ok=True)

        # this will also generate detail page
        self.generate_items(outdir)
        self.generate_mobs(outdir)
        self.generate_npcs(outdir)

        # home
        self.generate_home(outdir)