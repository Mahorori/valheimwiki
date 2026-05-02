from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class RecipeRequirement:
    """アップグレードや作成に必要な材料1種分"""
    item_id: str
    amount: int
    amount_per_level: int

@dataclass
class ValheimItem:
    """アイテムの基本情報"""
    id: str                 # internal name (例: SwordIron)
    name: str               # 表示名
    description: str
    item_type: str          # Material, Consumable, Weaponなど
    weight: float
    max_stack: int
    teleportable: bool
    
    # 食べ物の場合のみデータが入る
    food_hp: float = 0
    food_stamina: float = 0
    
    # レシピ情報
    requirements: List[RecipeRequirement] = field(default_factory=list)