from dataclasses import dataclass, field
from enum import Enum

class DamageModifier(Enum):
    Normal = 0

@dataclass
class DamageModifiers:
    pass

@dataclass
class ItemDrop:
    id: str = ''
    type: str = ''
    name: str = ''
    description: str = ''
    icon: str = ''
    maxStackSize: int = 1
    maxQuality: int = 1
    weight: float = 1.0
    teleportable: bool = True
    buildPieces: list = None

    eitrRegenModifier: float = 0.0
    movementModifier: float = 0.0
    homeItemsStaminaModifier: float = 0.0
    heatResistanceModifier: float = 0.0
    jumpStaminaModifier: float = 0.0
    attackStaminaModifier: float = 0.0
    blockStaminaModifier: float = 0.0
    dodgeStaminaModifier: float = 0.0
    swimStaminaModifier: float = 0.0
    sneakStaminaModifier: float = 0.0
    runStaminaModifier: float = 0.0

    # food
    food: float = 0.0
    foodStamina: float = 0.0
    foodEitr: float = 0.0
    isDrink: bool = False
    foodBurnTime: float = 0.0
    foodRegen: float = 0.0
    foodEatAnimTime: float = 0.0

    armor: float = 10.0
    armorPerLevel: float = 1.0
    blockPower: float = 10.0
    blockPowerPerLevel: float = None
    deflectionForce: float = None
    deflectionForcePerLevel: float = 0.0
    timedBlockBonus: float = 1.5
    perfectBlockStaminaRegen: float = None

    maxAdrenaline: float = None
    blockAdrenaline: float = None
    perfectBlockAdrenaline: float = None
    fullAdrenalineSE: dict[str, float] = field(default_factory=dict)

    skillType: str = '' # default Swords btw
    toolTier: int = None
    damages: dict[str, float] = field(default_factory=dict)
    damagesPerLevel: dict[str, float] = field(default_factory=dict)
    ammoType: str = ''
    maxDurability: float = 0.0 # ...
    durabilityPerLevel: float = 0.0 # ...

    consumeStatusEffect: dict = field(default_factory=dict)
