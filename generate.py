import json
import os
from collections import defaultdict

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
            return loc['biome']
    return None

def icon_path(item_id):
    path = f"../../{ICON_DIR}/{item_id}.png"
    if os.path.exists(f"{ICON_DIR}/{item_id}.png"):
        return path
    return None

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
for mob in drops:
    for d in mob["drops"]:
        dropped_by.setdefault(d["item"], []).append(mob["name"])

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

    html += f"""
<h1 style="margin-bottom:8px">{name}</h1>
"""

    icon = icon_path(item_id)
    if icon:
        html += f'<img src="{icon}" width="72" style="border-radius:8px;margin-bottom:10px"><br>'

    # ===== Recipe =====
    recipe_body = ""

    for recipe in recipes:
        if recipe["result"] != item_id:
            continue

        recipe_body += f"""
<div style="margin-bottom:10px;color:#aaa">
  <b style="color:#ddd">{item_name(item_id)} × {recipe['amount']}</b>
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
                recipe_body += link_item(
                    f"{req['item']}.html",
                    icon2,
                    f"{item_name(req['item'])} × {req['count']}"
                )

    if recipe_body:
        html += section("Recipe", recipe_body)
    else:
        html += section("Recipe", "<div style='color:#777'>No recipe</div>")

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
for drop in drops:

    mob = mobs.get(drop['name'], None)
    if not mob:
        continue

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
    if "drops" in drop:
        html += "<h2>ドロップ</h2><ul>"
        html += '<table class="drop-table">'
        html += "<tr><th>アイテム</th><th>数量</th><th>確率</th></tr>"

        for d in drop['drops']:
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

    current_type = None

    for item_id, item in items.items():
        icon = icon_path(item_id)
        if not icon:
            continue

        _type = item["type"]

        # type変わったらセクション作る
        if _type != current_type:
            if current_type is not None:
                html += "</div>"  # close previous flex container

            html += f"""
    <h2 id="{_type}" style="width:100%;margin-top:24px;border-bottom:1px solid #444;padding-bottom:4px">
    {_type}
    </h2>
    <div style="display:flex;flex-wrap:wrap">
    """
            current_type = _type

        img = f'<img src="../../{ICON_DIR}/{item_id}.png" width="64"><br>' if icon else ""

        html += f"""
    <div style="width:110px;text-align:center;margin:6px">
    <a href="{item_id}.html" style="color:white;text-decoration:none">
        {img}
        <div style="font-size:12px">{item["name"]}</div>
    </a>
    </div>
    """

    # close last block
    if current_type is not None:
        html += "</div>"

    # end of content
    html += r"""</div>"""

    with open(f"{SITE_DIR}/items/index.html", "w", encoding="utf-8") as f:
        f.write(page_template("Items", html))

# ===== index =====
# ========================
# 描画関数
# ========================
def render_group(title, groups):

    out = f"<h2>{title}</h2>"

    BIOME_ORDER = [
        "Meadows", "BlackForest", "Swamp",
        "Mountain", "Plains", "Mistlands",
        "AshLands", "DeepNorth", "Ocean", "Unknown"
    ]

    for biome in BIOME_ORDER:
        if biome not in groups:
            continue
        out += f"<h3>{biome}</h3>"
        out += '<div class="mob-grid">'

        group_sorted = sorted(groups[biome], key=lambda m: m.get("hp", 0), reverse=False)
        for mob in group_sorted:
            name = mob["name"]
            mob_id = mob["id"]

            icon = icon_path(mob_id)
            #img = f'<img src="{icon}" class="mob-icon">' if icon else ""
            img = f'<img src="{icon}" class="mob-icon">' if icon else '<div class="mob-icon placeholder"></div>'

            hp = mob.get("hp", "-")
            boss = mob.get("boss", False)

            boss_tag = '<div class="boss-tag">BOSS</div>' if boss else ""

            out += f"""
            <a href="{mob_id}.html" class="mob-card">
                {boss_tag}
                {img}
                <div class="mob-name">{mob_name(name)}</div>
                <div class="mob-hp">HP: {hp}</div>
            </a>
            """

        out += "</div>"

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

    for id, mob in mobs.items():
        biomes = mob_biomes(mob["id"]) or ["Unknown"]

        for b in biomes:
            if mob.get("boss"):
                boss_groups[b].append(mob)
            else:
                mob_groups[b].append(mob)

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